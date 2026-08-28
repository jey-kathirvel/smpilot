from typing import Any, Literal

from pydantic import BaseModel, Field


class AriaFinding(BaseModel):
    title: str
    detail: str
    severity: Literal["INFO", "WARNING", "CRITICAL"] = "INFO"


class AriaResponse(BaseModel):
    summary: str
    health: Literal["ON_TRACK", "AT_RISK", "CRITICAL", "UNKNOWN"] = "UNKNOWN"
    confidence: float = Field(ge=0, le=1)
    findings: list[AriaFinding] = []
    recommendations: list[str] = []
    requires_human_approval: bool = False
    metadata: dict[str, Any] = {}
