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


class SprintPlanRecommendation(BaseModel):
    sprint_goal: str
    recommended_story_ids: list[str]
    recommended_story_keys: list[str]
    expected_story_points: int = Field(ge=0)
    capacity_utilization: float = Field(ge=0)
    dependencies: list[str] = []
    risks: list[str] = []
    stories_requiring_refinement: list[str] = []
    stories_likely_too_large: list[str] = []
    rationale: str
    confidence: float = Field(ge=0, le=1)
    requires_human_approval: bool = True


class DailyScrumSummary(BaseModel):
    team_summary: str
    accomplishments: list[str] = []
    todays_focus: list[str] = []
    blockers: list[str] = []
    emerging_dependencies: list[str] = []
    missing_updates: list[str] = []
    stale_stories: list[str] = []
    coordination_needed: list[str] = []
    follow_up_suggestions: list[str] = []
    confidence: float = Field(ge=0, le=1)

class AriaAnswer(BaseModel):
    answer: str
    supporting_facts: list[str] = []
    recommended_action: str | None = None
    confidence: float = Field(ge=0, le=1)
