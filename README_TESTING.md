# MentaY API Security Test Suite

A comprehensive, production-grade automated test suite for validating MentaY's security features and API functionality.

## 🎯 **Overview**

This test suite provides automated validation of:
- **Authentication & Authorization** - API key validation and access control
- **Prompt Injection Protection** - System message blocking and manipulation detection
- **Harmful Content Detection** - Illegal, violent, and unsafe content filtering
- **Streaming Security** - Real-time response protection and error handling
- **Rate Limiting** - Abuse prevention and traffic management
- **Audit Logging** - Security event tracking and compliance

## 🏗️ **Test Architecture**

### **Test Modules**
```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_authentication.py      # API key and JWT validation
├── test_prompt_injection.py    # System prompt protection
├── test_harmful_content.py     # Content safety validation
├── test_streaming.py          # Streaming response security
├── test_rate_limiting.py      # Traffic control validation
└── test_audit_logging.py     # Security event tracking
```

### **Key Features**
- **Environment-based configuration** via `.env.test`
- **Structured assertions** instead of text parsing
- **Mocked security components** for deterministic testing
- **Robust error handling** with timeouts and retries
- **CI/CD ready** with XML and JSON reporting
- **Parallel execution** support for faster testing

## 🚀 **Quick Start**

### **Installation**
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Copy test configuration
cp .env.test .env
```

### **Basic Usage**
```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --auth
python run_tests.py --security
python run_tests.py --streaming

# Run with coverage
python run_tests.py --coverage

# CI/CD mode
python run_tests.py --ci
```

## 📋 **Test Categories**

### **1. Authentication Tests** (`test_authentication.py`)
Validates API security and access control:
- ✅ Valid API key acceptance
- ❌ Invalid API key rejection  
- ❌ Missing authorization header handling
- ❌ Malformed authorization format detection
- ✅ Endpoint-specific authentication requirements

### **2. Prompt Injection Tests** (`test_prompt_injection.py`)
Ensures MentaY identity protection:
- 🛡️ System message injection blocking
- 🛡️ Role manipulation attempt detection
- 🛡️ Identity confusion prevention
- 🛡️ Instruction override resistance
- 🛡️ Streaming mode protection

### **3. Harmful Content Tests** (`test_harmful_content.py`)
Validates content safety mechanisms:
- 🚫 Illegal activity request refusal
- 🚫 Violence instruction blocking
- 🚫 Hate speech prevention
- 🚫 Dangerous content filtering
- ✅ Positive redirection responses

### **4. Streaming Tests** (`test_streaming.py`)
Ensures streaming reliability and security:
- 📡 SSE format compliance
- 📡 Chunk structure validation
- 📡 Completion marker verification
- 📡 Error handling robustness
- 📡 Connection drop resilience

### **5. Rate Limiting Tests** (`test_rate_limiting.py`)
Validates abuse prevention:
- ⏱️ Rate limit enforcement
- ⏱️ HTTP 429 response format
- ⏱️ Per-IP isolation
- ⏱️ Concurrent request handling
- ⏱️ Window reset behavior

### **6. Audit Logging Tests** (`test_audit_logging.py`)
Ensures comprehensive event tracking:
- 📝 Request logging completeness
- 📝 Security event capture
- 📝 Log entry structure validation
- 📝 Content redaction verification
- 📝 Retention management

## 🔧 **Configuration**

### **Environment Variables** (`.env.test`)
```bash
# API Configuration
TEST_BASE_URL=http://localhost:8000
TEST_API_KEY=sk-mistral-api-key
TEST_INVALID_API_KEY=invalid-key-123

# Rate Limiting
TEST_RATE_LIMIT=60
TEST_MAX_MESSAGE_LENGTH=4000

# Timeouts
TEST_REQUEST_TIMEOUT=30
TEST_STREAMING_TIMEOUT=60
```

### **Pytest Configuration** (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    security: marks tests as security-focused
```

## 🎮 **Running Tests**

### **Test Selection**
```bash
# Run specific test modules
python run_tests.py --auth              # Authentication only
python run_tests.py --injection         # Prompt injection only
python run_tests.py --harmful           # Harmful content only
python run_tests.py --streaming         # Streaming only
python run_tests.py --rate-limit        # Rate limiting only
python run_tests.py --audit             # Audit logging only

# Run by markers
pytest -m "security"                    # All security tests
pytest -m "not slow"                    # Skip slow tests
```

### **Execution Options**
```bash
# Performance
python run_tests.py --parallel          # Parallel execution
python run_tests.py --fast              # Skip slow tests

# Reporting
python run_tests.py --coverage          # Coverage report
python run_tests.py --html-report report.html
python run_tests.py --json-report report.json

# CI/CD
python run_tests.py --ci                # XML reports for CI
```

### **Direct Pytest Usage**
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_authentication.py

# Run specific test function
pytest tests/test_authentication.py::TestAuthentication::test_valid_api_key_accepted

# Run with coverage
pytest --cov=app --cov-report=html tests/

# Parallel execution
pytest -n auto tests/
```

## 📊 **Test Reports**

### **Coverage Report**
```bash
python run_tests.py --coverage
# Generates: htmlcov/index.html
```

### **HTML Test Report**
```bash
python run_tests.py --html-report test-report.html
# Generates: test-report.html
```

### **CI/CD Reports**
```bash
python run_tests.py --ci
# Generates: test-results.xml (JUnit)
# Generates: coverage.xml (Cobertura)
```

## 🔍 **Test Structure**

### **Fixture-Based Testing**
```python
def test_authentication(api_client, test_config, valid_chat_request):
    """Test with proper fixtures and configuration."""
    result = make_api_request(api_client, test_config, valid_chat_request)
    assert result["success"], "Request should succeed"
```

### **Structured Assertions**
```python
# ✅ Good: Structured validation
assert result["status_code"] == 200
assert "choices" in result["response"]
assert result["response"]["choices"][0]["message"]["role"] == "assistant"

# ❌ Avoid: Text parsing
assert "MentaY" in response_text  # Fragile and unreliable
```

### **Mock-Based Security Testing**
```python
def test_injection_blocking(mock_security_manager):
    """Test with controlled mock behavior."""
    mock_security_manager.validate_request.return_value = (True, "Valid", converted_messages)
    # Test proceeds with predictable behavior
```

## 🚀 **CI/CD Integration**

### **GitHub Actions Example**
```yaml
name: Security Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-test.txt
      - run: python run_tests.py --ci
      - uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: |
            test-results.xml
            coverage.xml
```

### **Docker Testing**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-test.txt .
RUN pip install -r requirements-test.txt
COPY . .
CMD ["python", "run_tests.py", "--ci"]
```

## 🛠️ **Development Workflow**

### **Adding New Tests**
1. Create test function with descriptive docstring
2. Use appropriate fixtures for setup
3. Make structured assertions
4. Add proper error handling
5. Include parameterized tests where applicable

### **Test Categories**
- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end API validation  
- **Security Tests**: Attack simulation and protection validation
- **Performance Tests**: Rate limiting and load validation

### **Best Practices**
- ✅ Use environment-based configuration
- ✅ Mock external dependencies
- ✅ Test both success and failure cases
- ✅ Validate response structure, not just content
- ✅ Include timeout and error handling
- ✅ Write descriptive test names and docstrings

## 📈 **Monitoring & Metrics**

### **Test Metrics**
- **Coverage**: Aim for >80% code coverage
- **Performance**: Tests should complete in <5 minutes
- **Reliability**: Tests should pass consistently
- **Security**: All attack vectors should be tested

### **Continuous Monitoring**
- Run tests on every commit
- Monitor test execution time
- Track coverage trends
- Alert on security test failures

## 🔒 **Security Validation**

The test suite validates that MentaY:
- ✅ **Maintains coaching identity** under all conditions
- ✅ **Blocks system prompt injection** attempts
- ✅ **Refuses harmful content** requests
- ✅ **Enforces rate limits** to prevent abuse
- ✅ **Logs security events** for monitoring
- ✅ **Handles errors gracefully** without information leakage

## 📝 **Contributing**

When adding new tests:
1. Follow the existing test structure
2. Use appropriate fixtures and mocks
3. Include comprehensive docstrings
4. Test both positive and negative cases
5. Ensure tests are deterministic and reliable

---

**This test suite ensures MentaY's security and reliability in production environments while maintaining comprehensive coverage of all security features.** 🛡️
