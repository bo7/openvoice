# TTS Generator CLI

Command-line tool for converting long text to speech using multiple TTS engines.

## Features

- Multiple TTS engines: Kokoro, OpenAudio, XTTS, Chatterbox
- Automatic text chunking for long documents
- Voice cloning support (sven)
- Multiple output formats: WAV, FLAC, MP3, OGG
- Language support: en, de, fr, es, it, pt, and more

## Installation

```bash
# Clone the repository
git clone https://github.com/bo7/openvoice.git
cd openvoice

# No additional dependencies needed if servers are running
# FFmpeg required for format conversion
brew install ffmpeg  # macOS
```

## Requirements

- Python 3.8+
- FFmpeg (for format conversion)
- TTS servers running on mac2 (10.200.0.12)
- WireGuard VPN connection

## Quick Start

```bash
# Check server status
python3 tts_generator.py --check

# Simple text to speech
python3 tts_generator.py "Hello world" -o speech.flac

# German text with cloned voice
python3 tts_generator.py "Guten Tag, wie geht es Ihnen?" \
    --voice sven --engine openaudio --lang de -o german.mp3
```

## Usage

```
python3 tts_generator.py [TEXT] [OPTIONS]

Arguments:
  TEXT                    Text to convert (or use -f for file input)

Options:
  -f, --file FILE         Read text from file
  -o, --output FILE       Output file (default: output.wav)
  --format FORMAT         Output format: wav, flac, mp3, ogg, aac, m4a
  --voice VOICE           Voice selection (see below)
  --engine ENGINE         TTS engine: kokoro, openaudio, xtts, chatterbox
  --lang LANG             Language code (default: en)
  --speed SPEED           Speech speed for Kokoro (default: 1.0)
  --chunk-size SIZE       Max characters per chunk (default: 500)
  -q, --quiet             Suppress progress output
  --list-voices           List available voices
  --check                 Check server availability
```

## Voices

### Preset Voices (Kokoro)

| Alias | Voice ID | Description |
|-------|----------|-------------|
| female | af_heart | Female, warm (default) |
| male | am_adam | Male, American |
| female_british | bf_emma | Female, British |
| male_british | bm_george | Male, British |

### All Kokoro Voices

```
af_heart, af_nova, af_bella, af_sarah, af_nicole
bf_emma, bf_isabella
am_adam, am_michael
bm_george, bm_lewis
```

### Cloned Voices

| Voice | Engines | Description |
|-------|---------|-------------|
| sven | openaudio, xtts, chatterbox | Custom cloned voice |

## Engines

| Engine | Speed | Quality | Cloning | Languages |
|--------|-------|---------|---------|-----------|
| kokoro | Fast | Best | No | en |
| openaudio | Slow | Excellent | Yes | 14 |
| xtts | Medium | Good | Yes | 16 |
| chatterbox | Slow | Good | Yes | en |

## Examples

### Basic Usage

```bash
# Female voice (default)
python3 tts_generator.py "Hello world" -o hello.mp3

# Male voice
python3 tts_generator.py "Hello world" -o hello.mp3 --voice male

# Specific Kokoro voice
python3 tts_generator.py "Hello world" -o hello.mp3 --voice bf_emma
```

### Voice Cloning

```bash
# Using cloned "sven" voice with OpenAudio
python3 tts_generator.py "Dies ist ein Test." \
    --voice sven --engine openaudio --lang de -o test.flac

# Using cloned voice with XTTS (good for German)
python3 tts_generator.py "Guten Morgen!" \
    --voice sven --engine xtts --lang de -o morgen.mp3
```

### Long Documents

```bash
# From file
python3 tts_generator.py -f document.txt -o audiobook.mp3 --voice female

# From stdin
cat article.txt | python3 tts_generator.py -o article.flac

# With custom chunk size
python3 tts_generator.py -f long_text.txt -o output.flac --chunk-size 300
```

### Output Formats

```bash
# Lossless (recommended for archiving)
python3 tts_generator.py "Text" -o speech.flac

# Uncompressed
python3 tts_generator.py "Text" -o speech.wav

# Compressed (smallest file size)
python3 tts_generator.py "Text" -o speech.mp3

# Open format
python3 tts_generator.py "Text" -o speech.ogg
```

## Output Format Comparison

| Format | Type | Size | Quality | Use Case |
|--------|------|------|---------|----------|
| FLAC | Lossless | Medium | Perfect | Archiving, editing |
| WAV | Lossless | Large | Perfect | Raw audio, editing |
| MP3 | Lossy | Small | Good | Distribution, podcasts |
| OGG | Lossy | Small | Good | Web, open source |

## Voice Sample

A reference voice sample is included in `samples/sven.wav`. This can be used to clone the voice on other TTS engines or as a reference.

## Server Configuration

The tool expects TTS servers at these addresses:

| Engine | URL |
|--------|-----|
| Kokoro | http://10.200.0.12:8769 |
| OpenAudio | http://10.200.0.12:8770 |
| XTTS | http://10.200.0.12:8766 |
| Chatterbox | http://10.200.0.12:8767 |

To use different servers, edit the `SERVERS` dict in `tts_generator.py`.

## Troubleshooting

### Server not available

```bash
# Check all servers
python3 tts_generator.py --check

# Verify WireGuard connection
ping 10.200.0.12
```

### Audio quality issues

- Use `--engine openaudio` for best quality
- Use `--engine kokoro` for fastest generation
- For German text, use `--engine xtts --lang de`

### Long text problems

- Reduce `--chunk-size` if getting timeouts
- Use `--quiet` for large batch processing

## Integration with n8n

See `docs/n8n-podcast-prompt.md` for automated podcast generation workflows.

## License

MIT
