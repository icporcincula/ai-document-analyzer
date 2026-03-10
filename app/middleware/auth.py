# app/middleware/auth.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

class APIKeyAuth(HTTPBearer):
    """API Key authentication middleware"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.settings = get_settings()

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Validate API key from request headers"""
        if not self.settings.enable_auth:
            return None
            
        credentials = await super().__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if not self.verify_api_key(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired API key.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

    def verify_api_key(self, api_key: str) -> bool:
        """Verify the provided API key against the configured key"""
        if not api_key:
            return False
            
        # Compare API keys in constant time to prevent timing attacks
        import hmac
        expected_key = self.settings.api_key
        if not expected_key:
            logger.warning("API key authentication enabled but no API_KEY configured")
            return False
            
        return hmac.compare_digest(api_key, expected_key)

def get_api_key_auth() -> APIKeyAuth:
    """Factory function to create API key auth instance"""
    return APIKeyAuth()