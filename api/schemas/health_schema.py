"""Pydantic schemas for Service Health endpoint."""

from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, Field


class ModelStatus(BaseModel):
    """Health status and metadata of an individual AI model."""

    loaded: bool = Field(..., description="Whether the model is loaded in memory")
    status: str = Field(..., description="Operational status ('ready', 'error', 'uninitialized')")
    model_type: str = Field(..., description="Architecture or methodology description")
    source: str = Field(..., description="Weight file or remote registry source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional model specifications")


class HealthResponse(BaseModel):
    """Service health response schema."""

    status: str = Field(..., description="Global service status ('healthy', 'degraded', 'unhealthy')")
    service: str = Field(default="kisancare-inference-api", description="Service identifier")
    version: str = Field(..., description="API semantic version")
    timestamp: str = Field(..., description="Current ISO-8601 timestamp")
    models: Dict[str, ModelStatus] = Field(..., description="Loaded models status")
