#!/usr/bin/env python3
"""
Simple test script for the Mistral OpenAI-Compatible API.
"""
import requests
import json
import time
import sys


def test_health():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_non_streaming_chat():
    """Test non-streaming chat completion."""
    print("\n💬 Testing non-streaming chat completion...")
    
    payload = {
        "model": "mistral",
        "messages": [
            {"role": "user", "content": "Say hello in one sentence."}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ Non-streaming response: {content}")
            print(f"📊 Usage: {data['usage']}")
            return True
        else:
            print(f"❌ Non-streaming test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Non-streaming test error: {e}")
        return False


def test_streaming_chat():
    """Test streaming chat completion."""
    print("\n🌊 Testing streaming chat completion...")
    
    payload = {
        "model": "mistral",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5."}
        ],
        "max_tokens": 100,
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Streaming response:")
            content = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    token = delta['content']
                                    content += token
                                    print(token, end='', flush=True)
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n📝 Complete response: {content}")
            return True
        else:
            print(f"❌ Streaming test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming test error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Mistral OpenAI-Compatible API")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    for i in range(10):
        if test_health():
            break
        time.sleep(2)
    else:
        print("❌ Server not ready after 20 seconds")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    if test_non_streaming_chat():
        tests_passed += 1
    
    if test_streaming_chat():
        tests_passed += 1
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
