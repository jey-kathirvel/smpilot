import hashlib
import json
import logging
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.client import OpenAIResponsesClient
from app.ai.guardrails import sanitize_context
from app.ai.prompts import ARIA_SYSTEM_PROMPT
from app.config import Settings
from app.models.ai import AIAuditLog

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AriaService:
    def __init__(self, settings: Settings, client=None):
        self.settings = settings
        self.client = client or (OpenAIResponsesClient(settings.openai_api_key) if settings.openai_api_key else None)

    def run(self, db: Session, *, feature: str, project_id, sprint_id, prompt_version: str, context: dict, schema: type[SchemaT], fallback: Callable[[], SchemaT]) -> SchemaT:
        safe_context = sanitize_context(context)
        context_hash = hashlib.sha256(json.dumps(safe_context, sort_keys=True, default=str).encode()).hexdigest()
        audit = AIAuditLog(feature=feature, project_id=project_id, sprint_id=sprint_id, prompt_version=prompt_version, request_context_hash=context_hash, model=self.settings.openai_model if self.client else None, status="PENDING")
        db.add(audit); db.flush()
        try:
            if not self.client:
                result = fallback(); audit.status = "FALLBACK"
            else:
                result = self.client.structured(model=self.settings.openai_model, instructions=ARIA_SYSTEM_PROMPT, context=safe_context, schema=schema); audit.status = "SUCCESS"
            audit.response = result.model_dump(mode="json")
        except Exception:
            logger.exception("aria_request_failed")
            result = fallback(); audit.status = "FAILED_FALLBACK"; audit.response = result.model_dump(mode="json")
        db.commit()
        return result
