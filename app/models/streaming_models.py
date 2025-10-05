"""
OpenAI-compatible data models for chat completions and streaming.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal


class ChatMessage(BaseModel):
    """A chat message in the conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: Optional[str] = "mistral"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None


class UsageStats(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponseChoice(BaseModel):
    """A choice in a non-streaming chat response."""
    index: int
    message: ChatMessage
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = None


class ChatResponse(BaseModel):
    """OpenAI-compatible non-streaming chat response."""
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatResponseChoice]
    usage: UsageStats


class StreamDelta(BaseModel):
    """Delta content in streaming response."""
    role: Optional[str] = None
    content: Optional[str] = None


class StreamResponseChoice(BaseModel):
    """A choice in a streaming chat response."""
    index: int
    delta: StreamDelta
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = None


class StreamResponse(BaseModel):
    """OpenAI-compatible streaming chat response."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamResponseChoice]


class ErrorDetail(BaseModel):
    """Error detail structure."""
    message: str
    type: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response structure."""
    error: ErrorDetail