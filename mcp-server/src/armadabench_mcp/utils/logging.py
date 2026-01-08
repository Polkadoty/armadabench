"""
Logging Utilities

Structured logging setup for ArmadaBench runs.
Captures all model interactions, tool calls, and game state changes.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level


def setup_logging(
    log_level: str = "INFO",
    output_dir: Path | None = None,
    run_id: str | None = None,
    json_output: bool = True,
) -> None:
    """
    Set up structured logging for a benchmark run.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        output_dir: Directory for log files
        run_id: Unique run identifier for log file naming
        json_output: If True, output logs as JSON
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_log_level,
        TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        processors.append(JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    import logging

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        stream=sys.stdout,
    )

    # Set up file logging if output_dir provided
    if output_dir and run_id:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        log_file = output_dir / f"{run_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logging.getLogger().addHandler(file_handler)


class RunLogger:
    """
    Logger for a specific benchmark run.

    Captures detailed information about model interactions,
    tool calls, game states, and results.
    """

    def __init__(
        self,
        run_id: str,
        output_dir: Path,
        log_model_inputs: bool = True,
        log_model_outputs: bool = True,
        log_tool_calls: bool = True,
        log_game_states: bool = True,
    ):
        """
        Initialize run logger.

        Args:
            run_id: Unique identifier for this run
            output_dir: Directory to write log files
            log_model_inputs: Whether to log prompts sent to models
            log_model_outputs: Whether to log model responses
            log_tool_calls: Whether to log MCP tool calls
            log_game_states: Whether to log game state snapshots
        """
        self.run_id = run_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_model_inputs = log_model_inputs
        self.log_model_outputs = log_model_outputs
        self.log_tool_calls = log_tool_calls
        self.log_game_states = log_game_states

        self._logger = structlog.get_logger().bind(run_id=run_id)

        # Event log for detailed tracking
        self._events: list[dict[str, Any]] = []
        self._start_time = datetime.now()

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Log an event to the event list."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "run_id": self.run_id,
            **data,
        }
        self._events.append(event)
        self._logger.info(event_type, **data)

    def log_run_start(self, config: dict[str, Any]) -> None:
        """Log the start of a benchmark run."""
        self._log_event("run_start", {"config": config})

    def log_run_end(self, result: dict[str, Any]) -> None:
        """Log the end of a benchmark run."""
        duration = (datetime.now() - self._start_time).total_seconds()
        self._log_event("run_end", {"result": result, "duration_seconds": duration})

    def log_model_input(
        self,
        player: str,
        messages: list[dict[str, Any]],
        system_prompt: str,
    ) -> None:
        """Log input sent to a model."""
        if not self.log_model_inputs:
            return
        self._log_event("model_input", {
            "player": player,
            "message_count": len(messages),
            "system_prompt_length": len(system_prompt),
            "messages": messages,
        })

    def log_model_output(
        self,
        player: str,
        response: dict[str, Any],
        tokens_used: int | None = None,
    ) -> None:
        """Log output received from a model."""
        if not self.log_model_outputs:
            return
        self._log_event("model_output", {
            "player": player,
            "response": response,
            "tokens_used": tokens_used,
        })

    def log_tool_call(
        self,
        player: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        round_number: int | None = None,
    ) -> None:
        """Log an MCP tool call."""
        if not self.log_tool_calls:
            return
        self._log_event("tool_call", {
            "player": player,
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
            "round": round_number,
        })

    # Async wrapper methods for runner compatibility
    async def log_config(self, config: dict[str, Any]) -> None:
        """Log run configuration (async wrapper)."""
        self.log_run_start(config)

    async def log_llm_response(
        self,
        player: str,
        response: dict[str, Any],
        round_number: int | None = None,
    ) -> None:
        """Log LLM response (async wrapper)."""
        self._log_event("llm_response", {
            "player": player,
            "response": response,
            "round": round_number,
        })

    async def log_tool_call_async(
        self,
        player: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        round_number: int | None = None,
    ) -> None:
        """Log tool call (async wrapper)."""
        self.log_tool_call(player, tool_name, arguments, result, round_number)

    async def log_game_result(self, results: dict[str, Any]) -> None:
        """Log final game results (async wrapper)."""
        self.log_run_end(results)
        self.save_events()

    def log_game_state(
        self,
        state: dict[str, Any],
        trigger: str = "state_change",
    ) -> None:
        """Log a game state snapshot."""
        if not self.log_game_states:
            return
        self._log_event("game_state", {
            "trigger": trigger,
            "round": state.get("round"),
            "phase": state.get("phase"),
            "state": state,
        })

    def log_game_action(
        self,
        player: str,
        action_type: str,
        details: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Log a game action (move, attack, etc.)."""
        self._log_event("game_action", {
            "player": player,
            "action_type": action_type,
            "details": details,
            "result": result,
        })

    def log_error(
        self,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log an error."""
        self._log_event("error", {
            "error_type": error_type,
            "message": message,
            "details": details or {},
        })
        self._logger.error(error_type, message=message, **(details or {}))

    def log_warning(
        self,
        warning_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log a warning."""
        self._log_event("warning", {
            "warning_type": warning_type,
            "message": message,
            "details": details or {},
        })
        self._logger.warning(warning_type, message=message, **(details or {}))

    def save_events(self) -> Path:
        """
        Save all events to a JSON file.

        Returns:
            Path to the saved events file
        """
        events_file = self.output_dir / f"{self.run_id}_events.json"
        with open(events_file, "w") as f:
            json.dump(self._events, f, indent=2, default=str)
        return events_file

    def get_events(self, event_type: str | None = None) -> list[dict[str, Any]]:
        """
        Get logged events, optionally filtered by type.

        Args:
            event_type: If provided, only return events of this type

        Returns:
            List of event dictionaries
        """
        if event_type:
            return [e for e in self._events if e["type"] == event_type]
        return self._events.copy()


def get_run_logger(
    run_id: str,
    output_dir: Path | str,
    **kwargs: Any,
) -> RunLogger:
    """
    Create a RunLogger instance.

    Args:
        run_id: Unique identifier for this run
        output_dir: Directory to write log files
        **kwargs: Additional arguments passed to RunLogger

    Returns:
        Configured RunLogger instance
    """
    return RunLogger(run_id=run_id, output_dir=Path(output_dir), **kwargs)
