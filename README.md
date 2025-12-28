# Mac2 TTS/STT Server Documentation

Mac Studio M2 Ultra (192.168.2.147 / WireGuard: 10.200.0.12)
512GB RAM, 96 GPU cores

## Server Overview

| Port | Server | Model | Engine | Use Case |
|------|--------|-------|--------|----------|
| 8765 | Speech Server | Whisper | STT | Speech-to-Text transcription |
| 8766 | XTTS Server | XTTS v2 | CPU | Voice cloning, multilingual TTS |
| 8767 | Chatterbox | Chatterbox | MPS | Expressive emotional TTS |
| 8768 | MLX Server | Various | MLX | Apple Silicon optimized inference |
| 8769 | Kokoro | Kokoro-82M | MLX | Fast, high-quality TTS (11 voices) |
| 8770 | OpenAudio | S1-mini 0.5B | MPS | Emotional TTS, 50+ emotions, multilingual |

---

## 1. Speech Server (Whisper STT) - Port 8765

**Location:** `~/speech-server/`
**Purpose:** Speech-to-Text transcription

### Usage

```bash
# Transcribe audio file
curl -X POST http://mac2:8765/transcribe \
  -F "file=@audio.wav"

# Transcribe with language hint
curl -X POST http://mac2:8765/transcribe \
  -F "file=@audio.wav" \
  -F "language=en"
```

### Response
```json
{
  "text": "Transcribed text here",
  "language": "en"
}
```

---

## 2. XTTS Server - Port 8766

**Location:** `~/xtts-server/`
**Purpose:** Voice cloning and multilingual text-to-speech

### Usage

```bash
# Basic TTS (default voice)
curl -X POST http://mac2:8766/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en"}' \
  --output speech.wav

# Voice cloning (provide reference audio)
curl -X POST http://mac2:8766/tts \
  -F "text=Hello world" \
  -F "language=en" \
  -F "speaker_wav=@reference_voice.wav" \
  --output cloned_speech.wav
```

### Supported Languages
`en`, `de`, `fr`, `es`, `it`, `pt`, `pl`, `tr`, `ru`, `nl`, `cs`, `ar`, `zh-cn`, `ja`, `ko`, `hu`

---

## 3. Chatterbox Server - Port 8767

**Location:** `~/chatterbox-server/`
**Purpose:** Expressive emotional speech synthesis

### Usage

```bash
# Basic TTS
curl -X POST http://mac2:8767/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav

# With exaggeration (0.0 - 1.0, higher = more expressive)
curl -X POST http://mac2:8767/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "This is exciting!", "exaggeration": 0.7}' \
  --output expressive.wav

# Voice cloning
curl -X POST http://mac2:8767/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "audio_prompt_path": "/path/to/reference.wav"}' \
  --output cloned.wav
```

---

## 4. MLX Server - Port 8768

**Location:** `~/mlx_server.py`
**Purpose:** Apple Silicon optimized model inference

### Usage

```bash
# Check status
curl http://mac2:8768/

# Model-specific endpoints vary
curl http://mac2:8768/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your prompt here"}'
```

---

## 5. Kokoro Server - Port 8769

**Location:** `~/kokoro-server/`
**Model:** Kokoro-82M (MLX-native, Apple Silicon optimized)
**Purpose:** Fast, high-quality TTS with 11 preset voices

### Available Voices

| Voice ID | Description |
|----------|-------------|
| af_heart | Female, warm |
| af_nova | Female |
| af_bella | Female |
| af_sarah | Female |
| af_nicole | Female |
| bf_emma | British female |
| bf_isabella | British female |
| am_adam | Male |
| am_michael | Male |
| bm_george | British male |
| bm_lewis | British male |

### Usage

```bash
# Check status and list voices
curl http://mac2:8769/

# List all voices
curl http://mac2:8769/voices

# Basic TTS (default voice: af_heart)
curl -X POST http://mac2:8769/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav

# TTS with specific voice
curl -X POST http://mac2:8769/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "am_adam"}' \
  --output speech.wav

# TTS with speed adjustment (0.5 - 2.0)
curl -X POST http://mac2:8769/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "af_bella", "speed": 1.2}' \
  --output speech.wav

# Save to specific path
curl -X POST http://mac2:8769/tts/save \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "bm_george", "output_path": "/tmp/output.wav"}'
```

### Response Format
Returns WAV audio file (mono, 24kHz)

---

## 6. OpenAudio Server (S1-mini) - Port 8770

**Location:** `~/fish-speech-repo/`
**Model:** OpenAudio S1-mini (0.5B parameters)
**Purpose:** State-of-the-art TTS with 50+ emotions, multilingual support

### Features
- 50+ emotional markers
- 14 languages supported
- Voice cloning from 10-30 second samples
- RLHF-optimized for natural speech

### Emotional Markers
Use these in your text to control emotion:
- `(angry)` - Angry tone
- `(sad)` - Sad tone
- `(excited)` - Excited tone
- `(whisper)` - Whispered speech
- `(laugh)` - Laughing
- `(cry)` - Crying
- `(sigh)` - Sighing
- `(nervous)` - Nervous tone
- `(fearful)` - Fearful tone
- `(surprised)` - Surprised tone
- `(cheerful)` - Cheerful tone
- `(serious)` - Serious tone

### Usage

```bash
# Health check
curl http://mac2:8770/v1/health

# Basic TTS
curl -X POST http://mac2:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "format": "wav"}' \
  --output speech.wav

# TTS with emotion
curl -X POST http://mac2:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "(excited) This is amazing news!", "format": "wav"}' \
  --output excited.wav

# TTS with whisper
curl -X POST http://mac2:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "(whisper) This is a secret.", "format": "wav"}' \
  --output whisper.wav

# Voice cloning (requires reference audio in references/ folder)
curl -X POST http://mac2:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "reference_id": "my_voice", "format": "wav"}' \
  --output cloned.wav
```

### Supported Languages
English, Chinese, Japanese, Korean, French, German, Spanish, Portuguese, Italian, Russian, Arabic, Dutch, Polish, Thai

### Output Formats
- `wav` - WAV audio (default)
- `mp3` - MP3 audio
- `flac` - FLAC audio

---

## Quick Start Examples

### Python Client Example

```python
import requests

# Kokoro TTS
def kokoro_tts(text, voice="af_heart"):
    response = requests.post(
        "http://mac2:8769/tts",
        json={"text": text, "voice": voice}
    )
    with open("output.wav", "wb") as f:
        f.write(response.content)

# OpenAudio TTS with emotion
def openaudio_tts(text, emotion=None):
    if emotion:
        text = f"({emotion}) {text}"
    response = requests.post(
        "http://mac2:8770/v1/tts",
        json={"text": text, "format": "wav"}
    )
    with open("output.wav", "wb") as f:
        f.write(response.content)

# Whisper STT
def transcribe(audio_path):
    with open(audio_path, "rb") as f:
        response = requests.post(
            "http://mac2:8765/transcribe",
            files={"file": f}
        )
    return response.json()["text"]

# Usage
kokoro_tts("Hello from Kokoro!", voice="am_adam")
openaudio_tts("This is exciting!", emotion="excited")
text = transcribe("recording.wav")
```

---

## Service Management

### Start/Stop Services

```bash
# List all LaunchAgents
launchctl list | grep etl-kontor

# Start a service
launchctl load ~/Library/LaunchAgents/com.etl-kontor.kokoro-server.plist

# Stop a service
launchctl unload ~/Library/LaunchAgents/com.etl-kontor.kokoro-server.plist

# Check service status
launchctl print gui/$(id -u)/com.etl-kontor.kokoro-server
```

### LaunchAgent Locations
- Kokoro: `~/Library/LaunchAgents/com.etl-kontor.kokoro-server.plist`
- OpenAudio: `~/Library/LaunchAgents/com.etl-kontor.openaudio-server.plist`
- XTTS: `~/Library/LaunchAgents/com.etl-kontor.xtts-server.plist`
- Chatterbox: `~/Library/LaunchAgents/com.etl-kontor.chatterbox-server.plist`
- Speech: `~/Library/LaunchAgents/com.etl-kontor.speech-server.plist`

### Check Running Servers

```bash
# Check which ports are in use
netstat -an | grep LISTEN | grep -E '876[5-9]|8770'

# Check server processes
ps aux | grep -E 'server.py|xtts|chatterbox|kokoro|api_server'
```

---

## Network Access

### From Local Network
```
http://192.168.2.147:PORT
```

### Via WireGuard VPN
```
http://10.200.0.12:PORT
```

### Via SSH Tunnel
```bash
ssh -L 8769:localhost:8769 mac2
# Then access: http://localhost:8769
```

---

## Troubleshooting

### Server not responding
1. Check if process is running: `ps aux | grep server`
2. Check logs: `tail -f ~/SERVICE_NAME/server.log`
3. Restart service: `launchctl unload ... && launchctl load ...`

### Out of memory
1. Check memory usage: `top -l 1 | head -20`
2. Stop unused servers to free memory
3. XTTS uses ~8GB, OpenAudio uses ~2GB, Kokoro uses ~500MB

### Audio quality issues
- Increase sample rate if supported
- For voice cloning, use clean 10-30 second reference audio
- Avoid background noise in reference samples

---

## Model Comparison

| Model | Speed | Quality | Voice Cloning | Emotions | Languages |
|-------|-------|---------|---------------|----------|-----------|
| Kokoro | Very Fast | High | No | No | EN only |
| XTTS | Slow | High | Yes | Limited | 16 |
| Chatterbox | Medium | High | Yes | Yes | EN |
| OpenAudio | Medium | Excellent | Yes | 50+ | 14 |

**Recommendations:**
- **Fast responses:** Kokoro (8769)
- **Voice cloning:** XTTS (8766) or OpenAudio (8770)
- **Emotional speech:** OpenAudio (8770) or Chatterbox (8767)
- **Multilingual:** XTTS (8766) or OpenAudio (8770)
