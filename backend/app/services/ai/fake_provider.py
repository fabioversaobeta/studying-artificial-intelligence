"""Deterministic provider for tests and for running without an API key.

Behaviour is driven by a ``responses`` queue, ``rules`` (``(predicate, text)``
pairs) or ``fixtures`` keyed by ``request.purpose``. With nothing matching it
answers a fixed string, or -- when a schema is requested -- a minimal instance
generated from the JSON schema (strings ``"fake"``, numbers ``0``, first enum
value...). It never touches the network.
"""

import json
import time
from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from app.services.ai.base import AIRequest, AIResponse, AIUsageInfo
from app.services.ai.errors import AIError

Rule = tuple[Callable[[AIRequest], bool], str]


def _example_from_schema(schema: dict[str, Any], defs: dict[str, Any]) -> Any:
    if "$ref" in schema:
        return _example_from_schema(defs[schema["$ref"].split("/")[-1]], defs)
    if "enum" in schema:
        return schema["enum"][0]
    if "const" in schema:
        return schema["const"]
    for key in ("anyOf", "oneOf"):
        if key in schema:
            options = [o for o in schema[key] if o.get("type") != "null"] or schema[key]
            return _example_from_schema(options[0], defs)
    kind = schema.get("type")
    if kind == "object":
        return {
            name: _example_from_schema(sub, defs)
            for name, sub in schema.get("properties", {}).items()
        }
    if kind == "array":
        item = _example_from_schema(schema.get("items", {}), defs)
        return [item for _ in range(int(schema.get("minItems", 0)))]
    if kind == "string":
        return "fake"
    if kind == "integer":
        return int(schema.get("minimum", 0))
    if kind == "number":
        return float(schema.get("minimum", 0))
    if kind == "boolean":
        return False
    return None


class FakeProvider:
    name = "fake"

    def __init__(
        self,
        *,
        model: str = "fake-model",
        rules: Iterable[Rule] = (),
        responses: Iterable[str | Exception] = (),
        fixtures: dict[str, str] | None = None,
        default_text: str = "This is a fake AI response.",
    ) -> None:
        self.model = model
        self.rules = list(rules)
        self.responses: deque[str | Exception] = deque(responses)
        self.fixtures = dict(fixtures or {})
        self.default_text = default_text
        self.requests: list[AIRequest] = []

    def complete(self, request: AIRequest) -> AIResponse:
        started = time.perf_counter()
        self.requests.append(request)
        text = self._answer(request)
        prompt_chars = len(request.system) + sum(len(m.content) for m in request.messages)
        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            usage=AIUsageInfo(
                input_tokens=max(1, prompt_chars // 4),
                output_tokens=min(max(1, len(text) // 4), request.max_tokens),
            ),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _answer(self, request: AIRequest) -> str:
        if self.responses:
            item = self.responses.popleft()
            if isinstance(item, Exception):
                if isinstance(item, AIError):
                    raise item
                raise AIError(str(item))
            return item
        for predicate, text in self.rules:
            if predicate(request):
                return text
        if request.purpose in self.fixtures:
            return self.fixtures[request.purpose]
        if request.output_schema is not None:
            schema = request.output_schema.model_json_schema()
            return json.dumps(_example_from_schema(schema, schema.get("$defs", {})))
        return self.default_text
