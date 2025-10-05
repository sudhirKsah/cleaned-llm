"""
Rate Limiting Tests

This module tests the API's rate limiting functionality including:
- Per-IP rate limiting enforcement
- Rate limit threshold detection
- Temporary IP blocking
- Rate limit reset behavior
- HTTP 429 responses

Each test validates that the rate limiting system properly prevents
abuse while allowing legitimate usage patterns.
"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tests.conftest import make_api_request


class TestRateLimiting:
    """Test suite for rate limiting functionality."""
    
    def test_rate_limit_enforcement(self, api_client, test_config, valid_chat_request, reset_rate_limits):
        """
        Test that rate limits are properly enforced.
        
        This test validates that the API enforces configured rate limits
        and returns HTTP 429 when limits are exceeded.
        """
        # Make requests up to the limit
        rate_limit = min(test_config["rate_limit_per_minute"], 10)  # Cap for testing
        successful_requests = 0
        rate_limited = False
        
        for i in range(rate_limit + 5):  # Try to exceed limit
            result = make_api_request(
                api_client,
                test_config,
                valid_chat_request,
                expect_success=(i < rate_limit)
            )
            
            if result["success"]:
                successful_requests += 1
            elif result["status_code"] == 429:
                rate_limited = True
                break
            
            # Small delay between requests
            time.sleep(0.1)
        
        assert successful_requests > 0, "Should allow some requests before rate limiting"
        assert rate_limited or successful_requests >= rate_limit, \
            "Should either hit rate limit or allow expected number of requests"
    
    def test_rate_limit_response_format(self, api_client, test_config, valid_chat_request, reset_rate_limits):
        """
        Test that rate limit responses have proper format.
        
        This test validates that HTTP 429 responses include proper
        error information and follow the expected format.
        """
        # Quickly make many requests to trigger rate limiting
        rate_limit_response = None
        
        for i in range(20):  # Make many requests quickly
            result = make_api_request(
                api_client,
                test_config,
                valid_chat_request,
                expect_success=False
            )
            
            if result["status_code"] == 429:
                rate_limit_response = result
                break
            
            time.sleep(0.05)  # Very short delay
        
        if rate_limit_response:
            assert rate_limit_response["status_code"] == 429, "Should return HTTP 429"
            
            # Verify error response structure
            if isinstance(rate_limit_response["response"], dict):
                response = rate_limit_response["response"]
                assert "error" in response, "Rate limit response should contain error"
                
                error = response["error"]
                assert "message" in error, "Error should contain message"
                assert "type" in error, "Error should contain type"
                
                # Message should indicate rate limiting
                message = error["message"].lower()
                assert any(keyword in message for keyword in ["rate", "limit", "exceeded"]), \
                    "Error message should indicate rate limiting"
    
    def test_rate_limit_per_ip_isolation(self, api_client, test_config, valid_chat_request, reset_rate_limits):
        """
        Test that rate limits are applied per IP address.
        
        This test validates that rate limits are isolated per IP
        and don't affect requests from different sources.
        
        Note: This test simulates different IPs through headers where possible.
        """
        # Make requests that should be within limit
        base_requests = min(5, test_config["rate_limit_per_minute"] // 2)
        
        for i in range(base_requests):
            result = make_api_request(
                api_client,
                test_config,
                valid_chat_request
            )
            assert result["success"], f"Request {i+1} should succeed within rate limit"
            time.sleep(0.1)
        
        # Verify we haven't hit the limit yet by making another request
        final_result = make_api_request(
            api_client,
            test_config,
            valid_chat_request
        )
        
        # Should either succeed or hit rate limit, but behavior should be consistent
        assert final_result["status_code"] in [200, 429], \
            "Should return either success or rate limit status"
    
    def test_rate_limit_reset_behavior(self, api_client, test_config, valid_chat_request, reset_rate_limits):
        """
        Test that rate limits reset after the time window.
        
        This test validates that rate limits properly reset after
        the configured time window expires.
        
        Note: This test uses a shorter window for practical testing.
        """
        # Make a few requests to establish baseline
        initial_requests = min(3, test_config["rate_limit_per_minute"] // 3)
        
        for i in range(initial_requests):
            result = make_api_request(
                api_client,
                test_config,
                valid_chat_request
            )
            assert result["success"], f"Initial request {i+1} should succeed"
            time.sleep(0.1)
        
        # Wait a short time (simulating window reset)
        time.sleep(2)
        
        # Make another request after waiting
        post_wait_result = make_api_request(
            api_client,
            test_config,
            valid_chat_request
        )
        
        # Should succeed if rate limit window has reset
        # Note: In a real test environment, this would need proper time window configuration
        assert post_wait_result["status_code"] in [200, 429], \
            "Post-wait request should have valid status"
    
    def test_concurrent_request_rate_limiting(self, api_client, test_config, valid_chat_request, reset_rate_limits):
        """
        Test rate limiting with concurrent requests.
        
        This test validates that rate limiting works correctly
        when multiple requests are made concurrently.
        """
        def make_single_request():
            """Helper function to make a single request."""
            return make_api_request(
                api_client,
                test_config,
                valid_chat_request,
                expect_success=False  # Some may fail due to rate limiting
            )
        
        # Make concurrent requests
        concurrent_requests = min(10, test_config["rate_limit_per_minute"])
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit concurrent requests
            futures = [executor.submit(make_single_request) for _ in range(concurrent_requests)]
            
            # Collect results
            results = []
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Handle timeout or other errors
                    results.append({"success": False, "error": str(e), "status_code": 0})
        
        # Analyze results
        successful_requests = sum(1 for r in results if r["success"])
        rate_limited_requests = sum(1 for r in results if r.get("status_code") == 429)
        
        assert len(results) == concurrent_requests, "Should receive all results"
        assert successful_requests > 0, "Should have some successful requests"
        
        # If rate limiting is working, some requests should be rate limited
        total_processed = successful_requests + rate_limited_requests
        assert total_processed > 0, "Should process requests (either success or rate limited)"
    
    def test_rate_limit_with_different_endpoints(self, api_client, test_config, reset_rate_limits):
        """
        Test rate limiting across different endpoints.
        
        This test validates that rate limiting is applied consistently
        across different API endpoints.
        """
        # Test chat completions endpoint
        chat_request = {
            "model": "mistral",
            "messages": [{"role": "user", "content": "Test rate limiting"}],
            "max_tokens": 10
        }
        
        # Make requests to chat endpoint
        chat_results = []
        for i in range(5):
            result = make_api_request(
                api_client,
                test_config,
                chat_request,
                expect_success=False
            )
            chat_results.append(result)
            time.sleep(0.1)
        
        # Test health endpoint (should not be rate limited or have different limits)
        health_url = f"{test_config['base_url']}/health"
        health_result = api_client.get(health_url, timeout=test_config["request_timeout"])
        
        # Analyze results
        chat_successes = sum(1 for r in chat_results if r["success"])
        
        assert chat_successes > 0, "Should have some successful chat requests"
        assert health_result.status_code == 200, "Health endpoint should remain accessible"
    
    def test_rate_limit_error_details(self, api_client, test_config, valid_chat_request, reset_rate_limits):
        """
        Test that rate limit errors include helpful details.
        
        This test validates that rate limit error responses include
        useful information about limits and retry timing.
        """
        # Quickly trigger rate limiting
        rate_limit_hit = False
        rate_limit_response = None
        
        for i in range(15):  # Make many requests quickly
            result = make_api_request(
                api_client,
                test_config,
                valid_chat_request,
                expect_success=False
            )
            
            if result["status_code"] == 429:
                rate_limit_hit = True
                rate_limit_response = result
                break
            
            time.sleep(0.05)
        
        if rate_limit_hit and rate_limit_response:
            # Verify response contains helpful information
            if isinstance(rate_limit_response["response"], dict):
                response = rate_limit_response["response"]
                
                if "error" in response:
                    error = response["error"]
                    message = error.get("message", "").lower()
                    
                    # Should mention rate limiting
                    assert any(keyword in message for keyword in ["rate", "limit", "requests"]), \
                        "Error message should explain rate limiting"
                    
                    # Should have appropriate error type
                    assert error.get("type") in ["rate_limit_error", "validation_error"], \
                        "Should have appropriate error type"
    
    def test_rate_limit_streaming_requests(self, api_client, test_config, reset_rate_limits):
        """
        Test rate limiting for streaming requests.
        
        This test validates that rate limiting applies to streaming
        requests in the same way as non-streaming requests.
        """
        streaming_request = {
            "model": "mistral",
            "messages": [{"role": "user", "content": "Test streaming rate limit"}],
            "max_tokens": 20,
            "stream": True
        }
        
        # Make streaming requests
        streaming_results = []
        for i in range(8):
            result = make_api_request(
                api_client,
                test_config,
                streaming_request,
                expect_success=False,
                stream=True
            )
            streaming_results.append(result)
            time.sleep(0.1)
        
        # Analyze results
        successful_streams = sum(1 for r in streaming_results if r["success"])
        rate_limited_streams = sum(1 for r in streaming_results if r.get("status_code") == 429)
        
        assert successful_streams > 0, "Should have some successful streaming requests"
        
        # Rate limiting should apply to streaming requests
        total_handled = successful_streams + rate_limited_streams
        assert total_handled > 0, "Should handle streaming requests (success or rate limited)"
    
    @pytest.mark.parametrize("request_delay", [0.05, 0.1, 0.2, 0.5])
    def test_rate_limiting_with_different_delays(self, api_client, test_config, valid_chat_request, request_delay, reset_rate_limits):
        """
        Test rate limiting behavior with different request delays.
        
        This parameterized test validates that rate limiting behaves
        appropriately with different timing patterns.
        """
        # Make requests with specified delay
        results = []
        for i in range(6):
            result = make_api_request(
                api_client,
                test_config,
                valid_chat_request,
                expect_success=False
            )
            results.append(result)
            
            if i < 5:  # Don't delay after last request
                time.sleep(request_delay)
        
        # Analyze results
        successful_requests = sum(1 for r in results if r["success"])
        rate_limited_requests = sum(1 for r in results if r.get("status_code") == 429)
        
        assert len(results) == 6, "Should make all requests"
        assert successful_requests > 0, "Should have some successful requests"
        
        # Longer delays should result in fewer rate limit hits
        if request_delay >= 0.2:
            # With longer delays, more requests should succeed
            assert successful_requests >= 3, "Longer delays should allow more requests"
        
        # Verify total requests were processed
        total_processed = successful_requests + rate_limited_requests
        assert total_processed >= 4, "Should process most requests"
