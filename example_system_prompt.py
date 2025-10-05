#!/usr/bin/env python3
"""
Example of how to use system prompts with the Mistral API.
"""
import requests
import json

# Example 1: Basic system prompt
def test_basic_system_prompt():
    """Test with a basic system prompt."""
    payload = {
        "model": "mistral",
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful assistant that always responds in a friendly and concise manner."
            },
            {
                "role": "user", 
                "content": "What is the capital of France?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "stream": False
    }
    
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Basic System Prompt Response:")
        print(f"   {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ Request failed: {response.status_code}")

# Example 2: Role-based system prompt
def test_role_system_prompt():
    """Test with a role-based system prompt."""
    payload = {
        "model": "mistral",
        "messages": [
            {
                "role": "system", 
                "content": "You are a professional software engineer. Provide technical answers with code examples when appropriate."
            },
            {
                "role": "user", 
                "content": "How do I handle errors in Python?"
            }
        ],
        "max_tokens": 200,
        "temperature": 0.7,
        "stream": False
    }
    
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Role-based System Prompt Response:")
        print(f"   {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ Request failed: {response.status_code}")

# Example 3: Streaming with system prompt
def test_streaming_system_prompt():
    """Test streaming with system prompt."""
    payload = {
        "model": "mistral",
        "messages": [
            {
                "role": "system", 
                "content": "You are a creative storyteller. Tell engaging short stories."
            },
            {
                "role": "user", 
                "content": "Tell me a short story about a robot."
            }
        ],
        "max_tokens": 150,
        "temperature": 0.8,
        "stream": True
    }
    
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json=payload,
        stream=True
    )
    
    if response.status_code == 200:
        print("✅ Streaming System Prompt Response:")
        print("   ", end="")
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta and delta['content']:
                                print(delta['content'], end='', flush=True)
                    except json.JSONDecodeError:
                        continue
        print()  # New line after streaming
    else:
        print(f"❌ Streaming request failed: {response.status_code}")

if __name__ == "__main__":
    print("🧪 System Prompt Examples")
    print("=" * 40)
    print("Note: Make sure your server is running first!")
    print()
    
    test_basic_system_prompt()
    print()
    test_role_system_prompt()
    print()
    test_streaming_system_prompt()
