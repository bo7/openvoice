# Ollama LLM Service Guide

This guide explains how to use the Ollama LLM service available on the internal WireGuard network.

## Prerequisites

- Connected to WireGuard VPN network (10.200.0.0/24)
- Network access to mac1 (10.200.0.11)

## Server Information

| Property | Value |
|----------|-------|
| Host | mac1 / 10.200.0.11 |
| Port | 11434 |
| Base URL | http://10.200.0.11:11434 |
| Hardware | Mac Studio M3 Ultra, 512GB RAM |

## Available Models

| Model | Parameters | Use Case |
|-------|------------|----------|
| deepseek-r1:32b | 32B | Reasoning, analysis, complex tasks |
| qwen3-coder:30b | 30B | Code generation, programming |
| llama3.2-vision | - | Image understanding, visual tasks |
| nomic-embed-text | - | Text embeddings |
| bge-m3 | - | Multilingual embeddings |
| bge-large | - | Large text embeddings |

## API Reference

### List Available Models

```bash
curl http://10.200.0.11:11434/api/tags
```

Response:
```json
{
  "models": [
    {"name": "deepseek-r1:32b", ...},
    {"name": "qwen3-coder:30b", ...}
  ]
}
```

### Generate Completion

```bash
curl -X POST http://10.200.0.11:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:32b",
    "prompt": "Explain quantum computing in simple terms",
    "stream": false
  }'
```

Response:
```json
{
  "model": "deepseek-r1:32b",
  "response": "Quantum computing is...",
  "done": true
}
```

### Streaming Completion

```bash
curl -X POST http://10.200.0.11:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:32b",
    "prompt": "Write a short poem",
    "stream": true
  }'
```

Returns newline-delimited JSON:
```json
{"model":"deepseek-r1:32b","response":"The ","done":false}
{"model":"deepseek-r1:32b","response":"sun ","done":false}
...
{"model":"deepseek-r1:32b","response":"","done":true}
```

### Chat Completion

```bash
curl -X POST http://10.200.0.11:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:32b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
  }'
```

Response:
```json
{
  "model": "deepseek-r1:32b",
  "message": {
    "role": "assistant",
    "content": "The capital of France is Paris."
  },
  "done": true
}
```

### Generate Embeddings

```bash
curl -X POST http://10.200.0.11:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "prompt": "Text to embed"
  }'
```

Response:
```json
{
  "embedding": [0.123, -0.456, 0.789, ...]
}
```

### Vision Model (Image Analysis)

```bash
# Base64 encode an image
IMAGE_B64=$(base64 -i image.jpg)

curl -X POST http://10.200.0.11:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2-vision",
    "prompt": "Describe this image",
    "images": ["'$IMAGE_B64'"],
    "stream": false
  }'
```

## Python Examples

### Basic Generation

```python
import requests

OLLAMA_URL = "http://10.200.0.11:11434"

def generate(prompt, model="deepseek-r1:32b"):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Usage
result = generate("Explain machine learning")
print(result)
```

### Streaming Generation

```python
import requests

def stream_generate(prompt, model="deepseek-r1:32b"):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            print(data.get("response", ""), end="", flush=True)
            if data.get("done"):
                break

# Usage
stream_generate("Write a haiku about coding")
```

### Chat with History

```python
import requests

class OllamaChat:
    def __init__(self, model="deepseek-r1:32b", system_prompt=None):
        self.model = model
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
    
    def chat(self, user_message):
        self.messages.append({"role": "user", "content": user_message})
        
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": self.model,
                "messages": self.messages,
                "stream": False
            }
        )
        
        assistant_message = response.json()["message"]["content"]
        self.messages.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message

# Usage
chat = OllamaChat(system_prompt="You are a Python expert.")
print(chat.chat("How do I read a CSV file?"))
print(chat.chat("How do I filter rows?"))
```

### Embeddings for Similarity Search

```python
import requests
import numpy as np

def get_embedding(text, model="nomic-embed-text"):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": model, "prompt": text}
    )
    return np.array(response.json()["embedding"])

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Usage
texts = [
    "Machine learning is a subset of AI",
    "Deep learning uses neural networks",
    "The weather is nice today"
]

embeddings = [get_embedding(t) for t in texts]

query = get_embedding("Tell me about artificial intelligence")
similarities = [cosine_similarity(query, e) for e in embeddings]

for text, sim in sorted(zip(texts, similarities), key=lambda x: -x[1]):
    print(f"{sim:.3f}: {text}")
```

### Code Generation with Qwen

```python
def generate_code(task, language="python"):
    prompt = f"""Write {language} code for the following task:
{task}

Provide only the code, no explanations."""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "qwen3-coder:30b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Usage
code = generate_code("a function that finds prime numbers up to n")
print(code)
```

## JavaScript/Node.js Examples

### Basic Generation

```javascript
const OLLAMA_URL = "http://10.200.0.11:11434";

async function generate(prompt, model = "deepseek-r1:32b") {
  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      prompt,
      stream: false
    })
  });
  
  const data = await response.json();
  return data.response;
}

// Usage
const result = await generate("What is TypeScript?");
console.log(result);
```

### Streaming with Async Iterator

```javascript
async function* streamGenerate(prompt, model = "deepseek-r1:32b") {
  const response = await fetch(`${OLLAMA_URL}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      prompt,
      stream: true
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const lines = decoder.decode(value).split("\n");
    for (const line of lines) {
      if (line.trim()) {
        const data = JSON.parse(line);
        yield data.response;
        if (data.done) return;
      }
    }
  }
}

// Usage
for await (const token of streamGenerate("Explain React hooks")) {
  process.stdout.write(token);
}
```

## Model Selection Guide

| Task | Recommended Model | Why |
|------|-------------------|-----|
| General Q&A | deepseek-r1:32b | Best reasoning |
| Code generation | qwen3-coder:30b | Optimized for code |
| Code review | qwen3-coder:30b | Understands patterns |
| Image analysis | llama3.2-vision | Vision capability |
| Text search | nomic-embed-text | Fast embeddings |
| Multilingual | bge-m3 | Multi-language support |

## Performance Tips

1. Use streaming for long responses to get first tokens faster
2. Keep context length reasonable (under 4096 tokens for best speed)
3. Use embeddings model for similarity search, not generation models
4. Cache embeddings for repeated queries
5. Use appropriate model for task (coder for code, vision for images)

## Troubleshooting

### Connection Refused
- Check WireGuard connection: `wg show`
- Ping the server: `ping 10.200.0.11`
- Verify Ollama is running: `curl http://10.200.0.11:11434/api/tags`

### Slow Responses
- Large models need time to load on first request
- Subsequent requests are faster (model stays in memory)
- Consider using smaller models for quick tasks

### Out of Memory
- Only one large model can be loaded at a time
- Switch models to unload previous one
- Use embedding models for search instead of generation

## Network Configuration

If connecting from outside the local network:

```bash
# SSH tunnel (if WireGuard not available)
ssh -L 11434:localhost:11434 user@gateway-server

# Then access via localhost
curl http://localhost:11434/api/tags
```

## Related Resources

- Ollama Documentation: https://ollama.ai/docs
- Model Library: https://ollama.ai/library
- TTS Guide: [tts-guide.md](tts-guide.md)
