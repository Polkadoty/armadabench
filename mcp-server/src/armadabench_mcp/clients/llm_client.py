"""
LLM Clients with Tool Calling Support

Provides unified interface for both Anthropic (Claude) and OpenAI (GPT) models
with tool calling capabilities for the ArmadaBench benchmark.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal
import structlog

logger = structlog.get_logger()


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments
        }


@dataclass
class LLMResponse:
    """Unified response format from LLM providers."""
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"

    # Usage tracking
    input_tokens: int = 0
    output_tokens: int = 0

    # Raw response for debugging
    raw_response: Any = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "stop_reason": self.stop_reason,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass
class Message:
    """A message in the conversation."""
    role: Literal["user", "assistant", "system", "tool"]
    content: str | list[dict[str, Any]]
    tool_call_id: str | None = None
    name: str | None = None  # Tool name for tool results


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model: str, api_key: str | None = None):
        self.model = model
        self.api_key = api_key
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat message and get a response."""
        pass

    @abstractmethod
    def format_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        result: Any,
    ) -> Message:
        """Format a tool result for inclusion in messages."""
        pass

    def get_usage_stats(self) -> dict[str, int]:
        """Get total token usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }


class AnthropicClient(LLMClient):
    """
    Anthropic Claude client with tool calling support.

    Supports models: claude-3-opus, claude-3-sonnet, claude-3-haiku,
    claude-3.5-sonnet, claude-3.5-haiku
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None
    ):
        super().__init__(model, api_key or os.environ.get("ANTHROPIC_API_KEY"))

        # Import here to avoid dependency issues if not using Anthropic
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat message to Claude."""
        logger.debug("Anthropic chat request", model=self.model, num_messages=len(messages))

        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Convert tools to Anthropic format
        anthropic_tools = None
        if tools:
            anthropic_tools = self._convert_tools(tools)

        # Build request
        request_kwargs = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            request_kwargs["system"] = system_prompt

        if anthropic_tools:
            request_kwargs["tools"] = anthropic_tools

        # Make request
        response = await self._client.messages.create(**request_kwargs)

        # Track usage
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens

        # Parse response
        return self._parse_response(response)

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to Anthropic format."""
        result = []

        for msg in messages:
            if msg.role == "system":
                # System messages are handled separately in Anthropic
                continue

            if msg.role == "tool":
                # Tool results in Anthropic are content blocks
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                    }]
                })
            elif msg.role == "assistant" and isinstance(msg.content, list):
                # Assistant message with tool calls
                result.append({
                    "role": "assistant",
                    "content": msg.content
                })
            else:
                result.append({
                    "role": msg.role,
                    "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                })

        return result

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tools to Anthropic format."""
        anthropic_tools = []

        for tool in tools:
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", tool.get("parameters", {"type": "object", "properties": {}}))
            })

        return anthropic_tools

    def _parse_response(self, response) -> LLMResponse:
        """Parse Anthropic response into LLMResponse."""
        content = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            raw_response=response
        )

    def format_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        result: Any,
    ) -> Message:
        """Format a tool result for Anthropic."""
        content = result if isinstance(result, str) else json.dumps(result)
        return Message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=tool_name
        )


class OpenAIClient(LLMClient):
    """
    OpenAI GPT client with tool calling support.

    Supports models: gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None
    ):
        super().__init__(model, api_key or os.environ.get("OPENAI_API_KEY"))

        # Import here to avoid dependency issues if not using OpenAI
        import openai
        self._client = openai.AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat message to OpenAI."""
        logger.debug("OpenAI chat request", model=self.model, num_messages=len(messages))

        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages, system_prompt)

        # Convert tools to OpenAI format
        openai_tools = None
        if tools:
            openai_tools = self._convert_tools(tools)

        # Build request
        request_kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if openai_tools:
            request_kwargs["tools"] = openai_tools

        # Make request
        response = await self._client.chat.completions.create(**request_kwargs)

        # Track usage
        if response.usage:
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

        # Parse response
        return self._parse_response(response)

    def _convert_messages(
        self,
        messages: list[Message],
        system_prompt: str | None = None
    ) -> list[dict[str, Any]]:
        """Convert messages to OpenAI format."""
        result = []

        # Add system prompt first
        if system_prompt:
            result.append({
                "role": "system",
                "content": system_prompt
            })

        for msg in messages:
            if msg.role == "system":
                result.append({
                    "role": "system",
                    "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                })
            elif msg.role == "tool":
                result.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                })
            elif msg.role == "assistant":
                msg_dict = {"role": "assistant"}

                if isinstance(msg.content, str):
                    msg_dict["content"] = msg.content
                elif isinstance(msg.content, list):
                    # Check if this is tool calls
                    if msg.content and isinstance(msg.content[0], dict) and msg.content[0].get("type") == "tool_use":
                        # Convert Anthropic-style tool calls to OpenAI format
                        msg_dict["content"] = None
                        msg_dict["tool_calls"] = [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc.get("input", {}))
                                }
                            }
                            for tc in msg.content if tc.get("type") == "tool_use"
                        ]
                    else:
                        msg_dict["content"] = json.dumps(msg.content)
                else:
                    msg_dict["content"] = str(msg.content) if msg.content else None

                result.append(msg_dict)
            else:
                result.append({
                    "role": msg.role,
                    "content": msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                })

        return result

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tools to OpenAI format."""
        openai_tools = []

        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", tool.get("parameters", {"type": "object", "properties": {}}))
                }
            })

        return openai_tools

    def _parse_response(self, response) -> LLMResponse:
        """Parse OpenAI response into LLMResponse."""
        choice = response.choices[0]
        message = choice.message

        content = message.content
        tool_calls = []

        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))

        # Map OpenAI finish reasons to our format
        stop_reason_map = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
            "content_filter": "content_filter",
        }
        stop_reason = stop_reason_map.get(choice.finish_reason, choice.finish_reason)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            raw_response=response
        )

    def format_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        result: Any,
    ) -> Message:
        """Format a tool result for OpenAI."""
        content = result if isinstance(result, str) else json.dumps(result)
        return Message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=tool_name
        )


def create_client(
    provider: Literal["anthropic", "openai"],
    model: str | None = None,
    api_key: str | None = None
) -> LLMClient:
    """
    Factory function to create an LLM client.

    Args:
        provider: "anthropic" or "openai"
        model: Model name (defaults to provider's default)
        api_key: API key (defaults to environment variable)

    Returns:
        Configured LLM client
    """
    if provider == "anthropic":
        return AnthropicClient(
            model=model or "claude-sonnet-4-20250514",
            api_key=api_key
        )
    elif provider == "openai":
        return OpenAIClient(
            model=model or "gpt-4o",
            api_key=api_key
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
