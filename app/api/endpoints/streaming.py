"""
OpenAI-compatible chat completions endpoint with streaming support.
"""
import json
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.services.mistral_service import MistralService
from app.core.dependencies import get_mistral_service
from app.models.streaming_models import (
    ChatMessage, 
    ChatRequest, 
    ChatResponse, 
    ChatResponseChoice,
    StreamResponse,
    StreamResponseChoice,
    StreamDelta,
    UsageStats,
    ErrorResponse,
    ErrorDetail
)

router = APIRouter()

@router.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    mistral_service: MistralService = Depends(get_mistral_service)
):
    """OpenAI-compatible chat completions endpoint with streaming support."""
    try:
        if request.stream:
            return await _stream_chat_completions(request, mistral_service)
        else:
            return await _non_stream_chat_completions(request, mistral_service)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "api_error",
                    "code": "internal_error"
                }
            }
        )

async def _stream_chat_completions(request: ChatRequest, mistral_service: MistralService):
    """Stream chat completions with token-by-token streaming."""
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            completion_id = f"chatcmpl-{uuid.uuid4().hex}"
            created_time = int(time.time())
            
            # Send initial chunk with role
            initial_response = StreamResponse(
                id=completion_id,
                created=created_time,
                model=request.model or "mistral",
                choices=[
                    StreamResponseChoice(
                        index=0,
                        delta=StreamDelta(role="assistant")
                    )
                ]
            )
            yield f"data: {initial_response.model_dump_json()}\n\n"
            
            # Stream content tokens
            async for token in mistral_service.stream_chat(
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ):
                # Skip None or empty tokens
                if token is None or token == "":
                    continue
                    
                stream_response = StreamResponse(
                    id=completion_id,
                    created=created_time,
                    model=request.model or "mistral",
                    choices=[
                        StreamResponseChoice(
                            index=0,
                            delta=StreamDelta(content=str(token))
                        )
                    ]
                )
                yield f"data: {stream_response.model_dump_json()}\n\n"
            
            # Send final chunk with finish reason
            final_response = StreamResponse(
                id=completion_id,
                created=created_time,
                model=request.model or "mistral",
                choices=[
                    StreamResponseChoice(
                        index=0,
                        delta=StreamDelta(),
                        finish_reason="stop"
                    )
                ]
            )
            yield f"data: {final_response.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_response = ErrorResponse(
                error=ErrorDetail(
                    message=str(e),
                    type="api_error",
                    code="stream_error"
                )
            )
            yield f"data: {error_response.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

async def _non_stream_chat_completions(request: ChatRequest, mistral_service: MistralService):
    """Non-streaming chat completions."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created_time = int(time.time())
    
    # Get complete response by collecting all streaming tokens
    full_response = ""
    async for token in mistral_service.stream_chat(
        messages=request.messages,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    ):
        if token is not None:
            full_response += str(token)
    
    # Calculate approximate token counts (simple word-based estimation)
    prompt_tokens = sum(len(msg.content.split()) for msg in request.messages)
    completion_tokens = len(full_response.split())
    
    response = ChatResponse(
        id=completion_id,
        created=created_time,
        model=request.model or "mistral",
        choices=[
            ChatResponseChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=full_response.strip()
                ),
                finish_reason="stop"
            )
        ],
        usage=UsageStats(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
    )
    
    return response

@router.options("/chat/completions")
async def options_chat_completions():
    """Handle OPTIONS request for CORS preflight."""
    return {"status": "ok"}