#!/usr/bin/env python3
"""
OpenVoice - Multi-Engine TTS Hub
Flask Frontend for XTTS, Chatterbox, Kokoro, OpenAudio
With optimized presets for best voice cloning quality
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

app = Flask(__name__)

# Server Configuration
SERVERS = {
    "xtts": {
        "url": "http://10.200.0.12:8766",
        "name": "XTTS v2",
        "desc": "Voice cloning, 16 languages",
        "port": 8766,
        "supports_cloning": True,
        "supports_emotions": False,
        "languages": ["en", "de", "fr", "es", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hu"]
    },
    "chatterbox": {
        "url": "http://10.200.0.12:8767",
        "name": "Chatterbox",
        "desc": "Expressive emotional speech",
        "port": 8767,
        "supports_cloning": True,
        "supports_emotions": True,
        "languages": ["en"]
    },
    "kokoro": {
        "url": "http://10.200.0.12:8769",
        "name": "Kokoro",
        "desc": "Fast, 11 preset voices",
        "port": 8769,
        "supports_cloning": False,
        "supports_emotions": False,
        "languages": ["en"]
    },
    "openaudio": {
        "url": "http://10.200.0.12:8770",
        "name": "OpenAudio S1",
        "desc": "50+ emotions, 14 languages",
        "port": 8770,
        "supports_cloning": True,
        "supports_emotions": True,
        "languages": ["en", "zh", "ja", "ko", "fr", "de", "es", "pt", "it", "ru", "ar", "nl", "pl", "th"]
    },
}

# Best clone settings for each engine
BEST_CLONE_SETTINGS = {
    "xtts": {
        "name": "XTTS v2",
        "settings": {},  # XTTS uses default settings for cloning
        "description": "16 languages, faithful reproduction"
    },
    "chatterbox": {
        "name": "Chatterbox",
        "settings": {
            "exaggeration": 0.15,
            "cfg_weight": 0.9,
            "temperature": 0.3
        },
        "description": "Low exaggeration, high CFG for faithful clone"
    },
    "kokoro": {
        "name": "Kokoro",
        "settings": {
            "speed": 1.0
        },
        "description": "Preset voices only (no cloning)"
    },
    "openaudio": {
        "name": "OpenAudio S1",
        "settings": {
            "temperature": 0.3,
            "top_p": 0.7,
            "repetition_penalty": 1.1
        },
        "description": "Low temperature for consistent output"
    }
}

# Language name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "de": "German", 
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hu": "Hungarian",
    "th": "Thai"
}

# Chatterbox Presets
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


def get_common_languages():
    """Get languages supported by ALL engines that support cloning"""
    clone_engines = [k for k, v in SERVERS.items() if v.get("supports_cloning")]
    if not clone_engines:
        return []
    
    common = set(SERVERS[clone_engines[0]]["languages"])
    for engine in clone_engines[1:]:
        common = common.intersection(set(SERVERS[engine]["languages"]))
    
    return sorted(list(common))


def get_all_languages():
    """Get all unique languages across all engines"""
    all_langs = set()
    for srv in SERVERS.values():
        all_langs.update(srv.get("languages", []))
    return sorted(list(all_langs))


def generate_tts_for_engine(engine, text, language, voice=None):
    """Generate TTS for a single engine with best clone settings"""
    server = SERVERS.get(engine)
    if not server:
        return {"engine": engine, "error": "Unknown engine", "audio": None, "time": 0}
    
    # Check if language is supported
    if language not in server.get("languages", []):
        return {"engine": engine, "error": f"Language '{language}' not supported", "audio": None, "time": 0}
    
    url = server["url"]
    settings = BEST_CLONE_SETTINGS.get(engine, {}).get("settings", {})
    clean_text = text.replace("\n", " ").replace("\r", "").strip()
    
    start_time = time.time()
    
    try:
        if engine == "xtts":
            payload = {"text": clean_text, "language": language}
            payload["voice"] = voice if voice else "sven"  # Default voice
            r = requests.post(f"{url}/tts", json=payload, timeout=120)
            
        elif engine == "chatterbox":
            payload = {
                "text": clean_text,
                "exaggeration": settings.get("exaggeration", 0.15),
                "cfg_weight": settings.get("cfg_weight", 0.9),
                "temperature": settings.get("temperature", 0.3)
            }
            payload["voice"] = voice if voice else "sven"  # Default voice
            r = requests.post(f"{url}/tts", json=payload, timeout=180)
            
        elif engine == "kokoro":
            payload = {
                "text": clean_text,
                "voice": voice if voice else "af_heart",
                "speed": settings.get("speed", 1.0)
            }
            r = requests.post(f"{url}/tts", json=payload, timeout=60)
            
        elif engine == "openaudio":
            payload = {
                "text": clean_text,
                "format": "wav",
                "temperature": settings.get("temperature", 0.3),
                "top_p": settings.get("top_p", 0.7)
            }
            payload["reference_id"] = voice if voice else "sven"  # Default voice
            r = requests.post(f"{url}/v1/tts", json=payload, timeout=180)
            
        else:
            return {"engine": engine, "error": "Engine not implemented", "audio": None, "time": 0}
        
        elapsed = round(time.time() - start_time, 2)
        
        if r.status_code == 200 and len(r.content) > 100:
            audio_b64 = base64.b64encode(r.content).decode()
            return {
                "engine": engine,
                "name": server["name"],
                "audio": audio_b64,
                "time": elapsed,
                "error": None,
                "settings": settings
            }
        else:
            try:
                error = r.json().get("detail", r.json().get("message", f"Error {r.status_code}"))
            except:
                error = f"Error {r.status_code}"
            return {"engine": engine, "name": server["name"], "error": error, "audio": None, "time": elapsed}
            
    except requests.exceptions.Timeout:
        elapsed = round(time.time() - start_time, 2)
        return {"engine": engine, "name": server["name"], "error": "Timeout", "audio": None, "time": elapsed}
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        return {"engine": engine, "name": server["name"], "error": str(e), "audio": None, "time": elapsed}


@app.route("/")
def index():
    return render_template("index.html", servers=SERVERS)


@app.route("/compare", methods=["GET", "POST"])
def compare():
    """Compare all engines with the same text using best clone settings"""
    common_languages = get_common_languages()
    all_languages = get_all_languages()
    results = []
    
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        language = request.form.get("language", "en")
        voice = request.form.get("voice", "")
        run_parallel = request.form.get("parallel", "true") == "true"
        
        if not text:
            return render_template("compare.html",
                error="Text required",
                common_languages=common_languages,
                all_languages=all_languages,
                language_names=LANGUAGE_NAMES,
                servers=SERVERS,
                best_settings=BEST_CLONE_SETTINGS)
        
        # Determine which engines to run based on language
        engines_to_run = []
        for engine, srv in SERVERS.items():
            if language in srv.get("languages", []):
                engines_to_run.append(engine)
        
        if not engines_to_run:
            return render_template("compare.html",
                error=f"No engine supports language '{language}'",
                common_languages=common_languages,
                all_languages=all_languages,
                language_names=LANGUAGE_NAMES,
                servers=SERVERS,
                best_settings=BEST_CLONE_SETTINGS)
        
        # Run TTS for all compatible engines
        if run_parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(generate_tts_for_engine, engine, text, language, voice): engine
                    for engine in engines_to_run
                }
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            for engine in engines_to_run:
                results.append(generate_tts_for_engine(engine, text, language, voice))
        
        # Sort by engine name for consistent display
        results.sort(key=lambda x: x.get("engine", ""))
        
        return render_template("compare.html",
            results=results,
            text=text,
            selected_language=language,
            common_languages=common_languages,
            all_languages=all_languages,
            language_names=LANGUAGE_NAMES,
            servers=SERVERS,
            best_settings=BEST_CLONE_SETTINGS,
            engines_run=engines_to_run)
    
    return render_template("compare.html",
        common_languages=common_languages,
        all_languages=all_languages,
        language_names=LANGUAGE_NAMES,
        servers=SERVERS,
        best_settings=BEST_CLONE_SETTINGS)


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
            else:
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
    health_endpoints = {
        "xtts": "/health",
        "chatterbox": "/health",
        "kokoro": "/",
        "openaudio": "/v1/health"
    }
    for engine, server in SERVERS.items():
        try:
            endpoint = health_endpoints.get(engine, "/health")
            r = requests.get(f"{server['url']}{endpoint}", timeout=3)
            status[engine] = {"status": "ok"} if r.status_code == 200 else {"status": "error"}
        except:
            status[engine] = {"status": "offline"}
    return jsonify(status)


@app.route("/api/languages")
def api_languages():
    """Get language information"""
    return jsonify({
        "common": get_common_languages(),
        "all": get_all_languages(),
        "by_engine": {k: v.get("languages", []) for k, v in SERVERS.items()},
        "names": LANGUAGE_NAMES
    })


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """API endpoint for comparing all engines"""
    data = request.json
    text = data.get("text", "")
    language = data.get("language", "en")
    voice = data.get("voice", "")
    
    if not text:
        return jsonify({"error": "Text required"}), 400
    
    results = []
    for engine, srv in SERVERS.items():
        if language in srv.get("languages", []):
            result = generate_tts_for_engine(engine, text, language, voice)
            results.append(result)
    
    return jsonify({"results": results, "language": language})


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
    
    voices["kokoro"] = list(KOKORO_VOICES.keys())
    
    for engine, server in SERVERS.items():
        if engine == "kokoro":
            continue
        try:
            if engine == "openaudio":
                r = requests.get(f"{server['url']}/v1/health", timeout=3)
                voices[engine] = []
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
