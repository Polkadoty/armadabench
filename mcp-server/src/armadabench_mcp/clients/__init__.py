"""
ArmadaBench API Clients

Clients for external APIs:
- ISB API: Card data and fleet validation
- Anthropic: Claude models with tool use
- OpenAI: GPT models with tool use
"""

from .isb_client import ISBClient
from .llm_client import LLMClient, AnthropicClient, OpenAIClient, LLMResponse, ToolCall

__all__ = [
    "ISBClient",
    "LLMClient",
    "AnthropicClient",
    "OpenAIClient",
    "LLMResponse",
    "ToolCall",
]
