# OpenVoice Hub

Multi-Engine Text-to-Speech System running on Mac Studio M3 Ultra.

## Features

- 4 TTS Engines: Kokoro, XTTS v2, Chatterbox, OpenAudio S1
- Voice Cloning with multiple engines
- 50+ Emotional speech markers
- 16 languages support
- Best Clone presets for faithful voice reproduction
- Side-by-side engine comparison

## Quick Start

```bash
# Start the Flask server
python app.py

# Access at http://localhost:5050
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Home - Engine overview and status |
| `/talk` | Text-to-Speech with engine selection |
| `/compare` | Compare all engines with same text |
| `/clone` | Clone a voice from audio sample |

## TTS Engines

### Kokoro (Port 8769)
- Fastest engine
- 11 preset voices (no cloning)
- English only
- MLX-optimized for Apple Silicon

### XTTS v2 (Port 8766)
- Voice cloning support
- 16 languages
- CPU-based, slower but reliable

### Chatterbox (Port 8767)
- Expressive emotional speech
- Voice cloning with fine control
- English only
- Parameters: exaggeration, cfg_weight, temperature

### OpenAudio S1 (Port 8770)
- State-of-the-art quality
- 50+ emotion markers
- 14 languages
- Voice cloning support

## Best Clone Settings

Settings optimized for maximum fidelity to original voice:

| Engine | Settings |
|--------|----------|
| Chatterbox | exaggeration=0.15, cfg_weight=0.9, temperature=0.3 |
| OpenAudio | temperature=0.3, top_p=0.7 |
| XTTS | Default (optimized internally) |
| Kokoro | speed=1.0 (preset voices only) |

## API Endpoints

### Health Check
```bash
curl http://localhost:5050/api/health
```

### List Voices
```bash
curl http://localhost:5050/api/voices
```

### Language Info
```bash
curl http://localhost:5050/api/languages
```

### Direct TTS
```bash
curl -X POST http://localhost:5050/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "engine": "kokoro", "voice": "af_heart"}' \
  --output speech.wav
```

### Compare Engines
```bash
curl -X POST http://localhost:5050/api/compare \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en"}'
```

## Direct Server Access

Each TTS engine runs on its own port:

| Engine | Port | Health Endpoint |
|--------|------|-----------------|
| Whisper STT | 8765 | /health |
| XTTS | 8766 | /health |
| Chatterbox | 8767 | /health |
| MLX Server | 8768 | / |
| Kokoro | 8769 | / |
| OpenAudio | 8770 | /v1/health |

## Language Support

Languages supported by ALL cloning engines: English (en)

Full language matrix:

| Language | XTTS | Chatterbox | Kokoro | OpenAudio |
|----------|------|------------|--------|-----------|
| English | Yes | Yes | Yes | Yes |
| German | Yes | - | - | Yes |
| French | Yes | - | - | Yes |
| Spanish | Yes | - | - | Yes |
| Italian | Yes | - | - | Yes |
| Portuguese | Yes | - | - | Yes |
| Chinese | Yes | - | - | Yes |
| Japanese | Yes | - | - | Yes |
| Korean | Yes | - | - | Yes |
| Russian | Yes | - | - | Yes |

## Voice Cloning Tips

1. Use 10-30 seconds of clear speech
2. Avoid background noise
3. Natural speaking with varied intonation
4. WAV or MP3 format, any sample rate
5. Use "Best Clone" preset for faithful reproduction

## Infrastructure

- Server: Mac Studio M3 Ultra
- RAM: 512GB
- GPU Cores: 96
- Network: WireGuard VPN (10.200.0.12)
- Local IP: 192.168.2.147

## Files

```
openvoice/
  app.py              # Flask application
  templates/
    index.html        # Home page
    talk.html         # TTS interface
    compare.html      # Engine comparison
    clone.html        # Voice cloning
  README.md           # This file
```

## Related Documentation

- [Ollama LLM Guide](docs/ollama-guide.md) - Using LLM models
- [TTS Server Guide](docs/tts-guide.md) - Using TTS/STT services

## License

MIT
