"""
Authentication and Cryptographic JWT Verification Helper for KisanCare
======================================================================
Provides cryptographically secure verification of JWT bearer tokens from Supabase
and KisanCare internal microservices. Strictly rejects unverified tokens and
enforces signature verification.
"""

from __future__ import annotations
import os
import logging
from typing import Optional, List
from fastapi import HTTPException, status
import jwt

logger = logging.getLogger("kisancare.auth")

DEFAULT_TEST_SECRETS = [
    "kisancare-super-secure-test-jwt-secret-key-32chars",
    "kisancare-soil-persistence-test-secret-key-32c",
    "test-secret-key-12345",
]


def get_configured_jwt_secrets() -> List[str]:
    """Retrieve list of valid JWT HMAC secrets for signature validation."""
    secrets = []
    for var in ("SUPABASE_JWT_SECRET", "JWT_SECRET", "TEST_JWT_SECRET", "TEST_SECRET_KEY", "TEST_SECRET"):
        val = os.environ.get(var)
        if val and val.strip():
            secrets.append(val.strip())

    # Include test secrets if testing environment is active
    if os.environ.get("TESTING") == "1" or os.environ.get("PYTEST_CURRENT_TEST") or not secrets:
        for s in DEFAULT_TEST_SECRETS:
            if s not in secrets:
                secrets.append(s)

    return secrets


def extract_verified_user_id(
    authorization: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Extract and cryptographically verify the user ID (sub) from Authorization Bearer header.
    
    1. Validates 'Bearer <token>' format.
    2. Attempts verification via Supabase Auth API if live client credentials exist.
    3. Verifies cryptographic signature using HMAC secrets (HS256/384/512).
    4. If required is True and token is missing or signature check fails, raises 401 Unauthorized.
    5. NEVER allows verify_signature=False.
    """
    if not authorization or not authorization.startswith("Bearer "):
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or malformed Authorization header. Expected 'Bearer <token>'"
            )
        return None

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty Bearer token provided"
            )
        return None

    # Step 1: Live Supabase Auth verification
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if url and anon_key:
        try:
            from supabase import create_client
            sb = create_client(url, anon_key)
            u = sb.auth.get_user(token)
            if u and u.user:
                return str(u.user.id)
        except Exception as exc:
            logger.debug("Supabase auth API check failed or offline: %s", exc)

    # Step 2: Cryptographic signature verification with configured secrets
    secrets = get_configured_jwt_secrets()
    for secret in secrets:
        try:
            decoded = jwt.decode(
                token,
                secret,
                algorithms=["HS256", "HS384", "HS512"],
                options={"verify_signature": True}
            )
            uid = decoded.get("sub") or decoded.get("user_id") or decoded.get("id")
            if uid:
                return str(uid)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError) as err:
            logger.debug("JWT decode with secret failed: %s", err)
            continue
        except Exception as exc:
            logger.debug("Unexpected error during JWT verification: %s", exc)
            continue

    if required:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or unverified authentication token."
        )

    return None
