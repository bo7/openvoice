# OpenVoice Hub

Multi-Engine Text-to-Speech System running on Mac Studio M3 Ultra.

## Features

- 4 TTS Engines: Kokoro, XTTS v2, Chatterbox, OpenAudio S1
- Voice Cloning with browser recording or file upload
- CLI tool for batch processing and long documents
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
| `/clone` | Clone a voice - record or upload |

## Voice Cloning

Two ways to clone your voice:

### Browser Recording
1. Go to `/clone`
2. Click "Record Voice" tab
3. Click the red button to start recording
4. Speak for 10-30 seconds
5. Review playback, then click "Clone Voice"
6. Choose target engine(s): All, XTTS, Chatterbox, or OpenAudio

### File Upload
1. Go to `/clone`
2. Click "Upload File" tab
3. Drag & drop or select audio file (WAV, MP3)
4. Enter voice name
5. Select target engine

## CLI Tool

For batch processing and long documents, use `tts_generator.py`:

```bash
# Simple usage
python tts_generator.py "Hello world" -o speech.flac

# Long document with cloned voice
python tts_generator.py -f document.txt -o audiobook.mp3 \
    --voice sven --engine openaudio --lang de

# Check servers
python tts_generator.py --check

# List voices
python tts_generator.py --list-voices
```

See [TTS_CLI.md](TTS_CLI.md) for full documentation.

## TTS Engines

| Engine | Port | Speed | Cloning | Languages |
|--------|------|-------|---------|-----------|
| Kokoro | 8769 | Fast | No | en |
| XTTS v2 | 8766 | Medium | Yes | 16 |
| Chatterbox | 8767 | Slow | Yes | en |
| OpenAudio | 8770 | Slow | Yes | 14 |

### Kokoro
- Fastest engine, MLX-optimized for Apple Silicon
- 11 preset voices (af_heart, am_adam, bf_emma, etc.)
- Best quality for preset voices

### XTTS v2
- Voice cloning support
- 16 languages including German
- Reliable, CPU-based

### Chatterbox
- Expressive emotional speech
- Fine control: exaggeration, cfg_weight, temperature
- Best for expressive clones

### OpenAudio S1
- State-of-the-art quality
- 50+ emotion markers (happy, sad, excited, etc.)
- Best for high-fidelity clones

## Best Clone Settings

| Engine | Settings |
|--------|----------|
| Chatterbox | exaggeration=0.15, cfg_weight=0.9, temperature=0.3 |
| OpenAudio | temperature=0.3, top_p=0.7 |
| XTTS | Default (optimized internally) |

## API Endpoints

```bash
# Health check
curl http://localhost:5050/api/health

# List voices
curl http://localhost:5050/api/voices

# Text-to-Speech
curl -X POST http://localhost:5050/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "engine": "kokoro", "voice": "af_heart"}' \
  --output speech.wav

# Compare all engines
curl -X POST http://localhost:5050/api/compare \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en"}'
```

## Voice Sample

A reference voice sample is included: `samples/sven.wav`

Use it to clone the "sven" voice on any engine.

## Language Support

| Language | XTTS | OpenAudio | Kokoro | Chatterbox |
|----------|------|-----------|--------|------------|
| English | Yes | Yes | Yes | Yes |
| German | Yes | Yes | - | - |
| French | Yes | Yes | - | - |
| Spanish | Yes | Yes | - | - |
| Chinese | Yes | Yes | - | - |
| Japanese | Yes | Yes | - | - |

## Infrastructure

- Server: Mac Studio M3 Ultra
- RAM: 512GB
- GPU Cores: 80
- Network: WireGuard VPN (10.200.0.12)

## Files

```
openvoice/
  app.py                  # Flask application
  tts_generator.py        # CLI tool
  samples/
    sven.wav              # Voice sample
  templates/
    index.html            # Home
    talk.html             # TTS interface
    compare.html          # Engine comparison
    clone.html            # Voice cloning
  docs/
    tts-guide.md          # TTS server guide
    ollama-guide.md       # LLM guide
    n8n-podcast-prompt.md # Podcast automation
```

## Documentation

- [TTS CLI Tool](TTS_CLI.md) - Command-line usage
- [TTS Server Guide](docs/tts-guide.md) - Direct API access
- [Ollama LLM Guide](docs/ollama-guide.md) - Using LLM models
- [n8n Podcast Automation](docs/n8n-podcast-prompt.md) - Automated workflows

## License

MIT
