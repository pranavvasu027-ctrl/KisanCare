"""Health check route for KisanCare Inference Service."""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter

from api.config import API_VERSION
from api.schemas.health_schema import HealthResponse, ModelStatus
from api.services.irrigation_service import irrigation_service
from api.services.yield_service import yield_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """Return health status, model readiness, and version info."""
    irrigation_meta = irrigation_service.get_status()
    yield_meta = yield_service.get_status()

    all_ready = irrigation_meta["loaded"] and yield_meta["loaded"]
    any_ready = irrigation_meta["loaded"] or yield_meta["loaded"]

    if all_ready:
        global_status = "healthy"
    elif any_ready:
        global_status = "degraded"
    else:
        global_status = "unhealthy"

    return HealthResponse(
        status=global_status,
        service="kisancare-inference-api",
        version=API_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        models={
            "irrigation": ModelStatus(**irrigation_meta),
            "yield": ModelStatus(**yield_meta),
        },
    )
