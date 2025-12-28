#!/usr/bin/env python3
"""
Voice Cloning Web Interface
Flask Frontend fuer XTTS, Chatterbox, MLX-Audio und Fish Speech
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import base64

app = Flask(__name__)

# Server URLs
SERVERS = {
    "xtts": {"url": "http://mac2:8766", "name": "XTTS v2", "desc": "Coqui XTTS - 17 Sprachen"},
    "chatterbox": {"url": "http://mac2:8767", "name": "Chatterbox", "desc": "ResembleAI - Expressiv"},
    "mlx": {"url": "http://mac2:8768", "name": "MLX-Audio", "desc": "Kokoro/Marvis - Apple Silicon"},
    # "fish": {"url": "http://mac2:8769", "name": "Fish Speech", "desc": "OpenAudio - Decoder-Bug"},
}

# Chatterbox Presets
CHATTERBOX_PRESETS = {
    "clone": {"exaggeration": 0.3, "cfg_weight": 0.8, "temperature": 0.4, "label": "Klon-Treue"},
    "neutral": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "label": "Neutral"},
    "calm": {"exaggeration": 0.2, "cfg_weight": 0.7, "temperature": 0.5, "label": "Ruhig"},
    "expressive": {"exaggeration": 0.8, "cfg_weight": 0.4, "temperature": 0.9, "label": "Expressiv"},
    "dramatic": {"exaggeration": 1.2, "cfg_weight": 0.3, "temperature": 0.9, "label": "Dramatisch"},
    "monotone": {"exaggeration": 0.1, "cfg_weight": 0.8, "temperature": 0.3, "label": "Monoton"},
    "energetic": {"exaggeration": 1.0, "cfg_weight": 0.5, "temperature": 1.0, "label": "Energisch"},
}

# MLX Models
MLX_MODELS = {
    "kokoro": "Kokoro 82M - Schnell",
    "marvis": "Marvis 250M - Voice Cloning",
}


@app.route("/")
def index():
    return render_template("index.html", servers=SERVERS)


@app.route("/voiceClone", methods=["GET", "POST"])
def voice_clone():
    all_voices = get_all_voices()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        audio = request.files.get("audio")
        engine = request.form.get("engine", "xtts")
        
        if not name:
            return render_template("clone.html", error="Name fehlt", 
                                   voices=all_voices, servers=SERVERS)
        if not audio:
            return render_template("clone.html", error="Audiodatei fehlt", 
                                   voices=all_voices, servers=SERVERS)
        
        server = SERVERS.get(engine, SERVERS["xtts"])
        url = server["url"]
        files = {"audio": (audio.filename, audio.stream, audio.content_type)}
        data = {"name": name}
        
        try:
            r = requests.post(f"{url}/clone", files=files, data=data, timeout=60)
            if r.status_code == 200:
                return render_template("clone.html", 
                    success=f"Stimme '{name}' erfolgreich geklont ({server['name']})!", 
                    voices=get_all_voices(), servers=SERVERS)
            else:
                error = r.json().get("detail", "Fehler beim Klonen") if r.headers.get("content-type", "").startswith("application/json") else "Fehler"
                return render_template("clone.html", error=error, 
                                       voices=all_voices, servers=SERVERS)
        except Exception as e:
            return render_template("clone.html", error=str(e), 
                                   voices=all_voices, servers=SERVERS)
    
    return render_template("clone.html", voices=all_voices, servers=SERVERS)


@app.route("/talk", methods=["GET", "POST"])
def talk():
    all_voices = get_all_voices()
    languages = get_languages()
    
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        voice = request.form.get("voice", "sven")
        language = request.form.get("language", "de")
        engine = request.form.get("engine", "xtts")
        preset = request.form.get("preset", "neutral")
        mlx_model = request.form.get("mlx_model", "kokoro")
        
        # Custom params
        exaggeration = float(request.form.get("exaggeration", 0.5))
        cfg_weight = float(request.form.get("cfg_weight", 0.5))
        temperature = float(request.form.get("temperature", 0.8))
        speed = float(request.form.get("speed", 1.0))
        
        if not text:
            return render_template("talk.html", error="Text fehlt", 
                voices=all_voices, languages=languages, 
                presets=CHATTERBOX_PRESETS, mlx_models=MLX_MODELS, servers=SERVERS)
        
        server = SERVERS.get(engine, SERVERS["xtts"])
        url = server["url"]
        
        try:
            # Engine-spezifische Requests
            if engine == "chatterbox":
                if preset != "custom":
                    params = CHATTERBOX_PRESETS.get(preset, CHATTERBOX_PRESETS["neutral"])
                    exaggeration = params["exaggeration"]
                    cfg_weight = params["cfg_weight"]
                    temperature = params["temperature"]
                
                r = requests.post(f"{url}/tts", json={
                    "text": text.replace("\n", " ").replace("\r", ""),
                    "voice": voice,
                    "language": language,
                    "exaggeration": exaggeration,
                    "cfg_weight": cfg_weight,
                    "temperature": temperature
                }, timeout=180)
                
            elif engine == "mlx":
                r = requests.post(f"{url}/tts", json={
                    "text": text.replace("\n", " ").replace("\r", ""),
                    "voice": voice,
                    "model": mlx_model,
                    "speed": speed,
                    "language": "a" if language == "en" else "b",
                    "temperature": temperature
                }, timeout=120)
                
            elif engine == "fish":
                r = requests.post(f"{url}/tts", json={
                    "text": text.replace("\n", " ").replace("\r", ""),
                    "voice": voice,
                    "language": language,
                    "temperature": temperature
                }, timeout=180)
                
            else:  # xtts
                r = requests.post(f"{url}/tts", json={
                    "text": text.replace("\n", " ").replace("\r", ""),
                    "voice": voice,
                    "language": language
                }, timeout=60)
            
            if r.status_code == 200:
                audio_b64 = base64.b64encode(r.content).decode()
                return render_template("talk.html", 
                    voices=all_voices, languages=languages,
                    presets=CHATTERBOX_PRESETS, mlx_models=MLX_MODELS, servers=SERVERS,
                    audio=audio_b64, text=text, 
                    selected_voice=voice, selected_language=language,
                    selected_engine=engine, selected_preset=preset,
                    selected_mlx_model=mlx_model,
                    exaggeration=exaggeration, cfg_weight=cfg_weight, 
                    temperature=temperature, speed=speed)
            else:
                error = r.json().get("detail", "TTS Fehler") if r.headers.get("content-type", "").startswith("application/json") else f"TTS Fehler: {r.status_code}"
                return render_template("talk.html", error=error, 
                    voices=all_voices, languages=languages,
                    presets=CHATTERBOX_PRESETS, mlx_models=MLX_MODELS, servers=SERVERS)
                    
        except requests.exceptions.Timeout:
            return render_template("talk.html", error="Timeout - Text zu lang oder Server ueberlastet", 
                voices=all_voices, languages=languages,
                presets=CHATTERBOX_PRESETS, mlx_models=MLX_MODELS, servers=SERVERS)
        except Exception as e:
            return render_template("talk.html", error=str(e), 
                voices=all_voices, languages=languages,
                presets=CHATTERBOX_PRESETS, mlx_models=MLX_MODELS, servers=SERVERS)
    
    return render_template("talk.html", 
        voices=all_voices, languages=languages,
        presets=CHATTERBOX_PRESETS, mlx_models=MLX_MODELS, servers=SERVERS)


@app.route("/api/voices")
def api_voices():
    return jsonify(get_all_voices())


@app.route("/api/health")
def api_health():
    status = {}
    for engine, server in SERVERS.items():
        try:
            r = requests.get(f"{server['url']}/health", timeout=5)
            status[engine] = r.json() if r.status_code == 200 else {"status": "error"}
        except:
            status[engine] = {"status": "offline"}
    return jsonify(status)


def get_all_voices():
    """Hole Stimmen von allen Servern"""
    voices = {}
    for engine, server in SERVERS.items():
        try:
            r = requests.get(f"{server['url']}/voices", timeout=5)
            if r.status_code == 200:
                data = r.json()
                voices[engine] = data.get("voices", [])
        except:
            voices[engine] = []
    return voices


def get_languages():
    """Standard Sprachen"""
    return {
        "de": "Deutsch",
        "en": "English",
        "es": "Espanol",
        "fr": "Francais",
        "it": "Italiano",
        "pt": "Portugues",
        "pl": "Polski",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
