from __future__ import annotations

import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request

from .service import (
    CopilotRequest,
    CopilotResponse,
    get_copilot_provider,
    run_copilot_turn,
)

router = APIRouter(prefix="/copilot", tags=["copilot"])


def _extract_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user_id from Bearer token if present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        return None

    # Verify or extract user ID via Supabase client if available
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if url and anon_key:
        try:
            from supabase import create_client
            sb = create_client(url, anon_key)
            u = sb.auth.get_user(token)
            if u and u.user:
                return str(u.user.id)
        except Exception:
            pass

    # Fallback: decode unverified sub from JWT payload for testing / offline token decoding
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub") or decoded.get("user_id")
    except Exception:
        return None


@router.get("/status")
def copilot_status():
    """Return AI Copilot operational status and model readiness."""
    provider = get_copilot_provider()
    configured = provider.is_configured()
    return {
        "status": "ready" if configured else "unconfigured",
        "provider": "google-gemini",
        "model": "gemini-3.8-flash",
        "gemini_configured": configured,
        "message": "AI Copilot operational" if configured else "GEMINI_API_KEY is not configured on the backend server."
    }


@router.post("/chat", response_model=CopilotResponse)
def copilot_chat(request: CopilotRequest, authorization: Optional[str] = Header(None)):
    """Execute conversational AI Copilot turn grounded in farmer context."""
    user_id = _extract_user_id(authorization)
    return run_copilot_turn(request, user_id=user_id)
