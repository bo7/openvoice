#!/usr/bin/env python3
"""
MLX-Audio TTS Server
API Server fuer Kokoro und Marvis TTS auf Apple Silicon
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import soundfile as sf
import numpy as np
import io
import os
from pathlib import Path
from typing import Optional

app = FastAPI(title="MLX-Audio TTS Server")

# Globale Variablen
models = {}
VOICES_DIR = Path.home() / "voices" / "mlx"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Verfuegbare Modelle
AVAILABLE_MODELS = {
    "kokoro": "prince-canuma/Kokoro-82M",
    "marvis": "Marvis-AI/marvis-tts-250m-v0.1",
}

# Kokoro Voices (built-in)
KOKORO_VOICES = [
    "af_heart", "af_nova", "af_bella", "af_sky", "af_sarah",
    "am_michael", "am_adam", "am_brian",
    "bf_emma", "bf_isabella",
    "bm_george", "bm_lewis",
]


class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    model: str = "kokoro"
    speed: float = 1.0
    language: str = "a"  # a=American English, b=British English
    temperature: float = 0.7
    top_p: float = 0.9


class CloneRequest(BaseModel):
    name: str


def load_model(model_name: str):
    """Lade ein Modell (lazy loading)"""
    if model_name in models:
        return models[model_name]
    
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(400, f"Unbekanntes Modell: {model_name}")
    
    model_id = AVAILABLE_MODELS[model_name]
    
    if model_name == "kokoro":
        from mlx_audio.tts.models.kokoro import KokoroPipeline
        from mlx_audio.tts.utils import load_model as mlx_load
        
        model = mlx_load(model_id)
        models[model_name] = {"model": model, "model_id": model_id, "type": "kokoro"}
        
    elif model_name == "marvis":
        from mlx_audio.tts.utils import load_model as mlx_load
        
        model = mlx_load(model_id)
        models[model_name] = {"model": model, "model_id": model_id, "type": "marvis"}
    
    return models[model_name]


@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Generiere Audio aus Text"""
    try:
        model_data = load_model(req.model)
        
        if model_data["type"] == "kokoro":
            from mlx_audio.tts.models.kokoro import KokoroPipeline
            
            pipeline = KokoroPipeline(
                lang_code=req.language,
                model=model_data["model"],
                repo_id=model_data["model_id"]
            )
            
            # Check for custom voice (ref audio)
            custom_voice_path = VOICES_DIR / f"{req.voice}.wav"
            ref_audio = str(custom_voice_path) if custom_voice_path.exists() else None
            
            audio_chunks = []
            for _, _, audio in pipeline(
                req.text,
                voice=req.voice if not ref_audio else None,
                speed=req.speed,
                split_pattern=r'\n+'
            ):
                audio_chunks.append(audio)
            
            if not audio_chunks:
                raise HTTPException(500, "Keine Audio-Daten generiert")
            
            # Combine chunks
            full_audio = np.concatenate([chunk[0] if len(chunk.shape) > 1 else chunk for chunk in audio_chunks])
            
        elif model_data["type"] == "marvis":
            from mlx_audio.tts.generate import generate_audio
            
            # Marvis mit Reference Audio
            custom_voice_path = VOICES_DIR / f"{req.voice}.wav"
            
            # Generate to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            generate_audio(
                text=req.text,
                model_path=model_data["model_id"],
                ref_audio=str(custom_voice_path) if custom_voice_path.exists() else None,
                temperature=req.temperature,
                top_p=req.top_p,
                file_prefix=tmp_path.replace(".wav", ""),
                verbose=False
            )
            
            # Read generated audio
            full_audio, sr = sf.read(tmp_path)
            os.unlink(tmp_path)
        
        # Convert to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, full_audio, 24000, format='WAV')
        buffer.seek(0)
        
        return Response(content=buffer.read(), media_type="audio/wav")
        
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/clone")
async def clone_voice(name: str, audio: bytes):
    """Speichere Reference Audio fuer Voice Cloning"""
    try:
        # Speichere als WAV (24kHz mono)
        voice_path = VOICES_DIR / f"{name}.wav"
        
        # Lade und konvertiere Audio
        audio_buffer = io.BytesIO(audio)
        data, sr = sf.read(audio_buffer)
        
        # Resample zu 24kHz wenn noetig
        if sr != 24000:
            import resampy
            data = resampy.resample(data, sr, 24000)
        
        # Mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        
        # Speichere
        sf.write(voice_path, data, 24000)
        
        return {"status": "ok", "voice": name}
        
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/voices")
async def list_voices():
    """Liste verfuegbare Stimmen"""
    # Built-in Kokoro voices
    voices = KOKORO_VOICES.copy()
    
    # Custom voices
    for f in VOICES_DIR.glob("*.wav"):
        voice_name = f.stem
        if voice_name not in voices:
            voices.append(voice_name)
    
    return {
        "voices": voices,
        "models": list(AVAILABLE_MODELS.keys()),
        "languages": {"a": "American English", "b": "British English"}
    }


@app.get("/health")
async def health():
    """Health Check"""
    loaded = list(models.keys())
    return {
        "status": "ok",
        "engine": "mlx-audio",
        "device": "Apple Silicon (MPS)",
        "models_loaded": loaded,
        "available_models": list(AVAILABLE_MODELS.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8768)
