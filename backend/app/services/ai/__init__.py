"""Provider-agnostic AI layer (roadmap I1).

Nothing outside this package may import an AI provider SDK. Features talk to
``ai_service`` (``app.services.ai.service``) and depend only on the types
exported here.
"""

from app.services.ai.base import (
    AIMessage,
    AIProvider,
    AIRequest,
    AIResponse,
    AIUsageInfo,
)
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.errors import (
    AIError,
    AIInvalidOutput,
    AIProviderError,
    AIRateLimited,
    AIUnavailable,
    AIUsageLimitExceeded,
)
from app.services.ai.fake_provider import FakeProvider
from app.services.ai.prompts import build_user_message, delimit
from app.services.ai.service import AIResult, AIService, get_ai_service

__all__ = [
    "AIResult",
    "AIService",
    "ClaudeProvider",
    "build_user_message",
    "delimit",
    "get_ai_service",
    "AIError",
    "AIInvalidOutput",
    "AIMessage",
    "AIProvider",
    "AIProviderError",
    "AIRateLimited",
    "AIRequest",
    "AIResponse",
    "AIUnavailable",
    "AIUsageInfo",
    "AIUsageLimitExceeded",
    "FakeProvider",
]
