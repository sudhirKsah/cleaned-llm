# Mistral OpenAI-Compatible API Server

A production-ready OpenAI-compatible API server for Mistral models with streaming support.

## Features

- **OpenAI-Compatible API**: Drop-in replacement for OpenAI's chat completions API
- **Streaming Support**: Real-time token streaming for better user experience
- **Production Ready**: Clean, maintainable code with proper error handling
- **Configurable**: Environment-based configuration for different deployment scenarios
- **Mock Mode**: Fallback mode when model is not available

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd llm-stream
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Mistral dependencies (if using real model):
```bash
pip install mistral-common mistral-inference
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Server

```bash
# Development
python -m app.main

# Production with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## API Usage

### Chat Completions (Non-streaming)

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Chat Completions (Streaming)

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "max_tokens": 200,
    "temperature": 0.7,
    "stream": true
  }'
```

## Configuration

Environment variables can be set in `.env` file or as system environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `MODEL_PATH` | `/path/to/model` | Path to Mistral model |
| `MAX_TOKENS` | `4096` | Maximum tokens per request |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## Health Check

```bash
curl http://localhost:8000/health
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Model Support

The server supports:
- **Real Mistral Models**: When model files are available at the configured path
- **Mock Mode**: Automatic fallback when model is not available (useful for testing)

## Production Deployment

1. Set `RELOAD=false` in production
2. Configure appropriate `CORS_ORIGINS`
3. Use a reverse proxy (nginx) for SSL termination
4. Monitor logs and health endpoints
5. Consider using Docker for containerized deployment

## Docker Support

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY .env .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

[Add your license here]
