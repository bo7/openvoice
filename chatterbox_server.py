#!/usr/bin/env python3
"""
Chatterbox TTS Server - Optimiert fuer Mac Studio
Voice Cloning mit Apple Silicon Unterstuetzung
"""

import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import io
import re
import tempfile
import logging
from pathlib import Path

import torch
import torchaudio as ta
import numpy as np

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device - MPS fuer Apple Silicon GPU
if torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"

app = FastAPI(title="Chatterbox TTS Server", version="1.0.0")

model = None
VOICES_DIR = Path.home() / "chatterbox-server" / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHARS = 250


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    language: str = "de"
    exaggeration: float = 0.5
    cfg_weight: float = 0.5
    temperature: float = 0.8


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Teilt Text in Chunks"""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current = ""
    
    for sent in sentences:
        if len(sent) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            parts = re.split(r'(?<=[,;:])\s+', sent)
            for part in parts:
                if len(current) + len(part) + 1 <= max_chars:
                    current = f"{current} {part}".strip()
                else:
                    if current:
                        chunks.append(current.strip())
                    current = part
        elif len(current) + len(sent) + 1 <= max_chars:
            current = f"{current} {sent}".strip()
        else:
            if current:
                chunks.append(current.strip())
            current = sent
    
    if current:
        chunks.append(current.strip())
    
    return [c for c in chunks if c]


@app.on_event("startup")
async def load_model():
    global model
    
    logger.info(f"Loading Chatterbox on {DEVICE}...")
    logger.info(f"PyTorch: {torch.__version__}")
    logger.info(f"MPS available: {torch.backends.mps.is_available()}")
    
    try:
        from chatterbox.tts import ChatterboxTTS
        model = ChatterboxTTS.from_pretrained(device=DEVICE)
        logger.info("Chatterbox loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Chatterbox: {e}")
        raise


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "chatterbox",
        "device": DEVICE,
        "mps_available": torch.backends.mps.is_available(),
        "loaded": model is not None,
        "voices": [f.stem for f in VOICES_DIR.glob("*.wav")],
        "sample_rate": model.sr if model else None
    }


@app.get("/voices")
async def get_voices():
    return {
        "voices": [f.stem for f in VOICES_DIR.glob("*.wav")],
        "languages": ["de", "en", "es", "fr", "it", "ja", "ko", "nl", "pl", "pt", "ru", "tr", "zh",
                      "ar", "da", "el", "fi", "he", "hi", "ms", "no", "sv", "sw"]
    }


@app.post("/clone")
async def clone_voice(audio: UploadFile = File(...), name: str = Form(...)):
    if not name.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(400, "Ungueltiger Name")
    
    voice_path = VOICES_DIR / f"{name}.wav"
    suffix = Path(audio.filename).suffix.lower() if audio.filename else ".wav"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name
    
    try:
        import librosa
        y, sr = librosa.load(tmp_path, sr=22050)
        import soundfile as sf
        sf.write(str(voice_path), y, sr)
        
        return {"status": "success", "voice": name}
    finally:
        os.unlink(tmp_path)


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    if model is None:
        raise HTTPException(503, "Model not loaded")
    
    voice_path = VOICES_DIR / f"{request.voice}.wav"
    if not voice_path.exists():
        # Ohne Voice Cloning - Default Stimme
        voice_path = None
    
    try:
        text = request.text.strip().replace("\n", " ").replace("\r", "")
        chunks = split_text(text)
        
        logger.info(f"TTS: {len(text)} chars -> {len(chunks)} chunks")
        
        all_audio = []
        for i, chunk in enumerate(chunks):
            logger.info(f"  Chunk {i+1}/{len(chunks)}: {len(chunk)} chars")
            
            if voice_path:
                wav = model.generate(
                    chunk,
                    audio_prompt_path=str(voice_path),
                    exaggeration=request.exaggeration,
                    cfg_weight=request.cfg_weight,
                    temperature=request.temperature
                )
            else:
                wav = model.generate(
                    chunk,
                    exaggeration=request.exaggeration,
                    cfg_weight=request.cfg_weight,
                    temperature=request.temperature
                )
            
            all_audio.append(wav.squeeze().numpy())
        
        # Zusammenfuegen
        if len(all_audio) > 1:
            pause = np.zeros(int(model.sr * 0.2))  # 200ms Pause
            combined = []
            for i, audio in enumerate(all_audio):
                combined.append(audio)
                if i < len(all_audio) - 1:
                    combined.append(pause)
            final_audio = np.concatenate(combined)
        else:
            final_audio = all_audio[0]
        
        # Als WAV speichern
        buffer = io.BytesIO()
        import soundfile as sf
        sf.write(buffer, final_audio, model.sr, format='WAV')
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="audio/wav")
    
    except Exception as e:
        logger.error(f"TTS error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.delete("/voices/{name}")
async def delete_voice(name: str):
    voice_path = VOICES_DIR / f"{name}.wav"
    if not voice_path.exists():
        raise HTTPException(404, f"Stimme '{name}' nicht gefunden")
    
    voice_path.unlink()
    return {"status": "deleted", "voice": name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8767)
