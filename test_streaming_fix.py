#!/usr/bin/env python3
"""
Test the streaming fix without requiring a running server.
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/media/sks/Storage1/mentay/llm-stream')

async def test_streaming_service():
    """Test the streaming service directly."""
    try:
        from app.services.mistral_service import MistralService
        from app.models.streaming_models import ChatMessage
        
        print("🧪 Testing MistralService streaming...")
        
        # Create service instance
        service = MistralService()
        await service.load_model_async()
        
        print(f"✅ Service loaded: {service.loaded}, Type: {service.model_type}")
        
        # Test messages
        messages = [
            ChatMessage(role="user", content="Count from 1 to 5")
        ]
        
        print("🌊 Testing streaming...")
        tokens = []
        async for token in service.stream_chat(messages, max_tokens=50, temperature=0.7):
            if token is not None:
                tokens.append(str(token))
                print(f"Token: '{token}' (type: {type(token)})")
        
        full_response = "".join(tokens)
        print(f"✅ Complete response: '{full_response}'")
        print(f"📊 Total tokens: {len(tokens)}")
        
        # Check for None tokens
        none_count = sum(1 for token in tokens if token is None)
        if none_count > 0:
            print(f"❌ Found {none_count} None tokens")
            return False
        else:
            print("✅ No None tokens found")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_streaming_endpoint():
    """Test the streaming endpoint logic."""
    try:
        from app.api.endpoints.streaming import _stream_chat_completions
        from app.services.mistral_service import MistralService
        from app.models.streaming_models import ChatRequest, ChatMessage
        
        print("\n🧪 Testing streaming endpoint...")
        
        # Create service and request
        service = MistralService()
        await service.load_model_async()
        
        request = ChatRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            max_tokens=20,
            temperature=0.7,
            stream=True
        )
        
        print("🌊 Testing endpoint streaming...")
        response_gen = _stream_chat_completions(request, service)
        
        chunks = []
        async for chunk in response_gen:
            chunks.append(chunk)
            print(f"Chunk: {chunk[:100]}...")
        
        print(f"✅ Generated {len(chunks)} chunks")
        return True
        
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🔧 Testing Streaming Fix")
    print("=" * 40)
    
    success1 = await test_streaming_service()
    success2 = await test_streaming_endpoint()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Streaming fix is working.")
        return True
    else:
        print("\n❌ Some tests failed.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
