#!/usr/bin/env python3
"""
OpenVoice - Multi-Engine TTS Hub
Flask Frontend for XTTS, Chatterbox, Kokoro, OpenAudio
With optimized presets for best voice cloning quality
"""

from flask import Flask, render_template, request, jsonify
import requests
import base64

app = Flask(__name__)

# Server Configuration
SERVERS = {
    "xtts": {
        "url": "http://mac2:8766",
        "name": "XTTS v2",
        "desc": "Voice cloning, 16 languages",
        "port": 8766,
        "supports_cloning": True,
        "supports_emotions": False,
        "languages": ["en", "de", "fr", "es", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hu"]
    },
    "chatterbox": {
        "url": "http://mac2:8767",
        "name": "Chatterbox",
        "desc": "Expressive emotional speech",
        "port": 8767,
        "supports_cloning": True,
        "supports_emotions": True,
        "languages": ["en"]
    },
    "kokoro": {
        "url": "http://mac2:8769",
        "name": "Kokoro",
        "desc": "Fast, 11 preset voices",
        "port": 8769,
        "supports_cloning": False,
        "supports_emotions": False,
        "languages": ["en"]
    },
    "openaudio": {
        "url": "http://mac2:8770",
        "name": "OpenAudio S1",
        "desc": "50+ emotions, 14 languages",
        "port": 8770,
        "supports_cloning": True,
        "supports_emotions": True,
        "languages": ["en", "zh", "ja", "ko", "fr", "de", "es", "pt", "it", "ru", "ar", "nl", "pl", "th"]
    },
}

# Chatterbox Presets - Optimized for different use cases
CHATTERBOX_PRESETS = {
    "best_clone": {
        "exaggeration": 0.15,
        "cfg_weight": 0.9,
        "temperature": 0.3,
        "label": "Best Clone (Faithful)",
        "description": "Maximum fidelity to original voice"
    },
    "natural_clone": {
        "exaggeration": 0.25,
        "cfg_weight": 0.8,
        "temperature": 0.4,
        "label": "Natural Clone",
        "description": "Faithful with natural variation"
    },
    "balanced": {
        "exaggeration": 0.5,
        "cfg_weight": 0.5,
        "temperature": 0.7,
        "label": "Balanced",
        "description": "Balance between clone and expression"
    },
    "expressive": {
        "exaggeration": 0.8,
        "cfg_weight": 0.4,
        "temperature": 0.9,
        "label": "Expressive",
        "description": "More emotional range"
    },
    "dramatic": {
        "exaggeration": 1.2,
        "cfg_weight": 0.3,
        "temperature": 1.0,
        "label": "Dramatic",
        "description": "Maximum expression"
    },
    "calm": {
        "exaggeration": 0.1,
        "cfg_weight": 0.85,
        "temperature": 0.35,
        "label": "Calm & Steady",
        "description": "Relaxed, consistent delivery"
    },
    "newsreader": {
        "exaggeration": 0.2,
        "cfg_weight": 0.75,
        "temperature": 0.5,
        "label": "Newsreader",
        "description": "Professional, clear diction"
    },
}

# Kokoro Voices
KOKORO_VOICES = {
    "af_heart": "Heart (Female, warm)",
    "af_nova": "Nova (Female)",
    "af_bella": "Bella (Female)",
    "af_sarah": "Sarah (Female)",
    "af_nicole": "Nicole (Female)",
    "bf_emma": "Emma (British Female)",
    "bf_isabella": "Isabella (British Female)",
    "am_adam": "Adam (Male)",
    "am_michael": "Michael (Male)",
    "bm_george": "George (British Male)",
    "bm_lewis": "Lewis (British Male)",
}

# OpenAudio Emotions
OPENAUDIO_EMOTIONS = [
    "", "angry", "sad", "excited", "whisper", "laugh", "cry", "sigh",
    "nervous", "fearful", "surprised", "cheerful", "serious", "gentle",
    "sleepy", "confused", "disgusted", "proud", "relieved", "shy"
]

# OpenAudio Presets
OPENAUDIO_PRESETS = {
    "best_clone": {
        "temperature": 0.3,
        "top_p": 0.7,
        "repetition_penalty": 1.1,
        "label": "Best Clone",
        "description": "Maximum fidelity to reference voice"
    },
    "natural": {
        "temperature": 0.5,
        "top_p": 0.8,
        "repetition_penalty": 1.15,
        "label": "Natural",
        "description": "Natural speech with slight variation"
    },
    "expressive": {
        "temperature": 0.8,
        "top_p": 0.9,
        "repetition_penalty": 1.2,
        "label": "Expressive",
        "description": "More emotional range"
    },
}


@app.route("/")
def index():
    return render_template("index.html", servers=SERVERS)


@app.route("/clone", methods=["GET", "POST"])
def voice_clone():
    all_voices = get_all_voices()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        audio = request.files.get("audio")
        engine = request.form.get("engine", "xtts")
        
        if not name:
            return render_template("clone.html", error="Name required",
                                   voices=all_voices, servers=SERVERS)
        if not audio:
            return render_template("clone.html", error="Audio file required",
                                   voices=all_voices, servers=SERVERS)
        
        server = SERVERS.get(engine, SERVERS["xtts"])
        if not server.get("supports_cloning"):
            return render_template("clone.html", 
                error=f"{server['name']} does not support voice cloning",
                voices=all_voices, servers=SERVERS)
        
        url = server["url"]
        files = {"audio": (audio.filename, audio.stream, audio.content_type)}
        data = {"name": name}
        
        try:
            r = requests.post(f"{url}/clone", files=files, data=data, timeout=120)
            if r.status_code == 200:
                return render_template("clone.html",
                    success=f"Voice '{name}' cloned successfully ({server['name']})!",
                    voices=get_all_voices(), servers=SERVERS)
            else:
                error = r.json().get("detail", "Cloning failed") if "json" in r.headers.get("content-type", "") else f"Error {r.status_code}"
                return render_template("clone.html", error=error,
                                       voices=all_voices, servers=SERVERS)
        except Exception as e:
            return render_template("clone.html", error=str(e),
                                   voices=all_voices, servers=SERVERS)
    
    return render_template("clone.html", voices=all_voices, servers=SERVERS)


@app.route("/talk", methods=["GET", "POST"])
def talk():
    all_voices = get_all_voices()
    
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        voice = request.form.get("voice", "")
        language = request.form.get("language", "en")
        engine = request.form.get("engine", "xtts")
        
        # Engine-specific params
        preset = request.form.get("preset", "best_clone")
        emotion = request.form.get("emotion", "")
        speed = float(request.form.get("speed", 1.0))
        
        # Chatterbox params
        exaggeration = float(request.form.get("exaggeration", 0.15))
        cfg_weight = float(request.form.get("cfg_weight", 0.9))
        temperature = float(request.form.get("temperature", 0.3))
        
        # OpenAudio params
        oa_temperature = float(request.form.get("oa_temperature", 0.3))
        top_p = float(request.form.get("top_p", 0.7))
        
        if not text:
            return render_template("talk.html", error="Text required",
                voices=all_voices, servers=SERVERS,
                chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)
        
        server = SERVERS.get(engine)
        if not server:
            return render_template("talk.html", error="Unknown engine",
                voices=all_voices, servers=SERVERS,
                chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)
        
        url = server["url"]
        clean_text = text.replace("\n", " ").replace("\r", "").strip()
        
        try:
            # XTTS
            if engine == "xtts":
                r = requests.post(f"{url}/tts", json={
                    "text": clean_text,
                    "voice": voice,
                    "language": language
                }, timeout=120)
            
            # Chatterbox
            elif engine == "chatterbox":
                if preset != "custom" and preset in CHATTERBOX_PRESETS:
                    p = CHATTERBOX_PRESETS[preset]
                    exaggeration = p["exaggeration"]
                    cfg_weight = p["cfg_weight"]
                    temperature = p["temperature"]
                
                r = requests.post(f"{url}/tts", json={
                    "text": clean_text,
                    "voice": voice if voice else None,
                    "exaggeration": exaggeration,
                    "cfg_weight": cfg_weight,
                    "temperature": temperature
                }, timeout=180)
            
            # Kokoro
            elif engine == "kokoro":
                r = requests.post(f"{url}/tts", json={
                    "text": clean_text,
                    "voice": voice if voice else "af_heart",
                    "speed": speed
                }, timeout=60)
            
            # OpenAudio
            elif engine == "openaudio":
                # Add emotion marker if selected
                if emotion:
                    clean_text = f"({emotion}) {clean_text}"
                
                if preset != "custom" and preset in OPENAUDIO_PRESETS:
                    p = OPENAUDIO_PRESETS[preset]
                    oa_temperature = p["temperature"]
                    top_p = p["top_p"]
                
                payload = {
                    "text": clean_text,
                    "format": "wav",
                    "temperature": oa_temperature,
                    "top_p": top_p
                }
                if voice:
                    payload["reference_id"] = voice
                
                r = requests.post(f"{url}/v1/tts", json=payload, timeout=180)
            
            else:
                return render_template("talk.html", error="Engine not implemented",
                    voices=all_voices, servers=SERVERS,
                    chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                    openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)
            
            if r.status_code == 200 and "audio" in r.headers.get("content-type", "") or r.headers.get("content-type", "").startswith("audio"):
                audio_b64 = base64.b64encode(r.content).decode()
                return render_template("talk.html",
                    voices=all_voices, servers=SERVERS,
                    chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                    openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS,
                    audio=audio_b64, text=text,
                    selected_voice=voice, selected_language=language,
                    selected_engine=engine, selected_preset=preset,
                    selected_emotion=emotion, speed=speed,
                    exaggeration=exaggeration, cfg_weight=cfg_weight,
                    temperature=temperature, oa_temperature=oa_temperature, top_p=top_p)
            else:
                # Check if response is WAV despite content-type
                if r.status_code == 200 and len(r.content) > 100:
                    audio_b64 = base64.b64encode(r.content).decode()
                    return render_template("talk.html",
                        voices=all_voices, servers=SERVERS,
                        chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                        openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS,
                        audio=audio_b64, text=text,
                        selected_voice=voice, selected_language=language,
                        selected_engine=engine, selected_preset=preset,
                        selected_emotion=emotion, speed=speed,
                        exaggeration=exaggeration, cfg_weight=cfg_weight,
                        temperature=temperature, oa_temperature=oa_temperature, top_p=top_p)
                
                try:
                    error = r.json().get("detail", r.json().get("message", f"TTS Error {r.status_code}"))
                except:
                    error = f"TTS Error {r.status_code}: {r.text[:200]}"
                return render_template("talk.html", error=error,
                    voices=all_voices, servers=SERVERS,
                    chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                    openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)
                    
        except requests.exceptions.Timeout:
            return render_template("talk.html", error="Timeout - text too long or server busy",
                voices=all_voices, servers=SERVERS,
                chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)
        except Exception as e:
            return render_template("talk.html", error=str(e),
                voices=all_voices, servers=SERVERS,
                chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
                openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)
    
    return render_template("talk.html",
        voices=all_voices, servers=SERVERS,
        chatterbox_presets=CHATTERBOX_PRESETS, kokoro_voices=KOKORO_VOICES,
        openaudio_emotions=OPENAUDIO_EMOTIONS, openaudio_presets=OPENAUDIO_PRESETS)


@app.route("/api/voices")
def api_voices():
    return jsonify(get_all_voices())


@app.route("/api/health")
def api_health():
    status = {}
    for engine, server in SERVERS.items():
        try:
            if engine == "openaudio":
                r = requests.get(f"{server['url']}/v1/health", timeout=3)
            else:
                r = requests.get(f"{server['url']}/health", timeout=3)
            status[engine] = {"status": "ok"} if r.status_code == 200 else {"status": "error"}
        except:
            status[engine] = {"status": "offline"}
    return jsonify(status)


@app.route("/api/tts", methods=["POST"])
def api_tts():
    """Direct API endpoint for TTS"""
    data = request.json
    text = data.get("text", "")
    engine = data.get("engine", "kokoro")
    voice = data.get("voice", "")
    
    server = SERVERS.get(engine)
    if not server:
        return jsonify({"error": "Unknown engine"}), 400
    
    try:
        if engine == "kokoro":
            r = requests.post(f"{server['url']}/tts", json={
                "text": text,
                "voice": voice or "af_heart",
                "speed": data.get("speed", 1.0)
            }, timeout=60)
        elif engine == "openaudio":
            r = requests.post(f"{server['url']}/v1/tts", json={
                "text": text,
                "format": "wav"
            }, timeout=180)
        elif engine == "chatterbox":
            r = requests.post(f"{server['url']}/tts", json={
                "text": text,
                "exaggeration": data.get("exaggeration", 0.15),
                "cfg_weight": data.get("cfg_weight", 0.9),
                "temperature": data.get("temperature", 0.3)
            }, timeout=180)
        else:  # xtts
            r = requests.post(f"{server['url']}/tts", json={
                "text": text,
                "voice": voice,
                "language": data.get("language", "en")
            }, timeout=120)
        
        if r.status_code == 200:
            return r.content, 200, {"Content-Type": "audio/wav"}
        return jsonify({"error": f"TTS failed: {r.status_code}"}), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_all_voices():
    """Get voices from all servers"""
    voices = {}
    
    # Kokoro - static list
    voices["kokoro"] = list(KOKORO_VOICES.keys())
    
    for engine, server in SERVERS.items():
        if engine == "kokoro":
            continue
        try:
            if engine == "openaudio":
                # OpenAudio uses reference IDs from references/ folder
                r = requests.get(f"{server['url']}/v1/health", timeout=3)
                voices[engine] = []  # Reference voices need to be set up
            else:
                r = requests.get(f"{server['url']}/voices", timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    voices[engine] = data.get("voices", data) if isinstance(data, dict) else data
        except:
            voices[engine] = []
    
    return voices


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
