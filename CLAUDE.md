# CLAUDE.md

## Project overview

Polaris is a Python LLM API router (like litellm) that exposes an OpenAI-compatible API and forwards requests to upstream LLM providers (OpenAI, Anthropic, DeepSeek, etc.).

## Tech stack

- Python 3.12+, managed with **uv**
- **FastAPI** for the web server
- **httpx** for async HTTP client (supports streaming)
- **pytest** for testing

## Project structure

```
src/polaris/        - application code
  main.py           - FastAPI app entrypoint
  config.py         - config loading & validation
  router.py         - endpoint selection strategies (round-robin, etc.)
  models.py         - Pydantic request/response models
  providers/        - provider-specific translation layers
tests/              - test suite
config.json         - runtime configuration (models, endpoints)
```

## Key conventions

- The API is **OpenAI-compatible**: `/v1/chat/completions` is the main endpoint.
- Config is loaded from `config.json` at startup.
- API keys in config support `env:VAR_NAME` syntax to read from environment variables.
- Provider translation (e.g. Anthropic format) lives in `src/polaris/providers/`.
- Each logical model maps to one or more backend endpoints. Selection strategy defaults to round-robin.
- Streaming (`stream: true`) is supported — upstream SSE chunks are normalized to OpenAI format.
- Extra request parameters (temperature, max_tokens, etc.) are passed through to upstream providers as-is.
- Fallback: if one endpoint fails, the next is tried. All failures return 502.

## Commands

```bash
uv run fastapi dev src/polaris/main.py   # run dev server
uv run pytest                            # run tests
```
