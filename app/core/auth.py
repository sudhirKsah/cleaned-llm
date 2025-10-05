"""
Authentication and authorization system for MentaY API.
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.settings import settings


class AuthManager:
    """Handles API key and JWT authentication."""
    
    def __init__(self):
        self.security = HTTPBearer()
        self.jwt_secret = self._get_jwt_secret()
        self.valid_api_keys = set(settings.api_keys)
    
    def _get_jwt_secret(self) -> str:
        """Get or generate JWT secret."""
        # In production, this should be from environment or secure storage
        return "mentay-jwt-secret-change-in-production"
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        return api_key in self.valid_api_keys
    
    def create_jwt_token(self, user_id: str, expires_hours: int = 24) -> str:
        """Create JWT token for authenticated user."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow(),
            "iss": "mentay-api"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate_request(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """Authenticate request using API key or JWT."""
        token = credentials.credentials
        
        # Try API key first
        if self.validate_api_key(token):
            return {
                "auth_type": "api_key",
                "user_id": "api_user",
                "authenticated": True
            }
        
        # Try JWT token
        payload = self.validate_jwt_token(token)
        if payload:
            return {
                "auth_type": "jwt",
                "user_id": payload.get("user_id"),
                "authenticated": True,
                "expires": payload.get("exp")
            }
        
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )


# Global auth manager
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    """Dependency to get current authenticated user."""
    return auth_manager.authenticate_request(credentials)


# Optional: For endpoints that don't require auth (like health checks)
async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False))):
    """Optional authentication dependency."""
    if credentials is None:
        return {"authenticated": False}
    
    try:
        return auth_manager.authenticate_request(credentials)
    except HTTPException:
        return {"authenticated": False}
