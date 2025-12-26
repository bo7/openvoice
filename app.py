#!/usr/bin/env python3
"""
Voice Cloning Web Interface
Flask Frontend fuer XTTS und Chatterbox Server
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import base64

app = Flask(__name__)

XTTS_URL = "http://mac2ol:8766"
CHATTERBOX_URL = "http://mac2ol:8767"

# Chatterbox Presets
CHATTERBOX_PRESETS = {
    "neutral": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "label": "Neutral"},
    "calm": {"exaggeration": 0.2, "cfg_weight": 0.7, "temperature": 0.5, "label": "Ruhig"},
    "expressive": {"exaggeration": 0.8, "cfg_weight": 0.4, "temperature": 0.9, "label": "Expressiv"},
    "dramatic": {"exaggeration": 1.2, "cfg_weight": 0.3, "temperature": 0.9, "label": "Dramatisch"},
    "monotone": {"exaggeration": 0.1, "cfg_weight": 0.8, "temperature": 0.3, "label": "Monoton"},
    "energetic": {"exaggeration": 1.0, "cfg_weight": 0.5, "temperature": 1.0, "label": "Energisch"},
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/voiceClone", methods=["GET", "POST"])
def voice_clone():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        audio = request.files.get("audio")
        engine = request.form.get("engine", "xtts")
        
        if not name:
            return render_template("clone.html", error="Name fehlt", 
                                   xtts_voices=get_voices("xtts"), 
                                   chatterbox_voices=get_voices("chatterbox"))
        if not audio:
            return render_template("clone.html", error="Audiodatei fehlt", 
                                   xtts_voices=get_voices("xtts"),
                                   chatterbox_voices=get_voices("chatterbox"))
        
        url = XTTS_URL if engine == "xtts" else CHATTERBOX_URL
        files = {"audio": (audio.filename, audio.stream, audio.content_type)}
        data = {"name": name}
        
        try:
            r = requests.post(f"{url}/clone", files=files, data=data)
            if r.status_code == 200:
                return render_template("clone.html", 
                    success=f"Stimme '{name}' erfolgreich geklont ({engine.upper()})!", 
                    xtts_voices=get_voices("xtts"),
                    chatterbox_voices=get_voices("chatterbox"))
            else:
                return render_template("clone.html", 
                    error=r.json().get("detail", "Fehler beim Klonen"), 
                    xtts_voices=get_voices("xtts"),
                    chatterbox_voices=get_voices("chatterbox"))
        except Exception as e:
            return render_template("clone.html", error=str(e), 
                                   xtts_voices=get_voices("xtts"),
                                   chatterbox_voices=get_voices("chatterbox"))
    
    return render_template("clone.html", 
                           xtts_voices=get_voices("xtts"),
                           chatterbox_voices=get_voices("chatterbox"))


@app.route("/talk", methods=["GET", "POST"])
def talk():
    xtts_voices = get_voices("xtts")
    chatterbox_voices = get_voices("chatterbox")
    languages = get_languages()
    
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        voice = request.form.get("voice", "sven")
        language = request.form.get("language", "de")
        engine = request.form.get("engine", "xtts")
        preset = request.form.get("preset", "neutral")
        
        # Custom Chatterbox params
        exaggeration = float(request.form.get("exaggeration", 0.5))
        cfg_weight = float(request.form.get("cfg_weight", 0.5))
        temperature = float(request.form.get("temperature", 0.8))
        
        if not text:
            return render_template("talk.html", error="Text fehlt", 
                xtts_voices=xtts_voices, chatterbox_voices=chatterbox_voices,
                languages=languages, presets=CHATTERBOX_PRESETS)
        
        try:
            if engine == "chatterbox":
                # Preset oder custom
                if preset != "custom":
                    params = CHATTERBOX_PRESETS.get(preset, CHATTERBOX_PRESETS["neutral"])
                    exaggeration = params["exaggeration"]
                    cfg_weight = params["cfg_weight"]
                    temperature = params["temperature"]
                
                r = requests.post(f"{CHATTERBOX_URL}/tts", json={
                    "text": text.replace("\n", " ").replace("\r", ""),
                    "voice": voice,
                    "language": language,
                    "exaggeration": exaggeration,
                    "cfg_weight": cfg_weight,
                    "temperature": temperature
                }, timeout=180)
            else:
                r = requests.post(f"{XTTS_URL}/tts", json={
                    "text": text.replace("\n", " ").replace("\r", ""),
                    "voice": voice,
                    "language": language
                }, timeout=60)
            
            if r.status_code == 200:
                audio_b64 = base64.b64encode(r.content).decode()
                return render_template("talk.html", 
                    xtts_voices=xtts_voices, chatterbox_voices=chatterbox_voices,
                    languages=languages, presets=CHATTERBOX_PRESETS,
                    audio=audio_b64, text=text, 
                    selected_voice=voice, selected_language=language,
                    selected_engine=engine, selected_preset=preset,
                    exaggeration=exaggeration, cfg_weight=cfg_weight, temperature=temperature)
            else:
                error = r.json().get("detail", "TTS Fehler") if r.headers.get("content-type", "").startswith("application/json") else "TTS Fehler"
                return render_template("talk.html", error=error, 
                    xtts_voices=xtts_voices, chatterbox_voices=chatterbox_voices,
                    languages=languages, presets=CHATTERBOX_PRESETS)
        except requests.exceptions.Timeout:
            return render_template("talk.html", error="Timeout - Text zu lang oder Server ueberlastet", 
                xtts_voices=xtts_voices, chatterbox_voices=chatterbox_voices,
                languages=languages, presets=CHATTERBOX_PRESETS)
        except Exception as e:
            return render_template("talk.html", error=str(e), 
                xtts_voices=xtts_voices, chatterbox_voices=chatterbox_voices,
                languages=languages, presets=CHATTERBOX_PRESETS)
    
    return render_template("talk.html", 
        xtts_voices=xtts_voices, chatterbox_voices=chatterbox_voices,
        languages=languages, presets=CHATTERBOX_PRESETS)


@app.route("/api/voices")
def api_voices():
    return jsonify({
        "xtts": get_voices("xtts"),
        "chatterbox": get_voices("chatterbox")
    })


@app.route("/api/health")
def api_health():
    status = {}
    try:
        r = requests.get(f"{XTTS_URL}/health", timeout=5)
        status["xtts"] = r.json() if r.status_code == 200 else {"status": "error"}
    except:
        status["xtts"] = {"status": "offline"}
    
    try:
        r = requests.get(f"{CHATTERBOX_URL}/health", timeout=5)
        status["chatterbox"] = r.json() if r.status_code == 200 else {"status": "error"}
    except:
        status["chatterbox"] = {"status": "offline"}
    
    return jsonify(status)


def get_voices(engine="xtts"):
    url = XTTS_URL if engine == "xtts" else CHATTERBOX_URL
    try:
        r = requests.get(f"{url}/voices", timeout=5)
        return r.json().get("voices", [])
    except:
        return []


def get_languages():
    try:
        r = requests.get(f"{XTTS_URL}/voices", timeout=5)
        return r.json().get("languages", ["de", "en"])
    except:
        return ["de", "en"]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
