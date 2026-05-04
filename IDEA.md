
In this project named Polaris, I want to build a LLM API router in python, which running like litellm https://github.com/BerriAI/litellm, that provides an LLM calling API, and routes the request to the API to an actual LLM service API (e.g. Claude, GPT, or DeepSeek), and response with the LLM services return to the user. use uv to manage the python projets.

## Configuration

In configuration file `config.json`, user defines a model, and associated a list of actual LLM service endpoints to the model.

### Config structure

```json
{
  "models": {
    "gpt-4o": {
      "strategy": "round-robin",
      "endpoints": [
        {
          "base_url": "https://api.openai.com/v1",
          "model": "gpt-4o",
          "api_key": "sk-xxx"
        },
        {
          "base_url": "https://some-proxy.example.com/v1",
          "model": "gpt-4o",
          "api_key": "sk-yyy"
        }
      ]
    },
    "claude-sonnet": {
      "strategy": "round-robin",
      "endpoints": [
        {
          "base_url": "https://api.anthropic.com/v1",
          "model": "claude-sonnet-4-6",
          "api_key": "sk-ant-xxx"
        }
      ]
    }
  }
}
```

- Each logical model name (e.g. `gpt-4o`) maps to one or more backend endpoints.
- `strategy` controls how endpoints are selected when there are multiple. Default is `round-robin`. Other strategies to consider: `random`, `least-latency`, `failover`.

### API key resolution

The `api_key` field supports a special `env:VAR_NAME` syntax. When an api_key starts with `env:`, the value is read from the environment variable `VAR_NAME` at startup. This avoids putting secrets in the config file.

## API Interface

Polaris exposes an **OpenAI-compatible API** so that any existing tool or SDK that talks to OpenAI can point at Polaris without changes.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/completions` | Chat completion (main endpoint) |
| GET | `/v1/models` | List available models |
| GET | `/health` | Health check |

### Request format

Identical to OpenAI's chat completion request:

```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": false,
  "temperature": 0.7
}
```

- The `model` field is the logical model name defined in `config.json`.
- Extra parameters (temperature, max_tokens, etc.) are passed through to the upstream provider as-is.

## Workflow

1. User sends a LLM calling request to the Polaris API, with a specified model.
2. Polaris looks up the model in `config.json` and selects a backend endpoint using the configured strategy (round-robin by default).
3. Polaris translates the request if needed (e.g. OpenAI format to Anthropic format) and forwards it to the selected backend.
4. Polaris receives the response, normalizes it to OpenAI format, and returns it to the user.

## Streaming

- When `stream: true` is in the request, Polaris streams SSE chunks back to the client.
- Each chunk from the upstream provider is normalized to OpenAI SSE format before forwarding.
- This is critical for interactive chat use cases and must be supported from day one.

## Provider translation

Different LLM providers have different request/response formats:

| Provider | Request format | Notes |
|----------|---------------|-------|
| OpenAI / DeepSeek / most proxies | OpenAI-native | Pass through directly |
| Anthropic (Claude) | Anthropic format | Requires translation: `messages` structure differs, `system` is a top-level field, content blocks have a different shape |

Polaris should detect the provider from the `base_url` or an explicit `provider` field in the endpoint config, and apply the correct translation layer.

## Error handling and fallback

- If a backend endpoint returns an error (5xx, timeout, connection refused), Polaris should try the next endpoint in the list (if any), up to all endpoints once.
- If all endpoints fail, return a `502 Bad Gateway` with a JSON error body containing details.
- Timeouts: configurable per-endpoint, sensible default (e.g. 60s for non-streaming, 300s for streaming).

## Tech stack

- **Runtime:** Python 3.12+
- **Package manager:** uv
- **Web framework:** FastAPI (async, good SSE/streaming support, auto OpenAPI docs)
- **HTTP client:** httpx (async, supports streaming)
- **Testing:** pytest + httpx `AsyncClient` for integration tests

## Project structure

```
polaris-router/
  pyproject.toml
  config.json
  src/
    polaris/
      __init__.py
      main.py           # FastAPI app entrypoint
      config.py          # config loading & validation
      router.py          # endpoint selection strategies
      providers/
        __init__.py
        base.py          # base provider interface
        openai.py        # OpenAI-compatible provider (passthrough)
        anthropic.py     # Anthropic provider (translation layer)
      models.py          # Pydantic request/response models
  tests/
    test_router.py
    test_providers.py
```

## LLM service

Each LLM service endpoint config contains:
- `base_url` - the API base URL
- `model` - the actual model name at that provider
- `api_key` - authentication key for that provider
- `provider` (optional) - explicit provider type hint (`openai`, `anthropic`). If omitted, inferred from `base_url`.
- `timeout` (optional) - per-endpoint timeout override

## Future considerations (out of scope for v1)

- User authentication and token management
- Rate limiting per user / per model
- Usage tracking and cost estimation
- Admin API for adding/removing users and endpoints at runtime
- Hot-reload of config.json without restart
- Prometheus metrics endpoint
- Docker image for easy deployment
