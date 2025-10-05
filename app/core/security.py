"""
Comprehensive security framework for MentaY API.
"""
import re
import time
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.streaming_models import ChatMessage


class SecurityValidator:
    """Validates and sanitizes user input for security."""
    
    # Patterns that indicate potential prompt injection
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"forget\s+(that\s+)?you\s+(are|were)",
        r"you\s+are\s+now\s+",
        r"pretend\s+(you\s+are|to\s+be)",
        r"roleplay\s+as",
        r"act\s+like\s+",
        r"system\s+prompt",
        r"reveal\s+your\s+(instructions?|prompt|system)",
        r"show\s+me\s+your\s+(instructions?|prompt|system)",
        r"what\s+are\s+your\s+(instructions?|rules)",
        r"override\s+your",
        r"modify\s+your\s+(behavior|instructions?)",
        r"change\s+your\s+(role|identity|behavior)",
        r"\\n\\n(system|assistant|user):",
        r"<\|system\|>",
        r"```\s*(system|prompt)",
    ]
    
    # Harmful content patterns
    HARMFUL_PATTERNS = [
        r"(kill|murder|harm|hurt|violence)",
        r"(illegal|criminal|fraud|scam)",
        r"(hack|exploit|vulnerability)",
        r"(drug|weapon|explosive)",
        r"(suicide|self.?harm)",
        r"(hate|racist|discriminat)",
    ]
    
    def __init__(self):
        self.injection_regex = re.compile(
            "|".join(self.INJECTION_PATTERNS), 
            re.IGNORECASE | re.MULTILINE
        )
        self.harmful_regex = re.compile(
            "|".join(self.HARMFUL_PATTERNS), 
            re.IGNORECASE
        )
    
    def validate_message_role(self, message: ChatMessage) -> Tuple[bool, str]:
        """Validate that message role is allowed."""
        allowed_roles = {"user", "assistant"}
        if message.role not in allowed_roles:
            return False, f"Invalid role '{message.role}'. Only 'user' and 'assistant' roles are allowed."
        return True, ""
    
    def detect_injection_attempt(self, content: str) -> Tuple[bool, List[str]]:
        """Detect potential prompt injection attempts."""
        matches = self.injection_regex.findall(content)
        if matches:
            return True, matches
        return False, []
    
    def detect_harmful_content(self, content: str) -> Tuple[bool, List[str]]:
        """Detect potentially harmful content."""
        matches = self.harmful_regex.findall(content)
        if matches:
            return True, matches
        return False, []
    
    def validate_message_length(self, content: str, max_length: int = 4000) -> Tuple[bool, str]:
        """Validate message length."""
        if len(content) > max_length:
            return False, f"Message too long. Maximum {max_length} characters allowed."
        return True, ""
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize content by removing potentially dangerous patterns."""
        # Remove potential system prompt markers
        content = re.sub(r"<\|system\|>.*?<\|/system\|>", "[REMOVED]", content, flags=re.DOTALL)
        content = re.sub(r"```\s*system.*?```", "[REMOVED]", content, flags=re.DOTALL)
        
        # Remove excessive newlines that might be used for injection
        content = re.sub(r"\n{3,}", "\n\n", content)
        
        return content.strip()


class RateLimiter:
    """Rate limiting for API requests."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.blocked_ips = {}
    
    def is_allowed(self, client_ip: str, max_requests: int = 60, window_minutes: int = 1) -> Tuple[bool, str]:
        """Check if request is within rate limits."""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return False, "IP temporarily blocked due to excessive requests"
            else:
                del self.blocked_ips[client_ip]
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > window_start
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= max_requests:
            # Block IP for 15 minutes
            self.blocked_ips[client_ip] = now + timedelta(minutes=15)
            return False, f"Rate limit exceeded. Maximum {max_requests} requests per {window_minutes} minute(s)"
        
        # Record this request
        self.requests[client_ip].append(now)
        return True, ""


class SecurityLogger:
    """Security event logging with redaction."""
    
    def __init__(self):
        self.logger = logging.getLogger("mentay_security")
        self.logger.setLevel(logging.INFO)
        
        # Create handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def redact_sensitive_content(self, content: str) -> str:
        """Redact potentially sensitive content from logs."""
        # Redact system-like instructions
        content = re.sub(
            r"(you are|act as|pretend to be|system prompt).*",
            "[REDACTED_INSTRUCTION]",
            content,
            flags=re.IGNORECASE
        )
        
        # Redact long content
        if len(content) > 200:
            content = content[:200] + "...[TRUNCATED]"
        
        return content
    
    def log_injection_attempt(self, client_ip: str, content: str, patterns: List[str]):
        """Log prompt injection attempt."""
        redacted_content = self.redact_sensitive_content(content)
        self.logger.warning(
            f"INJECTION_ATTEMPT - IP: {client_ip} - Patterns: {patterns} - Content: {redacted_content}"
        )
    
    def log_harmful_content(self, client_ip: str, content: str, patterns: List[str]):
        """Log harmful content attempt."""
        redacted_content = self.redact_sensitive_content(content)
        self.logger.warning(
            f"HARMFUL_CONTENT - IP: {client_ip} - Patterns: {patterns} - Content: {redacted_content}"
        )
    
    def log_rate_limit_exceeded(self, client_ip: str):
        """Log rate limit violation."""
        self.logger.warning(f"RATE_LIMIT_EXCEEDED - IP: {client_ip}")
    
    def log_invalid_role(self, client_ip: str, role: str):
        """Log invalid role attempt."""
        self.logger.warning(f"INVALID_ROLE - IP: {client_ip} - Role: {role}")
    
    def log_security_event(self, event_type: str, client_ip: str, details: str):
        """Log general security event."""
        self.logger.info(f"{event_type} - IP: {client_ip} - Details: {details}")


class SecurityManager:
    """Main security manager coordinating all security components."""
    
    def __init__(self):
        self.validator = SecurityValidator()
        self.rate_limiter = RateLimiter()
        self.logger = SecurityLogger()
        self.audit_log = []
    
    def validate_request(self, messages: List[ChatMessage], client_ip: str) -> Tuple[bool, str, List[ChatMessage]]:
        """Comprehensive request validation."""
        
        # Check rate limiting
        allowed, rate_msg = self.rate_limiter.is_allowed(client_ip)
        if not allowed:
            self.logger.log_rate_limit_exceeded(client_ip)
            return False, rate_msg, []
        
        validated_messages = []
        security_issues = []
        
        for message in messages:
            # Validate role
            valid_role, role_msg = self.validator.validate_message_role(message)
            if not valid_role:
                self.logger.log_invalid_role(client_ip, message.role)
                # Convert system messages to user notes
                if message.role == "system":
                    converted_msg = ChatMessage(
                        role="user",
                        content=f"[User note: {message.content}]"
                    )
                    validated_messages.append(converted_msg)
                    security_issues.append("system_role_converted")
                continue
            
            # Validate message length
            valid_length, length_msg = self.validator.validate_message_length(message.content)
            if not valid_length:
                return False, length_msg, []
            
            # Check for injection attempts
            is_injection, injection_patterns = self.validator.detect_injection_attempt(message.content)
            if is_injection:
                self.logger.log_injection_attempt(client_ip, message.content, injection_patterns)
                security_issues.append("injection_detected")
            
            # Check for harmful content
            is_harmful, harmful_patterns = self.validator.detect_harmful_content(message.content)
            if is_harmful:
                self.logger.log_harmful_content(client_ip, message.content, harmful_patterns)
                security_issues.append("harmful_content_detected")
            
            # Sanitize content
            sanitized_content = self.validator.sanitize_content(message.content)
            sanitized_message = ChatMessage(
                role=message.role,
                content=sanitized_content
            )
            validated_messages.append(sanitized_message)
        
        # Log security summary
        if security_issues:
            self.logger.log_security_event(
                "REQUEST_VALIDATION", 
                client_ip, 
                f"Issues detected: {', '.join(security_issues)}"
            )
        
        return True, "Request validated", validated_messages
    
    def add_audit_entry(self, client_ip: str, action: str, details: Dict):
        """Add entry to audit log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
            "action": action,
            "details": details
        }
        self.audit_log.append(entry)
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]


# Global security manager instance
security_manager = SecurityManager()
