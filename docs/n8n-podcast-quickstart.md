# AI News Podcast Generator - Quick Start

## Sofort-Test (ohne E-Mail)

Kopiere diesen Prompt in Claude Code mit n8n-mcp:

---

Erstelle einen n8n Workflow "AI News Podcast Generator" mit diesen Nodes:

### Node 1: Manual Trigger
- Typ: manualTrigger
- Zum manuellen Testen

### Node 2: Set Test Content
- Typ: set
- Setze Variable "sections" als Array:

```json
[
  {
    "title": "Intro",
    "text": "Willkommen zum AI-News Podcast vom 28. Dezember 2025. Heute berichten wir über die wichtigsten Entwicklungen im Bereich Künstliche Intelligenz."
  },
  {
    "title": "Thema 1",
    "text": "Die rasante Entwicklung der Künstlichen Intelligenz führt zu einer Flut synthetischer Inhalte wie Bilder, Videos und Texte, die die Grenzen zwischen Realität und Fiktion zunehmend verwischen. Dies untergräbt das Vertrauen in digitale Medien grundlegend."
  },
  {
    "title": "Thema 2",  
    "text": "Der jährliche Kongress des Chaos Computer Clubs startet in Hamburg mit 16.000 Teilnehmern und beleuchtet kritisch Themen wie die Machtkonzentration bei KI-Unternehmen und die EU KI-Verordnung."
  },
  {
    "title": "Thema 3",
    "text": "Trotz der Unterstützung durch Künstliche Intelligenz bleibt das menschliche Arbeitsgedächtnis unersetzlich, da es kognitive Prozesse wie Lernen und Problemlösen ermöglicht."
  },
  {
    "title": "Outro",
    "text": "Das war der AI-News Podcast für heute. Vielen Dank fürs Zuhören und bis zum nächsten Mal."
  }
]
```

### Node 3: Split In Batches
- Typ: splitInBatches
- Batch Size: 1
- Input: sections Array

### Node 4: HTTP Request (TTS)
- Typ: httpRequest
- Method: POST
- URL: http://10.200.0.12:8766/tts
- Body (JSON):
```json
{
  "text": "{{ $json.text }}",
  "language": "de"
}
```
- Response Format: File
- Output Property Name: audio

### Node 5: Write Binary File
- Typ: writeBinaryFile
- File Name: /tmp/podcast/section_{{ $runIndex }}.wav
- Property Name: audio

### Node 6: Merge
- Typ: merge
- Mode: Append
- Warte auf alle Batches

### Node 7: Execute Command (Create file list)
- Typ: executeCommand
- Command:
```bash
mkdir -p /tmp/podcast/output && cd /tmp/podcast && ls -1 section_*.wav | sort -V | while read f; do echo "file '$f'"; done > files.txt
```

### Node 8: Execute Command (FFmpeg merge)
- Typ: executeCommand
- Command:
```bash
cd /tmp/podcast && ffmpeg -y -f concat -safe 0 -i files.txt -acodec libmp3lame -b:a 192k output/ai-news-podcast.mp3
```

### Node 9: Read Binary File
- Typ: readBinaryFile
- File Path: /tmp/podcast/output/ai-news-podcast.mp3

### Verbindungen:
Manual Trigger -> Set Content -> Split In Batches -> HTTP Request -> Write Binary -> (loop back to Split) -> Merge -> Execute (list) -> Execute (ffmpeg) -> Read Binary

---

## TTS Server Info

- XTTS (Deutsch): http://10.200.0.12:8766/tts
- OpenAudio (Beste Qualitaet): http://10.200.0.12:8770/v1/tts

Payload XTTS:
```json
{"text": "...", "language": "de"}
```

Payload OpenAudio:
```json
{"text": "...", "format": "wav", "temperature": 0.3}
```

---

## Nach dem Test

Wenn der Workflow funktioniert, erweitere mit:
1. Gmail/IMAP Trigger statt Manual
2. Playwright Node zum Scrapen des Grok-Links
3. Code Node zum Parsen der "Bildungshohe Version" Texte
