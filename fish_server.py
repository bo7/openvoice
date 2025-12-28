#!/usr/bin/env python3
"""
Fish Speech TTS Server
API Server fuer Fish Speech / OpenAudio auf Apple Silicon
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel
import soundfile as sf
import numpy as np
import io
import os
from pathlib import Path
from typing import Optional
import torch

app = FastAPI(title="Fish Speech TTS Server")

# Globale Variablen
model = None
VOICES_DIR = Path.home() / "voices" / "fish"
VOICES_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = Path.home() / "fish-speech-repo" / "checkpoints" / "fish-speech-1.5"


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    language: str = "de"
    temperature: float = 0.7
    top_p: float = 0.8


def load_fish_model():
    """Lade Fish Speech Modell"""
    global model
    if model is not None:
        return model
    
    import sys
    sys.path.insert(0, str(Path.home() / "fish-speech-repo"))
    
    from tools.llama.generate import load_model
    from tools.vqgan.inference import load_model as load_vqgan
    
    # Lade Modelle
    llama_model = load_model(
        checkpoint_path=str(CHECKPOINT_PATH),
        device="mps",
        precision=torch.float16
    )
    
    vqgan_path = CHECKPOINT_PATH / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    vqgan_model = load_vqgan(str(vqgan_path), device="mps")
    
    model = {
        "llama": llama_model,
        "vqgan": vqgan_model,
        "device": "mps"
    }
    
    return model


@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Generiere Audio aus Text mit Fish Speech"""
    try:
        import sys
        sys.path.insert(0, str(Path.home() / "fish-speech-repo"))
        
        from tools.llama.generate import generate_long
        from tools.vqgan.inference import decode
        
        m = load_fish_model()
        
        # Check for reference voice
        voice_path = VOICES_DIR / f"{req.voice}.wav"
        prompt_audio = None
        if voice_path.exists():
            prompt_audio = str(voice_path)
        
        # Generate codes
        codes = generate_long(
            model=m["llama"],
            text=req.text,
            prompt_audio=prompt_audio,
            temperature=req.temperature,
            top_p=req.top_p,
            device=m["device"]
        )
        
        # Decode to audio
        audio = decode(m["vqgan"], codes, device=m["device"])
        
        # Convert to numpy
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        
        # Ensure correct shape
        if len(audio.shape) > 1:
            audio = audio.squeeze()
        
        # Convert to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio, 21000, format='WAV')  # Fish Speech uses 21kHz
        buffer.seek(0)
        
        return Response(content=buffer.read(), media_type="audio/wav")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/clone")
async def clone_voice(
    name: str = Form(...),
    audio: UploadFile = File(...)
):
    """Speichere Reference Audio fuer Voice Cloning"""
    try:
        content = await audio.read()
        audio_buffer = io.BytesIO(content)
        data, sr = sf.read(audio_buffer)
        
        # Resample zu 21kHz wenn noetig (Fish Speech rate)
        if sr != 21000:
            import resampy
            data = resampy.resample(data, sr, 21000)
        
        # Mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        
        # Speichere
        voice_path = VOICES_DIR / f"{name}.wav"
        sf.write(voice_path, data, 21000)
        
        return {"status": "ok", "voice": name}
        
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/voices")
async def list_voices():
    """Liste verfuegbare Stimmen"""
    voices = ["default"]
    
    # Custom voices
    for f in VOICES_DIR.glob("*.wav"):
        voice_name = f.stem
        if voice_name not in voices:
            voices.append(voice_name)
    
    return {
        "voices": voices,
        "languages": ["de", "en", "zh", "ja"]
    }


@app.get("/health")
async def health():
    """Health Check"""
    model_loaded = model is not None
    return {
        "status": "ok",
        "engine": "fish-speech-1.5",
        "device": "Apple Silicon (MPS)",
        "model_loaded": model_loaded,
        "checkpoint": str(CHECKPOINT_PATH)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8769)
