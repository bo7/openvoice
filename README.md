# OpenVoice

Self-hosted Voice Cloning Server mit Web-Interface. Unterstuetzt zwei TTS-Engines:
- **XTTS v2** (Coqui) - Schnell, gute Qualitaet
- **Chatterbox** (Resemble AI) - MIT-Lizenz, Stimmvariationen

## Features

- Voice Cloning mit kurzen Audio-Samples (6-30 Sekunden)
- Web-Interface fuer einfache Bedienung
- REST API fuer Integration
- Chatterbox Stimmvariationen (Emotion, Tempo, Kreativitaet)
- 23 Sprachen unterstuetzt
- Optimiert fuer Apple Silicon (MPS) und CPU

## Architektur

```
┌─────────────────┐     ┌──────────────────┐
│   Flask Web UI  │────▶│  XTTS Server     │ :8766
│     :5050       │     │  (schnell)       │
│                 │────▶│                  │
│                 │     ├──────────────────┤
│                 │────▶│ Chatterbox Server│ :8767
│                 │     │ (MIT, Variationen)│
└─────────────────┘     └──────────────────┘
```

## Installation

### Voraussetzungen

- Python 3.11
- macOS 12+ (Apple Silicon) oder Linux mit CUDA
- ~10 GB Speicherplatz fuer Modelle

### 1. XTTS Server

```bash
# Verzeichnis erstellen
mkdir -p ~/xtts-server && cd ~/xtts-server

# Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install TTS fastapi uvicorn librosa soundfile python-multipart

# Server starten
python xtts_server.py
# Laeuft auf http://localhost:8766
```

### 2. Chatterbox Server

```bash
# Verzeichnis erstellen
mkdir -p ~/chatterbox-server && cd ~/chatterbox-server

# Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install chatterbox-tts fastapi uvicorn soundfile python-multipart

# Server starten
python chatterbox_server.py
# Laeuft auf http://localhost:8767
```

### 3. Flask Web-Interface

```bash
# Verzeichnis erstellen
mkdir -p ~/openvoice && cd ~/openvoice

# Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install flask requests

# Server URLs anpassen (falls noetig)
# In app.py: XTTS_URL und CHATTERBOX_URL

# Starten
python app.py
# Laeuft auf http://localhost:5050
```

## Verwendung

### Web-Interface

1. Oeffne http://localhost:5050
2. **Voice Clone**: Audio hochladen, Name vergeben, Engine waehlen
3. **Talk**: Text eingeben, Stimme und Engine waehlen, generieren

### Chatterbox Stimmvariationen

| Preset | Exaggeration | CFG Weight | Temperature | Effekt |
|--------|--------------|------------|-------------|--------|
| Neutral | 0.5 | 0.5 | 0.8 | Ausgeglichen |
| Ruhig | 0.2 | 0.7 | 0.5 | Langsam, monoton |
| Expressiv | 0.8 | 0.4 | 0.9 | Lebendig |
| Dramatisch | 1.2 | 0.3 | 0.9 | Uebertrieben |
| Monoton | 0.1 | 0.8 | 0.3 | Roboterhaft |
| Energisch | 1.0 | 0.5 | 1.0 | Schnell, variabel |

**Parameter:**
- **Exaggeration** (0-2): Emotionale Intensitaet
- **CFG Weight** (0-1): Wie streng die geklonte Stimme befolgt wird
- **Temperature** (0-1): Kreativitaet/Variation

### REST API

#### Health Check
```bash
# Beide Engines
curl http://localhost:5050/api/health

# Einzelne Engine
curl http://localhost:8766/health  # XTTS
curl http://localhost:8767/health  # Chatterbox
```

#### Voice Cloning
```bash
# XTTS
curl -X POST http://localhost:8766/clone \
  -F "audio=@sample.wav" \
  -F "name=meineStimme"

# Chatterbox
curl -X POST http://localhost:8767/clone \
  -F "audio=@sample.wav" \
  -F "name=meineStimme"
```

#### Text-to-Speech
```bash
# XTTS
curl -X POST http://localhost:8766/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hallo Welt", "voice": "meineStimme", "language": "de"}' \
  -o output.wav

# Chatterbox mit Stimmvariation
curl -X POST http://localhost:8767/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hallo Welt",
    "voice": "meineStimme",
    "language": "de",
    "exaggeration": 0.8,
    "cfg_weight": 0.4,
    "temperature": 0.9
  }' \
  -o output.wav
```

#### Stimmen auflisten
```bash
curl http://localhost:8766/voices  # XTTS
curl http://localhost:8767/voices  # Chatterbox
```

## Systemd Services (Linux)

### XTTS Service

```ini
# /etc/systemd/system/xtts.service
[Unit]
Description=XTTS Voice Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/xtts-server
Environment="PATH=/home/your_user/xtts-server/.venv/bin"
ExecStart=/home/your_user/xtts-server/.venv/bin/python xtts_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Chatterbox Service

```ini
# /etc/systemd/system/chatterbox.service
[Unit]
Description=Chatterbox Voice Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/chatterbox-server
Environment="PATH=/home/your_user/chatterbox-server/.venv/bin"
ExecStart=/home/your_user/chatterbox-server/.venv/bin/python chatterbox_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## macOS LaunchAgent

```xml
<!-- ~/Library/LaunchAgents/com.openvoice.xtts.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openvoice.xtts</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOU/xtts-server/.venv/bin/python</string>
        <string>/Users/YOU/xtts-server/xtts_server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOU/xtts-server</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

## Performance

| Engine | Device | Kurzer Text | Langer Text |
|--------|--------|-------------|-------------|
| XTTS | CPU (16 threads) | ~4s | ~15s |
| Chatterbox | CPU | ~49s | ~60s |
| Chatterbox | MPS (Apple Silicon) | ~18-28s | ~30s |

## Vergleich der Engines

| Eigenschaft | XTTS | Chatterbox |
|-------------|------|------------|
| Lizenz | Coqui Public (non-commercial) | MIT (commercial OK) |
| Geschwindigkeit | Schneller | Langsamer |
| Qualitaet | Sehr gut | Sehr gut, natuerlicher |
| Voice Sample | 10-30s empfohlen | 6s+ reicht |
| Stimmvariationen | Nein | Ja (Emotion, Tempo) |
| Sprachen | 16 | 23 |
| Paralinguistik | Nein | Ja ([laugh], [cough]) |
| MPS Support | Nein (Conv1d Bug) | Ja (mit Workarounds) |

## Sprachen

**XTTS:** en, de, es, fr, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko

**Chatterbox:** ar, da, de, el, en, es, fi, fr, he, hi, it, ja, ko, ms, nl, no, pl, pt, ru, sv, sw, tr, zh

## Tipps

### Voice Cloning
- Verwende saubere Audio-Aufnahmen ohne Hintergrundgeraeusche
- 10-30 Sekunden fuer beste Ergebnisse
- Gleichmaessige Sprechgeschwindigkeit
- Keine Musik oder andere Stimmen

### Chatterbox Paralinguistik (nur Turbo-Modell)
```
"Das ist ja [laugh] wirklich lustig!"
"Hmm [cough] entschuldigung..."
"Wow [chuckle] das haette ich nicht erwartet."
```

## Troubleshooting

### MPS Fehler (Apple Silicon)
```
Output channels > 65536 not supported at the MPS device
```
Loesung: XTTS laeuft nur auf CPU. Chatterbox funktioniert mit MPS.

### Modell-Download haengt
Die Modelle werden beim ersten Start von HuggingFace heruntergeladen:
- XTTS: ~1.9 GB
- Chatterbox: ~3 GB

### Port bereits belegt
```bash
lsof -i :5050  # Prozess finden
kill -9 PID    # Prozess beenden
```

## Lizenz

- **XTTS v2**: Coqui Public Model License (non-commercial)
- **Chatterbox**: MIT License
- **Dieses Projekt**: MIT License

## Credits

- [Coqui TTS](https://github.com/coqui-ai/TTS) - XTTS v2 Model
- [Resemble AI](https://github.com/resemble-ai/chatterbox) - Chatterbox TTS
