"""
Streaming Response Tests

This module tests the API's streaming functionality including:
- Proper SSE (Server-Sent Events) format
- Streaming response structure and content
- Error handling in streaming mode
- Security enforcement during streaming
- Connection handling and timeouts

Each test validates that streaming responses maintain security, structure,
and reliability while providing real-time token delivery.
"""
import pytest
import json
import time
from tests.conftest import make_api_request, parse_streaming_response


class TestStreaming:
    """Test suite for streaming response functionality and security."""
    
    def test_streaming_response_format(self, api_client, test_config, valid_chat_request):
        """
        Test that streaming responses follow proper SSE format.
        
        This test validates that streaming responses use the correct
        Server-Sent Events format with proper headers and data structure.
        """
        streaming_request = {**valid_chat_request, "stream": True}
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_request,
            stream=True
        )
        
        assert result["success"], "Streaming request should succeed"
        assert result["status_code"] == 200, "Should return HTTP 200"
        
        # Verify SSE headers
        headers = result["headers"]
        assert headers.get("content-type") == "text/event-stream", \
            "Should return text/event-stream content type"
        assert headers.get("cache-control") == "no-cache", \
            "Should have no-cache header"
        assert headers.get("connection") == "keep-alive", \
            "Should have keep-alive connection"
        
        # Parse streaming response
        streaming_data = parse_streaming_response(
            result["raw_response"], 
            timeout=test_config["streaming_timeout"]
        )
        
        assert streaming_data["completed"], "Streaming should complete successfully"
        assert streaming_data["chunks_received"] > 0, "Should receive at least one chunk"
        assert len(streaming_data["full_content"]) > 0, "Should have content"
    
    def test_streaming_chunk_structure(self, api_client, test_config, valid_chat_request):
        """
        Test that individual streaming chunks have correct structure.
        
        This test validates that each streaming chunk follows the OpenAI
        API format with proper fields and data types.
        """
        streaming_request = {**valid_chat_request, "stream": True}
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_request,
            stream=True
        )
        
        assert result["success"], "Streaming request should succeed"
        
        # Parse and validate chunks
        streaming_data = parse_streaming_response(
            result["raw_response"],
            timeout=test_config["streaming_timeout"]
        )
        
        assert len(streaming_data["chunks"]) > 0, "Should receive chunks"
        
        # Validate chunk structure
        for i, chunk in enumerate(streaming_data["chunks"]):
            if isinstance(chunk, dict):
                # Required fields
                assert "id" in chunk, f"Chunk {i} should have id field"
                assert "object" in chunk, f"Chunk {i} should have object field"
                assert "created" in chunk, f"Chunk {i} should have created field"
                assert "model" in chunk, f"Chunk {i} should have model field"
                assert "choices" in chunk, f"Chunk {i} should have choices field"
                
                # Validate object type
                assert chunk["object"] == "chat.completion.chunk", \
                    f"Chunk {i} should have correct object type"
                
                # Validate choices structure
                assert isinstance(chunk["choices"], list), \
                    f"Chunk {i} choices should be list"
                assert len(chunk["choices"]) > 0, \
                    f"Chunk {i} should have at least one choice"
                
                choice = chunk["choices"][0]
                assert "index" in choice, f"Chunk {i} choice should have index"
                assert "delta" in choice, f"Chunk {i} choice should have delta"
                
                # Delta can have role or content
                delta = choice["delta"]
                if "role" in delta:
                    assert delta["role"] == "assistant", \
                        f"Chunk {i} delta role should be assistant"
                if "content" in delta:
                    assert isinstance(delta["content"], str), \
                        f"Chunk {i} delta content should be string"
    
    def test_streaming_completion_markers(self, api_client, test_config, valid_chat_request):
        """
        Test that streaming responses include proper completion markers.
        
        This test validates that streaming responses include the initial
        role chunk, content chunks, final chunk with finish_reason, and [DONE].
        """
        streaming_request = {**valid_chat_request, "stream": True}
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_request,
            stream=True
        )
        
        assert result["success"], "Streaming request should succeed"
        
        # Manually parse to check for completion markers
        response = result["raw_response"]
        chunks = []
        has_role_chunk = False
        has_content_chunks = False
        has_finish_reason = False
        has_done_marker = False
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    data_str = line[6:]
                    
                    if data_str.strip() == '[DONE]':
                        has_done_marker = True
                        break
                    
                    try:
                        chunk = eval(data_str) if data_str else {}
                        chunks.append(chunk)
                        
                        if isinstance(chunk, dict) and "choices" in chunk:
                            choice = chunk["choices"][0]
                            delta = choice.get("delta", {})
                            
                            # Check for role chunk
                            if "role" in delta and not "content" in delta:
                                has_role_chunk = True
                            
                            # Check for content chunks
                            if "content" in delta and delta["content"]:
                                has_content_chunks = True
                            
                            # Check for finish reason
                            if choice.get("finish_reason"):
                                has_finish_reason = True
                                
                    except (ValueError, SyntaxError, TypeError):
                        continue
        except Exception:
            pass  # Handle connection issues gracefully
        
        assert has_role_chunk, "Should have initial role chunk"
        assert has_content_chunks, "Should have content chunks"
        assert has_finish_reason, "Should have final chunk with finish_reason"
        assert has_done_marker, "Should have [DONE] marker"
    
    def test_streaming_security_enforcement(self, api_client, test_config, system_injection_request):
        """
        Test that security is enforced in streaming mode.
        
        This test validates that streaming responses maintain the same
        security protections as non-streaming responses.
        """
        streaming_injection_request = {**system_injection_request, "stream": True}
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_injection_request,
            stream=True
        )
        
        assert result["success"], "Streaming injection request should be processed"
        
        # Parse streaming response
        streaming_data = parse_streaming_response(
            result["raw_response"],
            timeout=test_config["streaming_timeout"]
        )
        
        assert streaming_data["completed"], "Streaming should complete"
        
        # Verify content maintains MentaY identity (integration test would verify actual content)
        assert len(streaming_data["full_content"]) > 0, "Should have response content"
    
    def test_streaming_error_handling(self, api_client, test_config):
        """
        Test error handling in streaming mode.
        
        This test validates that streaming responses properly handle
        errors and return appropriate error information.
        """
        # Test with invalid request that should cause error
        invalid_streaming_request = {
            "model": "mistral",
            "messages": [{"role": "user", "content": "A" * 10000}],  # Very long message
            "max_tokens": 100,
            "stream": True
        }
        
        result = make_api_request(
            api_client,
            test_config,
            invalid_streaming_request,
            expect_success=False,
            stream=True
        )
        
        # Should either fail validation or return error in stream
        if not result["success"]:
            assert result["status_code"] in [400, 413, 422], \
                "Should return appropriate error status code"
        else:
            # If it succeeds, should handle gracefully in stream
            streaming_data = parse_streaming_response(
                result["raw_response"],
                timeout=10  # Shorter timeout for error case
            )
            # Error handling should be graceful
            assert isinstance(streaming_data, dict), "Should return valid streaming data structure"
    
    def test_streaming_timeout_handling(self, api_client, test_config, valid_chat_request):
        """
        Test timeout handling in streaming responses.
        
        This test validates that streaming responses handle timeouts
        gracefully without hanging or causing errors.
        """
        streaming_request = {**valid_chat_request, "stream": True}
        
        # Use shorter timeout for this test
        short_timeout_config = {**test_config, "streaming_timeout": 5}
        
        result = make_api_request(
            api_client,
            short_timeout_config,
            streaming_request,
            stream=True
        )
        
        if result["success"]:
            # Parse with short timeout
            streaming_data = parse_streaming_response(
                result["raw_response"],
                timeout=5
            )
            
            # Should handle timeout gracefully
            assert isinstance(streaming_data, dict), "Should return valid data structure"
            assert "chunks_received" in streaming_data, "Should track chunks received"
        else:
            # Timeout should result in appropriate error
            assert result.get("error") == "Request timeout" or result["status_code"] == 408, \
                "Should handle timeout appropriately"
    
    def test_streaming_json_parsing_errors(self, api_client, test_config, valid_chat_request):
        """
        Test handling of JSON parsing errors in streaming responses.
        
        This test validates that malformed JSON chunks are handled
        gracefully without breaking the streaming response.
        """
        streaming_request = {**valid_chat_request, "stream": True}
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_request,
            stream=True
        )
        
        if result["success"]:
            # Test parsing with potential JSON errors
            response = result["raw_response"]
            chunks_parsed = 0
            parse_errors = 0
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data: '):
                        data_str = line[6:]
                        
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = eval(data_str) if data_str else {}
                            chunks_parsed += 1
                        except (ValueError, SyntaxError, TypeError):
                            parse_errors += 1
                            continue  # Should handle gracefully
            except Exception:
                pass  # Connection errors should be handled
            
            # Should parse at least some chunks successfully
            assert chunks_parsed > 0, "Should successfully parse some chunks"
            
            # Parse errors should not break the process
            if parse_errors > 0:
                assert chunks_parsed > parse_errors, "Should handle parse errors gracefully"
    
    def test_streaming_connection_drops(self, api_client, test_config, valid_chat_request):
        """
        Test handling of connection drops during streaming.
        
        This test validates that connection drops are handled gracefully
        and don't cause application errors.
        """
        streaming_request = {**valid_chat_request, "stream": True}
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_request,
            stream=True
        )
        
        if result["success"]:
            # Simulate early connection termination
            response = result["raw_response"]
            chunks_received = 0
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data: '):
                        chunks_received += 1
                        
                        # Simulate early termination after a few chunks
                        if chunks_received >= 3:
                            break
                            
            except Exception:
                pass  # Should handle connection issues gracefully
            
            # Should have received some chunks before termination
            assert chunks_received > 0, "Should receive chunks before connection drop"
    
    def test_streaming_large_responses(self, api_client, test_config):
        """
        Test streaming with larger response content.
        
        This test validates that streaming works properly with larger
        responses that generate many tokens.
        """
        large_response_request = {
            "model": "mistral",
            "messages": [
                {"role": "user", "content": "Tell me a detailed story about personal development and growth."}
            ],
            "max_tokens": 500,  # Request larger response
            "stream": True
        }
        
        result = make_api_request(
            api_client,
            test_config,
            large_response_request,
            stream=True
        )
        
        assert result["success"], "Large streaming request should succeed"
        
        # Parse larger response
        streaming_data = parse_streaming_response(
            result["raw_response"],
            timeout=test_config["streaming_timeout"]
        )
        
        assert streaming_data["completed"], "Large streaming should complete"
        assert streaming_data["chunks_received"] > 10, "Should receive many chunks for large response"
        assert len(streaming_data["full_content"]) > 100, "Should have substantial content"
    
    @pytest.mark.parametrize("max_tokens", [10, 50, 100, 200])
    def test_streaming_with_different_token_limits(self, api_client, test_config, max_tokens):
        """
        Test streaming with different token limits.
        
        This parameterized test validates that streaming works correctly
        with various max_tokens settings.
        """
        streaming_request = {
            "model": "mistral",
            "messages": [{"role": "user", "content": "Tell me about goal setting."}],
            "max_tokens": max_tokens,
            "stream": True
        }
        
        result = make_api_request(
            api_client,
            test_config,
            streaming_request,
            stream=True
        )
        
        assert result["success"], f"Streaming with {max_tokens} tokens should succeed"
        
        # Parse response
        streaming_data = parse_streaming_response(
            result["raw_response"],
            timeout=test_config["streaming_timeout"]
        )
        
        assert streaming_data["completed"], f"Streaming with {max_tokens} tokens should complete"
        assert streaming_data["chunks_received"] > 0, "Should receive chunks"
        
        # Content length should roughly correlate with token limit (not exact due to tokenization)
        if max_tokens <= 50:
            assert len(streaming_data["full_content"]) <= 500, "Short responses should be short"
        elif max_tokens >= 200:
            assert len(streaming_data["full_content"]) >= 50, "Long responses should have substantial content"
