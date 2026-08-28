import json
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class OpenAIResponsesClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, timeout=10.0, max_retries=0)

    def structured(self, *, model: str, instructions: str, context: dict, schema: type[SchemaT]) -> SchemaT:
        response = self.client.responses.create(
            model=model,
            instructions=instructions,
            input=json.dumps(context, separators=(",", ":"), default=str),
            text={"format": {"type": "json_schema", "name": schema.__name__, "strict": True, "schema": schema.model_json_schema()}},
            store=False,
        )
        return schema.model_validate_json(response.output_text)
