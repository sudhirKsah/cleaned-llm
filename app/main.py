"""
OpenAI-compatible API server for Mistral models with streaming support.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import streaming
from app.services.mistral_service import MistralService
from app.core.dependencies import set_mistral_service
from app.core.security import security_manager
from app.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    mistral_service = MistralService(model_path=settings.model_path)
    print("Starting model loading...")
    await mistral_service.load_model_async()
    print(f"Model loading completed. Type: {mistral_service.model_type}, Loaded: {mistral_service.loaded}")
    set_mistral_service(mistral_service)
    
    # Initialize security system
    print("Security framework initialized")
    security_manager.logger.log_security_event("SERVER_STARTUP", "system", "MentaY API server started with security enabled")
    
    yield
    
    # Shutdown
    print("Shutting down server...")
    security_manager.logger.log_security_event("SERVER_SHUTDOWN", "system", "MentaY API server shutting down")


app = FastAPI(
    title="Mistral OpenAI-Compatible API",
    description="Production-ready OpenAI-compatible API for Mistral models with streaming support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_server_error",
                "code": "internal_error"
            }
        }
    )

# Include routers with OpenAI-compatible paths
app.include_router(
    streaming.router,
    prefix="/v1",
    tags=["chat"]
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Mistral OpenAI-Compatible API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.core.dependencies import get_mistral_service
    
    try:
        service = get_mistral_service()
        return {
            "status": "healthy" if service.loaded else "degraded",
            "model_loaded": service.loaded,
            "model_type": service.model_type,
            "timestamp": int(time.time())
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time())
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.reload
    )