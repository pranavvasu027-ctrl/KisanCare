from __future__ import annotations

import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request

from .service import (
    CopilotRequest,
    CopilotResponse,
    get_copilot_provider,
    run_copilot_turn,
    run_copilot_turn_async,
)

router = APIRouter(prefix="/copilot", tags=["copilot"])


def _extract_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user_id strictly from Bearer token if present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        return None

    # Verify user ID via Supabase client if available
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

    # Cryptographic JWT signature verification fallback
    from backend.app.core.auth import extract_verified_user_id
    return extract_verified_user_id(authorization, required=False)


@router.get("/status")
def copilot_status():
    """Return AI Copilot operational status and model readiness without consuming quota."""
    provider = get_copilot_provider()
    configured = provider.is_configured()
    model_name = getattr(provider, "model_name", os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
    return {
        "status": "ready" if configured else "unconfigured",
        "provider": "google-gemini",
        "model": model_name,
        "gemini_configured": configured,
        "message": "AI Copilot operational" if configured else "GEMINI_API_KEY is not configured on the backend server."
    }


@router.get("/health")
def copilot_health():
    """Diagnostic health check for the Copilot service."""
    provider = get_copilot_provider()
    configured = provider.is_configured()
    model_name = getattr(provider, "model_name", os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
    return {
        "status": "healthy" if configured else "unconfigured",
        "service": "KisanCare AI Copilot",
        "model": model_name,
        "configured": configured
    }


@router.post("/chat", response_model=CopilotResponse)
async def copilot_chat(request: CopilotRequest, authorization: Optional[str] = Header(None)):
    """Execute conversational AI Copilot turn grounded in authenticated farmer context."""
    user_id = _extract_user_id(authorization)
    return await run_copilot_turn_async(request, user_id=user_id)
