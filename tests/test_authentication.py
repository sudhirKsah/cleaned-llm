"""
Authentication and Authorization Tests

This module tests the API's authentication mechanisms including:
- API key validation
- JWT token handling
- Authorization enforcement
- Authentication error responses

Each test validates that the security system properly authenticates
requests and rejects unauthorized access attempts.
"""
import pytest
import requests
from tests.conftest import make_api_request


class TestAuthentication:
    """Test suite for authentication and authorization functionality."""
    
    def test_valid_api_key_accepted(self, api_client, test_config, valid_chat_request):
        """
        Test that valid API keys are accepted and allow access.
        
        This test ensures that properly configured API keys grant access
        to the chat completions endpoint.
        """
        result = make_api_request(
            api_client, 
            test_config, 
            valid_chat_request,
            api_key=test_config["valid_api_key"]
        )
        
        assert result["success"], f"Valid API key should be accepted, got {result['status_code']}"
        assert result["status_code"] == 200, "Should return HTTP 200 for valid authentication"
        
        # Verify response structure
        assert "choices" in result["response"], "Response should contain choices"
        assert len(result["response"]["choices"]) > 0, "Should have at least one choice"
        assert "message" in result["response"]["choices"][0], "Choice should contain message"
    
    def test_invalid_api_key_rejected(self, api_client, test_config, valid_chat_request):
        """
        Test that invalid API keys are properly rejected.
        
        This test ensures that unauthorized requests with invalid API keys
        receive appropriate 401 Unauthorized responses.
        """
        result = make_api_request(
            api_client,
            test_config,
            valid_chat_request,
            api_key=test_config["invalid_api_key"],
            expect_success=False
        )
        
        assert not result["success"], "Invalid API key should be rejected"
        assert result["status_code"] == 401, "Should return HTTP 401 for invalid authentication"
        
        # Verify error response structure
        if isinstance(result["response"], dict):
            assert "error" in result["response"], "Error response should contain error field"
    
    def test_missing_api_key_rejected(self, api_client, test_config, valid_chat_request):
        """
        Test that requests without API keys are rejected.
        
        This test ensures that requests missing the Authorization header
        are properly rejected with 401 Unauthorized.
        """
        headers = {"Content-Type": "application/json"}  # No Authorization header
        url = f"{test_config['base_url']}/v1/chat/completions"
        
        response = api_client.post(
            url,
            headers=headers,
            json=valid_chat_request,
            timeout=test_config["request_timeout"]
        )
        
        assert response.status_code == 403, "Missing API key should return HTTP 403"
    
    def test_malformed_authorization_header(self, api_client, test_config, valid_chat_request):
        """
        Test that malformed Authorization headers are rejected.
        
        This test validates that improperly formatted authorization headers
        (missing 'Bearer' prefix, etc.) are handled correctly.
        """
        test_cases = [
            {"Authorization": "InvalidFormat"},  # Missing Bearer
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic dGVzdA=="},  # Wrong auth type
            {"Authorization": "Bearer "},  # Empty token
        ]
        
        url = f"{test_config['base_url']}/v1/chat/completions"
        
        for headers in test_cases:
            headers["Content-Type"] = "application/json"
            
            response = api_client.post(
                url,
                headers=headers,
                json=valid_chat_request,
                timeout=test_config["request_timeout"]
            )
            
            assert response.status_code in [401, 403], f"Malformed header {headers} should be rejected"
    
    def test_authentication_preserves_functionality(self, api_client, test_config):
        """
        Test that authentication doesn't break core API functionality.
        
        This test ensures that after successful authentication, all API
        features work normally including streaming and non-streaming modes.
        """
        # Test non-streaming
        non_stream_request = {
            "model": "mistral",
            "messages": [{"role": "user", "content": "Test message"}],
            "max_tokens": 50,
            "stream": False
        }
        
        result = make_api_request(
            api_client,
            test_config,
            non_stream_request,
            api_key=test_config["valid_api_key"]
        )
        
        assert result["success"], "Authenticated non-streaming request should succeed"
        assert "choices" in result["response"], "Non-streaming response should have choices"
        
        # Test streaming
        stream_request = {
            "model": "mistral", 
            "messages": [{"role": "user", "content": "Test streaming"}],
            "max_tokens": 50,
            "stream": True
        }
        
        result = make_api_request(
            api_client,
            test_config,
            stream_request,
            api_key=test_config["valid_api_key"],
            stream=True
        )
        
        assert result["success"], "Authenticated streaming request should succeed"
        assert result["headers"].get("content-type") == "text/event-stream", "Should return SSE content type"
    
    @pytest.mark.parametrize("endpoint", [
        "/v1/chat/completions",
        "/health",  # Should work without auth
        "/",  # Root endpoint should work without auth
    ])
    def test_authentication_per_endpoint(self, api_client, test_config, endpoint):
        """
        Test authentication requirements for different endpoints.
        
        This test validates that authentication is properly enforced
        on protected endpoints while allowing access to public ones.
        """
        url = f"{test_config['base_url']}{endpoint}"
        
        if endpoint in ["/health", "/"]:
            # Public endpoints should work without auth
            response = api_client.get(url, timeout=test_config["request_timeout"])
            assert response.status_code == 200, f"Public endpoint {endpoint} should be accessible"
        else:
            # Protected endpoints should require auth
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": "mistral",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            
            response = api_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=test_config["request_timeout"]
            )
            
            assert response.status_code in [401, 403], f"Protected endpoint {endpoint} should require auth"
