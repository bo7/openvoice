#!/usr/bin/env python3
"""
XTTS Voice Cloning Server - Mac Studio
Mit automatischem Text-Chunking fuer lange Texte
"""

import os
os.environ["OMP_NUM_THREADS"] = "16"
os.environ["MKL_NUM_THREADS"] = "16"

import io
import re
import tempfile
import logging
from pathlib import Path

import torch
import numpy as np

DEVICE = torch.device("cpu")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import soundfile as sf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="XTTS Voice Cloning Server", version="2.2.0")

xtts_model = None
gpt_cond_latent_cache = {}
speaker_embedding_cache = {}
VOICES_DIR = Path.home() / "xtts-server" / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHARS = 200  # Sicher unter 250 Limit


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    language: str = "de"


def get_model_path():
    base = Path.home() / "Library/Application Support/tts/tts_models--multilingual--multi-dataset--xtts_v2"
    return base if base.exists() else None


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Teilt Text in Chunks, respektiert Satzgrenzen"""
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
            # Lange Saetze bei Kommas teilen
            parts = re.split(r'(?<=[,;:])\s+', sent)
            for part in parts:
                if len(part) > max_chars:
                    words = part.split()
                    temp = ""
                    for w in words:
                        if len(temp) + len(w) + 1 <= max_chars:
                            temp = f"{temp} {w}".strip()
                        else:
                            if temp:
                                chunks.append(temp)
                            temp = w
                    if temp:
                        chunks.append(temp)
                elif len(current) + len(part) + 1 <= max_chars:
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
    global xtts_model
    
    logger.info("Loading XTTS v2 on CPU")
    
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        
        model_path = get_model_path()
        if not model_path:
            from TTS.api import TTS
            xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            return
        
        config = XttsConfig()
        config.load_json(str(model_path / "config.json"))
        
        xtts_model = Xtts.init_from_config(config)
        xtts_model.load_checkpoint(config, checkpoint_dir=str(model_path), eval=True)
        logger.info("XTTS v2 loaded")
            
    except Exception as e:
        logger.error(f"Load error: {e}")
        from TTS.api import TTS
        xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")


def get_voice_conditioning(voice_path: str):
    """Cache voice conditioning fuer schnellere Generierung"""
    if voice_path in gpt_cond_latent_cache:
        return gpt_cond_latent_cache[voice_path], speaker_embedding_cache[voice_path]
    
    gpt_cond, spk_emb = xtts_model.get_conditioning_latents(audio_path=[voice_path])
    gpt_cond_latent_cache[voice_path] = gpt_cond
    speaker_embedding_cache[voice_path] = spk_emb
    return gpt_cond, spk_emb


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "xtts_v2",
        "device": "cpu",
        "max_chars_per_chunk": MAX_CHARS,
        "voices": [f.stem for f in VOICES_DIR.glob("*.wav")]
    }


@app.get("/voices")
async def get_voices():
    return {
        "voices": [f.stem for f in VOICES_DIR.glob("*.wav")],
        "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu"]
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
        sf.write(str(voice_path), y, sr)
        
        # Cache invalidieren
        str_path = str(voice_path)
        gpt_cond_latent_cache.pop(str_path, None)
        speaker_embedding_cache.pop(str_path, None)
        
        return {"status": "success", "voice": name}
    finally:
        os.unlink(tmp_path)


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    if xtts_model is None:
        raise HTTPException(503, "Model not loaded")
    
    voice_path = VOICES_DIR / f"{request.voice}.wav"
    if not voice_path.exists():
        raise HTTPException(400, f"Stimme '{request.voice}' nicht gefunden")
    
    try:
        text = request.text.strip().replace("\n", " ").replace("\r", "")
        chunks = split_text(text)
        
        logger.info(f"TTS: {len(text)} chars -> {len(chunks)} chunks")
        
        gpt_cond, spk_emb = get_voice_conditioning(str(voice_path))
        
        all_audio = []
        for i, chunk in enumerate(chunks):
            logger.info(f"  Chunk {i+1}/{len(chunks)}: {len(chunk)} chars")
            
            out = xtts_model.inference(
                text=chunk,
                language=request.language,
                gpt_cond_latent=gpt_cond,
                speaker_embedding=spk_emb,
            )
            all_audio.append(out["wav"])
        
        # Chunks zusammenfuegen mit kleiner Pause
        if len(all_audio) > 1:
            pause = np.zeros(int(24000 * 0.15))  # 150ms Pause
            combined = []
            for i, audio in enumerate(all_audio):
                combined.append(audio)
                if i < len(all_audio) - 1:
                    combined.append(pause)
            final_audio = np.concatenate(combined)
        else:
            final_audio = all_audio[0]
        
        buffer = io.BytesIO()
        sf.write(buffer, final_audio, 24000, format='WAV')
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
    
    # Cache loeschen
    gpt_cond_latent_cache.pop(str(voice_path), None)
    speaker_embedding_cache.pop(str(voice_path), None)
    
    voice_path.unlink()
    return {"status": "deleted", "voice": name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)
