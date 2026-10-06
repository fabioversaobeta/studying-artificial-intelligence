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
from app.services.ai.errors import (
    AIError,
    AIInvalidOutput,
    AIProviderError,
    AIRateLimited,
    AIUnavailable,
    AIUsageLimitExceeded,
)
from app.services.ai.fake_provider import FakeProvider

__all__ = [
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
