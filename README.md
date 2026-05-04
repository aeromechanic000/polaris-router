# Polaris

A lightweight LLM API router that exposes an Anthropic-compatible API and forwards requests to upstream LLM providers. Designed for use with Claude Code.

## Quick start

```bash
# Install dependencies
uv sync

# Set required API keys
export OPENROUTER_API_KEY=your-key-here

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
          "base_url": "https://api.anthropic.com/v1",
          "model": "claude-sonnet-4-20250514",
          "api_key": "sk-ant-xxx"
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
    "code": {
      "strategy": "round-robin",
      "endpoints": [
        { "base_url": "https://api.anthropic.com/v1", "model": "claude-sonnet-4-20250514", "api_key": "sk-ant-aaa" },
        { "base_url": "https://provider.example.com/v1", "model": "claude-sonnet-4-20250514", "api_key": "sk-ant-bbb" }
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
    "code": {
      "strategy": "round-robin",
      "endpoints": [
        {
          "base_url": "https://api.anthropic.com/v1",
          "model": "claude-sonnet-4-20250514",
          "api_key": "env:ANTHROPIC_API_KEY"
        }
      ]
    }
  }
}
```

## Using with Claude Code

Polaris exposes an Anthropic-compatible Messages API, so Claude Code can connect to it by setting the Anthropic base URL.

### Option 1: System-wide environment variables

Set these in your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export ANTHROPIC_BASE_URL=http://localhost:11565
export ANTHROPIC_API_KEY=any-value     # Polaris doesn't require auth; Claude Code requires a non-empty value
```

Then launch Claude Code normally:

```bash
claude
```

### Option 2: Project-level settings

In your project's `.claude/settings.json` or the global `~/.claude/settings.json`, set the environment variables:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:11565",
    "ANTHROPIC_API_KEY": "any-value"
  }
}
```

### Option 3: Per-session

Prefix the Claude Code command:

```bash
ANTHROPIC_BASE_URL=http://localhost:11565 ANTHROPIC_API_KEY=any-value claude
```

## API usage

All endpoints follow the Anthropic Messages API format:

```bash
# Create a message
curl http://localhost:11565/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: any-value" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "code",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# List available models
curl http://localhost:11565/v1/models

# Streaming
curl http://localhost:11565/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: any-value" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "code",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```
