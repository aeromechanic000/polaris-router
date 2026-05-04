# Polaris

A lightweight LLM API router that exposes an OpenAI-compatible API and forwards requests to upstream LLM providers.

## Quick start

```bash
# Install dependencies
uv sync

# Set required API keys
export KIMI_API_KEY=your-key-here

# Start the server
uv run python main.py
```

The API listens on port 11565. Verify it's running:

```bash
curl http://localhost:11565/health
# {"status":"ok"}
```

## Adding models

Models are defined in `config.json`. Each model has a strategy and one or more endpoints:

```json
{
  "models": {
    "my-model": {
      "strategy": "round-robin",
      "endpoints": [
        {
          "base_url": "https://api.openai.com/v1",
          "model": "gpt-4o",
          "api_key": "sk-xxx"
        }
      ]
    }
  }
}
```

### Multiple endpoints (load balancing)

Add more endpoints to the list. The `strategy` field controls how they're picked:

- `round-robin` — cycle through endpoints in order (default)
- `random` — pick a random endpoint each time
- `failover` — always use the first endpoint, only fall back on failure

```json
{
  "models": {
    "gpt-4o": {
      "strategy": "round-robin",
      "endpoints": [
        { "base_url": "https://api.openai.com/v1", "model": "gpt-4o", "api_key": "sk-aaa" },
        { "base_url": "https://proxy.example.com/v1", "model": "gpt-4o", "api_key": "sk-bbb" }
      ]
    }
  }
}
```

### Using environment variables for API keys

Use `env:VAR_NAME` as the `api_key` value to read from an environment variable at startup:

```json
{
  "models": {
    "kimi": {
      "strategy": "round-robin",
      "endpoints": [
        {
          "base_url": "https://api.moonshot.cn/v1",
          "model": "moonshot-v1-8k",
          "api_key": "env:KIMI_API_KEY"
        }
      ]
    }
  }
}
```

## API usage

All endpoints are OpenAI-compatible. Call them as you would the OpenAI API:

```bash
# Chat completion
curl http://localhost:11565/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "kimi", "messages": [{"role": "user", "content": "Hello"}]}'

# List available models
curl http://localhost:11565/v1/models

# Streaming
curl http://localhost:11565/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "kimi", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```
