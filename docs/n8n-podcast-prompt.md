# Claude Code Prompt: Automated AI News Podcast with n8n

## Projekt-Uebersicht

Baue einen automatisierten Workflow in n8n, der:
1. Taeglich um 9:00 Uhr eine E-Mail von Grok mit AI-News erhaelt
2. Den Link in der E-Mail oeffnet und den Content scraped
3. Die Texte durch unser TTS-System spricht
4. Die Audio-Dateien zu einem Podcast zusammenfuegt

## Verfuegbare Infrastruktur

### n8n MCP Server
- Server: n8n-mcp (connected)
- Kann Workflows erstellen und ausfuehren

### AI/LLM (Ollama auf mac1)
- Host: http://10.200.0.11:11434
- Modelle:
  - deepseek-r1:32b (Reasoning, Zusammenfassungen)
  - qwen3-coder:30b (Code-Generierung)
  - llama3.2-vision (falls Bilder relevant)

### TTS Server (mac2)
- Host: http://10.200.0.12
- Ports:
  - 8766: XTTS v2 (Deutsch, Voice Cloning)
  - 8767: Chatterbox (Expressiv, nur Englisch)
  - 8769: Kokoro (Schnell, nur Englisch)
  - 8770: OpenAudio S1 (Beste Qualitaet, Deutsch)

Fuer deutschen Podcast nutze:
- **XTTS v2** (Port 8766) - Gute deutsche Aussprache
- **OpenAudio S1** (Port 8770) - Beste Qualitaet, 14 Sprachen inkl. Deutsch

### Browser Automation
- Playwright MCP Server (connected)
- Puppeteer MCP Server (connected)

### Weitere Tools
- brave-search (connected)
- github (connected)
- filesystem (connected)

## Workflow-Architektur

```
[Schedule Trigger 9:00]
        |
        v
[Gmail Trigger] --> Filtere "Aktuelle KI-Nachrichten-Update"
        |
        v
[Extract Link from Email]
        |
        v
[Playwright/Puppeteer] --> Oeffne Link in authentifizierter Grok-Session
        |
        v
[Scrape Content] --> Extrahiere nur "Bildungshohe Version" Texte
        |
        v
[Split into Sections] --> Deutsche Themen + Internationale Themen
        |
        v
[Generate Intro with Ollama] --> "Willkommen zum AI-News Podcast vom [Datum]..."
        |
        v
[Loop: For Each Section]
        |
        +---> [HTTP Request to TTS] --> POST http://10.200.0.12:8770/v1/tts
        |           |
        |           v
        |     [Save Audio to /tmp/section_N.wav]
        |
        v
[Merge Audios with FFmpeg] --> ffmpeg -i "concat:intro.wav|section1.wav|..." output.mp3
        |
        v
[Save Final Podcast] --> /path/to/podcasts/ai-news-YYYY-MM-DD.mp3
        |
        v
[Optional: Send Notification/Upload]
```

## Detaillierte n8n Nodes

### 1. Schedule Trigger
```json
{
  "type": "n8n-nodes-base.scheduleTrigger",
  "parameters": {
    "rule": {
      "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
    }
  }
}
```

### 2. Gmail Trigger (Alternative: IMAP)
```json
{
  "type": "n8n-nodes-base.gmailTrigger",
  "parameters": {
    "filters": {
      "subject": "Aktuelle KI-Nachrichten-Update",
      "from": "grok@x.ai"
    }
  }
}
```

### 3. Extract Link (Code Node)
```javascript
// Code Node: Extract Grok Link
const emailBody = $input.first().json.body;
const linkMatch = emailBody.match(/https:\/\/[^\s"<>]+grok[^\s"<>]*/i);
return [{ json: { grokUrl: linkMatch ? linkMatch[0] : null } }];
```

### 4. Playwright Browser Automation
Da Grok-Session authentifiziert sein muss:

Option A: Persistente Browser-Session mit gespeicherten Cookies
Option B: Headless Browser mit vorher exportierten Cookies

```javascript
// Playwright Script
const { chromium } = require('playwright');

async function scrapeGrokContent(url) {
  const browser = await chromium.launchPersistentContext(
    '/path/to/chrome-profile',  // Profile mit Grok Login
    { headless: true }
  );
  
  const page = await browser.newPage();
  await page.goto(url);
  await page.waitForSelector('.message-content', { timeout: 30000 });
  
  const content = await page.evaluate(() => {
    const sections = [];
    document.querySelectorAll('.message-content').forEach(el => {
      sections.push(el.innerText);
    });
    return sections;
  });
  
  await browser.close();
  return content;
}
```

### 5. Parse Content (Code Node)
```javascript
// Extrahiere nur "Bildungshohe Version" Abschnitte
const rawContent = $input.first().json.content;

const sections = [];
const regex = /Bildungshohe Version[^:]*:\s*([\s\S]*?)(?=Schülerfreundliche Version|Thema \d|$)/gi;

let match;
while ((match = regex.exec(rawContent)) !== null) {
  sections.push({
    text: match[1].trim(),
    index: sections.length
  });
}

return sections.map(s => ({ json: s }));
```

### 6. Generate Intro with Ollama (HTTP Request)
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://10.200.0.11:11434/api/generate",
    "body": {
      "model": "deepseek-r1:32b",
      "prompt": "Schreibe eine kurze, professionelle Podcast-Intro fuer einen deutschen AI-News Podcast. Datum: {{ $now.format('DD. MMMM YYYY') }}. Halte es unter 50 Woertern. Nur der Intro-Text, keine Anweisungen.",
      "stream": false
    }
  }
}
```

### 7. TTS Generation (HTTP Request in Loop)
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://10.200.0.12:8770/v1/tts",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {"name": "text", "value": "={{ $json.text }}"},
        {"name": "format", "value": "wav"},
        {"name": "temperature", "value": "0.3"},
        {"name": "top_p", "value": "0.7"}
      ]
    },
    "options": {
      "response": {"response": {"responseFormat": "file"}}
    }
  }
}
```

Alternative mit XTTS fuer besseres Deutsch:
```json
{
  "url": "http://10.200.0.12:8766/tts",
  "body": {
    "text": "={{ $json.text }}",
    "language": "de"
  }
}
```

### 8. Save Audio Files (Write Binary File)
```json
{
  "type": "n8n-nodes-base.writeBinaryFile",
  "parameters": {
    "fileName": "/tmp/podcast/section_{{ $json.index }}.wav"
  }
}
```

### 9. Merge with FFmpeg (Execute Command)
```json
{
  "type": "n8n-nodes-base.executeCommand",
  "parameters": {
    "command": "cd /tmp/podcast && ffmpeg -y -i \"concat:$(ls -1 *.wav | sort -V | tr '\\n' '|' | sed 's/|$//')\" -acodec libmp3lame -b:a 192k /output/ai-news-$(date +%Y-%m-%d).mp3"
  }
}
```

Bessere FFmpeg Variante mit File List:
```bash
cd /tmp/podcast
ls -1 *.wav | sort -V > files.txt
sed -i "s/^/file '/; s/$/'/" files.txt
ffmpeg -y -f concat -safe 0 -i files.txt -acodec libmp3lame -b:a 192k /output/ai-news-$(date +%Y-%m-%d).mp3
```

## Sofort-Test mit vorhandenem Text

Fuer den ersten Test ohne E-Mail-Automation, nutze diesen statischen Content:

```javascript
// Static Test Data Node
const testContent = `
Thema 1: KI verursacht eine digitale Vertrauenskrise

Die rasante Entwicklung der Künstlichen Intelligenz führt zu einer Flut synthetischer Inhalte wie Bilder, Videos und Texte, die die Grenzen zwischen Realität und Fiktion zunehmend verwischen. Dies untergräbt das Vertrauen in digitale Medien grundlegend, da jede Information manipulierbar wird und Authentizität schwer überprüfbar ist.

Thema 2: Chaos Computer Club diskutiert KI und Sicherheitslücken

Der jährliche Kongress des Chaos Computer Clubs, Europas größtes Hacker-Treffen, startet in Hamburg mit 16.000 Teilnehmern und beleuchtet kritisch Themen wie die Machtkonzentration bei KI-Unternehmen, die EU-KI-Verordnung und den Einsatz von KI durch deutsche Behörden.

Thema 3: KI kann das Gedächtnis nicht ersetzen

Trotz der Unterstützung durch Künstliche Intelligenz wie ChatGPT bleibt das menschliche Arbeitsgedächtnis unersetzlich, da es kognitive Prozesse wie Lernen und Problemlösen ermöglicht.
`;

return [{ json: { content: testContent } }];
```

## Datei-Struktur

```
/home/sbo/podcasts/
  /tmp/                    # Temporaere WAV-Dateien
  /output/                 # Fertige MP3-Podcasts
  /logs/                   # Workflow-Logs
```

## Workflow als JSON Export

Erstelle den Workflow mit diesen Nodes:

1. **Manual Trigger** (fuer Tests)
2. **Set Node** (Static Test Content)
3. **Code Node** (Parse Sections)
4. **Split In Batches** (1 item at a time)
5. **HTTP Request** (TTS API Call)
6. **Write Binary File** (Save WAV)
7. **Merge Node** (Wait for all)
8. **Execute Command** (FFmpeg merge)
9. **Move Binary File** (Final output)

## TTS API Calls

### OpenAudio S1 (Beste Qualitaet, Deutsch)
```bash
curl -X POST http://10.200.0.12:8770/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Willkommen zum AI-News Podcast.",
    "format": "wav",
    "temperature": 0.3,
    "top_p": 0.7
  }' --output intro.wav
```

### XTTS v2 (Gutes Deutsch, Voice Cloning moeglich)
```bash
curl -X POST http://10.200.0.12:8766/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Willkommen zum AI-News Podcast.",
    "language": "de"
  }' --output intro.wav
```

## Erweiterungen (Phase 2)

1. **Voice Cloning**: Eigene Stimme fuer den Podcast
2. **Background Music**: Intro/Outro Musik mit FFmpeg mixen
3. **RSS Feed**: Automatisch Podcast-Feed generieren
4. **Transcription**: Whisper STT fuer Show Notes
5. **Upload**: Automatisch zu Podcast-Hosting hochladen

## Aufgabe fuer Claude Code

1. Erstelle einen n8n Workflow mit dem n8n-mcp Server
2. Starte mit dem statischen Test-Content
3. Implementiere TTS-Calls zu http://10.200.0.12:8770/v1/tts
4. Merge die Audio-Dateien mit FFmpeg
5. Speichere das Ergebnis als MP3

Nutze diese MCP Server:
- n8n-mcp: Workflow erstellen
- playwright: Browser Automation (spaeter fuer Grok)
- filesystem: Dateien verwalten

Teste zuerst mit dem statischen Content, dann erweitere auf E-Mail-Trigger.
