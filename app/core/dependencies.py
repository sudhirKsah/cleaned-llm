"""
Dependency injection for the Mistral service.
"""
from fastapi import HTTPException

from app.services.mistral_service import MistralService

# Global mistral service instance
_mistral_service: MistralService = None


def get_mistral_service() -> MistralService:
    """Get the global Mistral service instance."""
    if _mistral_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _mistral_service


def set_mistral_service(service: MistralService) -> None:
    """Set the global Mistral service instance."""
    global _mistral_service
    _mistral_service = service