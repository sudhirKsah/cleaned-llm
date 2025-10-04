"""
Mistral model service for handling chat completions and streaming.
"""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, AsyncGenerator, Optional

from app.models.streaming_models import ChatMessage


class MistralService:
    """Service for managing Mistral model inference."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.tokenizer = None
        self.loaded = False
        self.model_type = "mock"
        self.model_path = model_path or "/teamspace/studios/this_studio/Mentay-Complete-Model-v1/checkpoints/checkpoint_000100/consolidated"
        self._thread_pool = ThreadPoolExecutor(max_workers=1)
    
    async def load_model_async(self) -> None:
        """Load the model asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._thread_pool, self._load_model)
    
    def _load_model(self) -> None:
        """Load the Mistral model synchronously."""
        try:
            if not os.path.exists(self.model_path):
                print(f"Model path does not exist: {self.model_path}")
                print("Falling back to mock mode")
                self.model_type = "mock"
                self.loaded = True
                return
            
            print(f"Loading Mistral model from {self.model_path}")
            
            from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
            from mistral_inference.transformer import Transformer
            
            tokenizer_path = f"{self.model_path}/tokenizer.model.v3"
            
            if not os.path.exists(tokenizer_path):
                raise FileNotFoundError(f"Tokenizer not found at {tokenizer_path}")
            
            self.tokenizer = MistralTokenizer.from_file(tokenizer_path)
            self.model = Transformer.from_folder(self.model_path)
            
            self.model_type = "mistral"
            self.loaded = True
            print("✓ Mistral model loaded successfully!")
            
        except Exception as e:
            print(f"✗ Model loading failed: {e}")
            print("Falling back to mock mode")
            self.model_type = "mock"
            self.loaded = True
    
    async def stream_chat(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int = 1000, 
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens."""
        if not self.loaded:
            raise RuntimeError("Model not loaded")
            
        if self.model_type == "mock":
            async for token in self._stream_chat_mock(messages, max_tokens, temperature):
                yield token
        else:
            async for token in self._stream_chat_real(messages, max_tokens, temperature):
                yield token
    
    async def _stream_chat_real(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int, 
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """Stream using real Mistral model."""
        try:
            from mistral_common.protocol.instruct.messages import UserMessage, AssistantMessage
            from mistral_common.protocol.instruct.request import ChatCompletionRequest as MistralCompletionRequest
            from mistral_inference.generate import generate
            
            # Convert messages to Mistral format
            mistral_messages = []
            for msg in messages:
                if msg.role == "user":
                    mistral_messages.append(UserMessage(content=msg.content))
                elif msg.role == "assistant":
                    mistral_messages.append(AssistantMessage(content=msg.content))
                # Skip system messages for now as they need special handling
            
            # Create request and encode
            completion_request = MistralCompletionRequest(messages=mistral_messages)
            tokens = self.tokenizer.encode_chat_completion(completion_request).tokens
            
            # Generate completion
            out_tokens, _ = generate(
                [tokens], 
                self.model, 
                max_tokens=max_tokens, 
                temperature=temperature,
                eos_id=self.tokenizer.instruct_tokenizer.tokenizer.eos_id
            )
            
            # Decode and stream response word by word
            full_response = self.tokenizer.instruct_tokenizer.tokenizer.decode(out_tokens[0])
            
            words = full_response.split()
            for i, word in enumerate(words):
                # Add space after word except for the last one
                token = word + (" " if i < len(words) - 1 else "")
                yield token
                await asyncio.sleep(0.05)  # Adjust streaming speed
                
        except Exception as e:
            print(f"Error in Mistral model generation: {e}")
            # Fallback to mock response
            async for token in self._stream_chat_mock(messages, max_tokens, temperature):
                yield token
    
    async def _stream_chat_mock(
        self, 
        messages: List[ChatMessage], 
        max_tokens: int, 
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """Mock streaming response for testing."""
        user_message = next((msg.content for msg in reversed(messages) if msg.role == "user"), "Hello")
        
        # Generate a more realistic mock response
        mock_responses = [
            f"I understand you're asking about: {user_message[:50]}...",
            "This is a mock response from the Mistral service.",
            "The actual model is not loaded, so this is a placeholder response.",
            "In production, this would be replaced by the real Mistral model output."
        ]
        
        response = " ".join(mock_responses)
        words = response.split()
        
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield token
            await asyncio.sleep(0.08)  # Slower for mock to simulate processing
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=False)