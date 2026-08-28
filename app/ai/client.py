import json
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class ResponsesClient:
    def __init__(self, api_key: str, *, base_url: str | None = None, app_url: str = "", app_name: str = "SMPilot AI"):
        headers = {"HTTP-Referer": app_url, "X-OpenRouter-Title": app_name} if base_url else None
        self.is_openrouter = bool(base_url)
        self.client = OpenAI(api_key=api_key, base_url=base_url, default_headers=headers, timeout=10.0, max_retries=0)

    def structured(self, *, model: str, instructions: str, context: dict, schema: type[SchemaT]) -> SchemaT:
        request = dict(
            model=model,
            instructions=instructions,
            input=json.dumps(context, separators=(",", ":"), default=str),
            text={"format": {"type": "json_schema", "name": schema.__name__, "strict": True, "schema": schema.model_json_schema()}},
            store=False,
        )
        if self.is_openrouter:
            request["extra_body"] = {"provider": {"require_parameters": True}}
        response = self.client.responses.create(**request)
        return schema.model_validate_json(response.output_text)


OpenAIResponsesClient = ResponsesClient
