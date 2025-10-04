#!/bin/bash

# Mistral OpenAI-Compatible API Server Startup Script

set -e  # Exit on error

echo "🚀 Starting Mistral OpenAI-Compatible API Server..."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $(pwd)"

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Install requirements if needed
if [ "$1" = "--install" ]; then
    echo "📚 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install Mistral dependencies if available
    echo "🤖 Installing Mistral dependencies (optional)..."
    pip install mistral-inference mistral-common || echo "⚠️  Mistral dependencies not available, will use mock mode"
fi

# Health check function
check_health() {
    echo "🔍 Checking server health..."
    sleep 2
    curl -s http://localhost:${PORT:-8000}/health || echo "⚠️  Health check failed"
}

# Start the server
echo "🌐 Starting server..."
echo "📊 API available at: http://localhost:${PORT:-8000}"
echo "📚 Documentation at: http://localhost:${PORT:-8000}/docs"
echo "❤️  Health check at: http://localhost:${PORT:-8000}/health"
echo ""
echo "Press Ctrl+C to stop the server"

# Run health check in background
check_health &

# Start the server using the configuration
python -m app.main
