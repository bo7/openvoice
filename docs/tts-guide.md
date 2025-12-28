# TTS/STT Service Guide

This guide explains how to use the Text-to-Speech and Speech-to-Text services available on the internal WireGuard network.

## Prerequisites

- Connected to WireGuard VPN network (10.200.0.0/24)
- Network access to mac2 (10.200.0.12)

## Server Information

| Property | Value |
|----------|-------|
| Host | mac2 / 10.200.0.12 |
| Local IP | 192.168.2.147 |
| Hardware | Mac Studio M3 Ultra, 512GB RAM, 80 GPU cores |

## Available Services

| Service | Port | Type | Engine |
|---------|------|------|--------|
| Whisper | 8765 | STT | Speech-to-Text transcription |
| XTTS v2 | 8766 | TTS | Voice cloning, 16 languages |
| Chatterbox | 8767 | TTS | Expressive emotional speech |
| MLX Server | 8768 | TTS | Apple Silicon optimized |
| Kokoro | 8769 | TTS | Fast, 11 preset voices |
| OpenAudio S1 | 8770 | TTS | Best quality, 50+ emotions |

## Base URLs

```
http://10.200.0.12:PORT
```

Or using hostname (if DNS configured):
```
http://mac2:PORT
```

---

## Whisper STT (Port 8765)

Speech-to-Text transcription service.

### Transcribe Audio File

```bash
curl -X POST http://10.200.0.12:8765/transcribe \
  -F "file=@recording.wav"
```

Response:
```json
{
  "text": "Hello, this is the transcribed text.",
  "language": "en"
}
```

### Transcribe with Language Hint

```bash
curl -X POST http://10.200.0.12:8765/transcribe \
  -F "file=@recording.wav" \
  -F "language=de"
```

### Python Example

```python
import requests

def transcribe(audio_path, language=None):
    url = "http://10.200.0.12:8765/transcribe"
    
    with open(audio_path, "rb") as f:
        files = {"file": f}
        data = {"language": language} if language else {}
        response = requests.post(url, files=files, data=data)
    
    return response.json()

# Usage
result = transcribe("recording.wav")
print(result["text"])
```

---

## XTTS v2 (Port 8766)

Voice cloning with 16 language support.

### Supported Languages

en, de, fr, es, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, ko, hu

### Basic TTS

```bash
curl -X POST http://10.200.0.12:8766/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en"}' \
  --output speech.wav
```

### TTS with Cloned Voice

```bash
curl -X POST http://10.200.0.12:8766/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en", "voice": "my_voice"}' \
  --output speech.wav
```

### Clone a Voice

```bash
curl -X POST http://10.200.0.12:8766/clone \
  -F "name=my_voice" \
  -F "audio=@reference.wav"
```

### List Available Voices

```bash
curl http://10.200.0.12:8766/voices
```

### Python Example

```python
import requests

XTTS_URL = "http://10.200.0.12:8766"

def xtts_speak(text, language="en", voice=None, output_path="output.wav"):
    payload = {"text": text, "language": language}
    if voice:
        payload["voice"] = voice
    
    response = requests.post(f"{XTTS_URL}/tts", json=payload)
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

def xtts_clone(name, audio_path):
    with open(audio_path, "rb") as f:
        files = {"audio": f}
        data = {"name": name}
        response = requests.post(f"{XTTS_URL}/clone", files=files, data=data)
    return response.json()

# Usage
xtts_speak("Guten Tag, wie geht es Ihnen?", language="de")
xtts_clone("my_voice", "reference_audio.wav")
```

---

## Chatterbox (Port 8767)

Expressive emotional speech synthesis with fine control.

### Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| exaggeration | 0.0 - 2.0 | 0.5 | Expression intensity |
| cfg_weight | 0.0 - 1.0 | 0.5 | Classifier-free guidance |
| temperature | 0.1 - 1.5 | 0.8 | Randomness in generation |

### Best Clone Settings

For faithful voice reproduction:
- exaggeration: 0.15
- cfg_weight: 0.9
- temperature: 0.3

### Basic TTS

```bash
curl -X POST http://10.200.0.12:8767/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav
```

### Expressive TTS

```bash
curl -X POST http://10.200.0.12:8767/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is exciting news!",
    "exaggeration": 0.8,
    "cfg_weight": 0.4,
    "temperature": 0.9
  }' \
  --output expressive.wav
```

### Best Clone Quality

```bash
curl -X POST http://10.200.0.12:8767/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This should sound like the original voice.",
    "voice": "my_voice",
    "exaggeration": 0.15,
    "cfg_weight": 0.9,
    "temperature": 0.3
  }' \
  --output clone.wav
```

### Python Example

```python
import requests

CHATTERBOX_URL = "http://10.200.0.12:8767"

# Preset configurations
PRESETS = {
    "best_clone": {"exaggeration": 0.15, "cfg_weight": 0.9, "temperature": 0.3},
    "natural": {"exaggeration": 0.25, "cfg_weight": 0.8, "temperature": 0.4},
    "expressive": {"exaggeration": 0.8, "cfg_weight": 0.4, "temperature": 0.9},
    "dramatic": {"exaggeration": 1.2, "cfg_weight": 0.3, "temperature": 1.0},
    "calm": {"exaggeration": 0.1, "cfg_weight": 0.85, "temperature": 0.35},
}

def chatterbox_speak(text, preset="best_clone", voice=None, output_path="output.wav"):
    params = PRESETS.get(preset, PRESETS["best_clone"])
    
    payload = {
        "text": text,
        **params
    }
    if voice:
        payload["voice"] = voice
    
    response = requests.post(f"{CHATTERBOX_URL}/tts", json=payload)
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

# Usage
chatterbox_speak("Hello, how are you?", preset="best_clone")
chatterbox_speak("This is amazing!", preset="expressive")
```

---

## Kokoro (Port 8769)

Fastest TTS engine with 11 high-quality preset voices.

### Available Voices

| Voice ID | Description |
|----------|-------------|
| af_heart | Female, warm (default) |
| af_nova | Female |
| af_bella | Female |
| af_sarah | Female |
| af_nicole | Female |
| bf_emma | British Female |
| bf_isabella | British Female |
| am_adam | Male |
| am_michael | Male |
| bm_george | British Male |
| bm_lewis | British Male |

### Check Status

```bash
curl http://10.200.0.12:8769/
```

### List Voices

```bash
curl http://10.200.0.12:8769/voices
```

### Basic TTS

```bash
curl -X POST http://10.200.0.12:8769/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav
```

### TTS with Voice Selection

```bash
curl -X POST http://10.200.0.12:8769/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "am_adam"}' \
  --output speech.wav
```

### TTS with Speed Adjustment

```bash
curl -X POST http://10.200.0.12:8769/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "af_bella", "speed": 1.2}' \
  --output speech.wav
```

### Python Example

```python
import requests

KOKORO_URL = "http://10.200.0.12:8769"

VOICES = [
    "af_heart", "af_nova", "af_bella", "af_sarah", "af_nicole",
    "bf_emma", "bf_isabella",
    "am_adam", "am_michael",
    "bm_george", "bm_lewis"
]

def kokoro_speak(text, voice="af_heart", speed=1.0, output_path="output.wav"):
    payload = {
        "text": text,
        "voice": voice,
        "speed": speed
    }
    
    response = requests.post(f"{KOKORO_URL}/tts", json=payload)
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

def list_voices():
    response = requests.get(f"{KOKORO_URL}/voices")
    return response.json()

# Usage
kokoro_speak("Hello, this is a test.", voice="am_adam")
kokoro_speak("Speaking faster now.", voice="af_bella", speed=1.3)
```

---

## OpenAudio S1 (Port 8770)

State-of-the-art TTS with 50+ emotions and 14 languages.

### Supported Languages

en, zh, ja, ko, fr, de, es, pt, it, ru, ar, nl, pl, th

### Emotion Markers

Add emotion to speech by prefixing text with markers:

| Marker | Effect |
|--------|--------|
| (angry) | Angry tone |
| (sad) | Sad tone |
| (excited) | Excited tone |
| (whisper) | Whispered speech |
| (laugh) | Laughing |
| (cry) | Crying |
| (sigh) | Sighing |
| (nervous) | Nervous tone |
| (fearful) | Fearful tone |
| (surprised) | Surprised tone |
| (cheerful) | Cheerful tone |
| (serious) | Serious tone |
| (gentle) | Gentle tone |
| (sleepy) | Sleepy tone |

### Health Check

```bash
curl http://10.200.0.12:8770/v1/health
```

### Basic TTS

```bash
curl -X POST http://10.200.0.12:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "format": "wav"}' \
  --output speech.wav
```

### Emotional TTS

```bash
curl -X POST http://10.200.0.12:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "(excited) This is amazing news!", "format": "wav"}' \
  --output excited.wav
```

### Whispered Speech

```bash
curl -X POST http://10.200.0.12:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "(whisper) This is a secret.", "format": "wav"}' \
  --output whisper.wav
```

### Best Clone Settings

```bash
curl -X POST http://10.200.0.12:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This should sound natural.",
    "format": "wav",
    "temperature": 0.3,
    "top_p": 0.7
  }' \
  --output clone.wav
```

### Python Example

```python
import requests

OPENAUDIO_URL = "http://10.200.0.12:8770"

EMOTIONS = [
    "angry", "sad", "excited", "whisper", "laugh", "cry", "sigh",
    "nervous", "fearful", "surprised", "cheerful", "serious", "gentle", "sleepy"
]

def openaudio_speak(text, emotion=None, temperature=0.3, top_p=0.7, output_path="output.wav"):
    if emotion:
        text = f"({emotion}) {text}"
    
    payload = {
        "text": text,
        "format": "wav",
        "temperature": temperature,
        "top_p": top_p
    }
    
    response = requests.post(f"{OPENAUDIO_URL}/v1/tts", json=payload)
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

def openaudio_health():
    response = requests.get(f"{OPENAUDIO_URL}/v1/health")
    return response.json()

# Usage
openaudio_speak("Hello, how are you today?")
openaudio_speak("I cannot believe this happened!", emotion="surprised")
openaudio_speak("Let me tell you a secret.", emotion="whisper")
```

---

## Complete Python Client

A unified client for all TTS services:

```python
import requests
from pathlib import Path

class TTSClient:
    def __init__(self, base_ip="10.200.0.12"):
        self.servers = {
            "whisper": f"http://{base_ip}:8765",
            "xtts": f"http://{base_ip}:8766",
            "chatterbox": f"http://{base_ip}:8767",
            "kokoro": f"http://{base_ip}:8769",
            "openaudio": f"http://{base_ip}:8770",
        }
    
    def transcribe(self, audio_path, language=None):
        """Speech-to-Text with Whisper"""
        with open(audio_path, "rb") as f:
            files = {"file": f}
            data = {"language": language} if language else {}
            response = requests.post(
                f"{self.servers['whisper']}/transcribe",
                files=files, data=data
            )
        return response.json()["text"]
    
    def speak_kokoro(self, text, voice="af_heart", speed=1.0):
        """Fast TTS with preset voices"""
        response = requests.post(
            f"{self.servers['kokoro']}/tts",
            json={"text": text, "voice": voice, "speed": speed}
        )
        return response.content
    
    def speak_xtts(self, text, language="en", voice=None):
        """Multilingual TTS with cloning"""
        payload = {"text": text, "language": language}
        if voice:
            payload["voice"] = voice
        response = requests.post(
            f"{self.servers['xtts']}/tts",
            json=payload
        )
        return response.content
    
    def speak_chatterbox(self, text, voice=None, preset="best_clone"):
        """Expressive TTS with fine control"""
        presets = {
            "best_clone": {"exaggeration": 0.15, "cfg_weight": 0.9, "temperature": 0.3},
            "expressive": {"exaggeration": 0.8, "cfg_weight": 0.4, "temperature": 0.9},
        }
        params = presets.get(preset, presets["best_clone"])
        payload = {"text": text, **params}
        if voice:
            payload["voice"] = voice
        response = requests.post(
            f"{self.servers['chatterbox']}/tts",
            json=payload
        )
        return response.content
    
    def speak_openaudio(self, text, emotion=None, temperature=0.3):
        """Best quality TTS with emotions"""
        if emotion:
            text = f"({emotion}) {text}"
        response = requests.post(
            f"{self.servers['openaudio']}/v1/tts",
            json={"text": text, "format": "wav", "temperature": temperature}
        )
        return response.content
    
    def save(self, audio_data, path):
        """Save audio data to file"""
        Path(path).write_bytes(audio_data)
        return path
    
    def health_check(self):
        """Check all server status"""
        status = {}
        endpoints = {
            "whisper": "/health",
            "xtts": "/health",
            "chatterbox": "/health",
            "kokoro": "/",
            "openaudio": "/v1/health",
        }
        for name, endpoint in endpoints.items():
            try:
                r = requests.get(f"{self.servers[name]}{endpoint}", timeout=3)
                status[name] = "online" if r.status_code == 200 else "error"
            except:
                status[name] = "offline"
        return status

# Usage
tts = TTSClient()

# Check status
print(tts.health_check())

# Transcribe audio
text = tts.transcribe("recording.wav")
print(f"Transcribed: {text}")

# Generate speech with different engines
tts.save(tts.speak_kokoro("Fast response needed"), "kokoro.wav")
tts.save(tts.speak_xtts("Guten Tag", language="de"), "xtts_german.wav")
tts.save(tts.speak_chatterbox("Faithful voice clone", preset="best_clone"), "chatterbox.wav")
tts.save(tts.speak_openaudio("Amazing news!", emotion="excited"), "openaudio.wav")
```

---

## JavaScript/Node.js Client

```javascript
const fs = require("fs");
const fetch = require("node-fetch");
const FormData = require("form-data");

const BASE_IP = "10.200.0.12";

const SERVERS = {
  whisper: `http://${BASE_IP}:8765`,
  xtts: `http://${BASE_IP}:8766`,
  chatterbox: `http://${BASE_IP}:8767`,
  kokoro: `http://${BASE_IP}:8769`,
  openaudio: `http://${BASE_IP}:8770`,
};

async function transcribe(audioPath) {
  const form = new FormData();
  form.append("file", fs.createReadStream(audioPath));
  
  const response = await fetch(`${SERVERS.whisper}/transcribe`, {
    method: "POST",
    body: form,
  });
  
  const data = await response.json();
  return data.text;
}

async function speakKokoro(text, voice = "af_heart", speed = 1.0) {
  const response = await fetch(`${SERVERS.kokoro}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, speed }),
  });
  
  return Buffer.from(await response.arrayBuffer());
}

async function speakOpenAudio(text, emotion = null) {
  const finalText = emotion ? `(${emotion}) ${text}` : text;
  
  const response = await fetch(`${SERVERS.openaudio}/v1/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: finalText,
      format: "wav",
      temperature: 0.3,
    }),
  });
  
  return Buffer.from(await response.arrayBuffer());
}

// Usage
async function main() {
  // Transcribe
  const text = await transcribe("recording.wav");
  console.log(`Transcribed: ${text}`);
  
  // Generate speech
  const audio = await speakKokoro("Hello world", "am_adam");
  fs.writeFileSync("output.wav", audio);
  
  const excited = await speakOpenAudio("This is amazing!", "excited");
  fs.writeFileSync("excited.wav", excited);
}

main();
```

---

## Engine Selection Guide

| Use Case | Recommended Engine | Why |
|----------|-------------------|-----|
| Quick responses | Kokoro | Fastest generation |
| Voice cloning | XTTS or Chatterbox | Best clone support |
| Multiple languages | XTTS | 16 languages |
| Emotional speech | OpenAudio | 50+ emotions |
| Best quality | OpenAudio | State-of-the-art |
| Fine control | Chatterbox | Adjustable parameters |

## Best Clone Settings Summary

For maximum fidelity to original voice:

| Engine | Settings |
|--------|----------|
| XTTS | Default |
| Chatterbox | exaggeration=0.15, cfg_weight=0.9, temperature=0.3 |
| OpenAudio | temperature=0.3, top_p=0.7 |

## Troubleshooting

### Connection Refused
- Check WireGuard connection: `wg show`
- Ping the server: `ping 10.200.0.12`
- Check specific port: `nc -zv 10.200.0.12 8769`

### Timeout Errors
- Long text may take time to process
- Increase timeout in requests
- Consider breaking text into smaller chunks

### Audio Quality Issues
- Use clean reference audio for cloning
- Avoid background noise
- Try different engines for comparison

### Server Not Responding
- Check if service is running on mac2
- Review server logs
- Restart the specific service

## Network Configuration

If connecting from outside WireGuard:

```bash
# SSH tunnel for single port
ssh -L 8769:localhost:8769 user@gateway

# Multiple ports
ssh -L 8766:10.200.0.12:8766 \
    -L 8767:10.200.0.12:8767 \
    -L 8769:10.200.0.12:8769 \
    -L 8770:10.200.0.12:8770 \
    user@gateway
```

## Related Resources

- OpenVoice Hub: http://10.200.0.12:5050
- Ollama Guide: [ollama-guide.md](ollama-guide.md)
