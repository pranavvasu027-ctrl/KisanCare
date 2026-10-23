"""API Key authentication and authorization security dependency."""

from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPAuthorizationCredentials, HTTPBearer

from disease_pest_ai.api.config import API_KEY, API_KEY_NAME

# Supported credential extraction mechanisms
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> str:
    """
    Validates API Key from X-API-Key header, query param, or Bearer auth.
    Raises 401 Unauthorized if invalid or missing.
    """
    token = header_key or query_key or (bearer_token.credentials if bearer_token else None)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Missing API Key",
                "message": f"Please provide a valid API key via header '{API_KEY_NAME}' or Bearer token.",
            },
        )

    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid API Key",
                "message": "The provided API key is unauthorized.",
            },
        )

    return token
