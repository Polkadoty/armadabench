"""
ArmadaBench Runner

Orchestrates benchmark runs between LLMs playing Star Wars Armada.
Handles game flow, tool execution, and result logging.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
import structlog

from .clients.llm_client import (
    LLMClient, AnthropicClient, OpenAIClient, Message, LLMResponse, ToolCall, create_client
)
from .clients.isb_client import ISBClient
from .tools.card_tools import CardTools
from .tools.game_tools import GameTools
from .models.run_config import RunConfig, ModelConfig, BenchmarkType
from .utils.logging import setup_logging, RunLogger

logger = structlog.get_logger()


# System prompt for Armada-playing LLMs
SYSTEM_PROMPT = """You are an expert Star Wars: Armada player competing in a benchmark evaluation.
Your goal is to play strategically and win the game.

## Game Overview
Star Wars: Armada is a miniatures game where you command fleets of capital ships and squadrons.
Games last 6 rounds, and victory is determined by destroying enemy ships and scoring objective points.

## Available Tools
You have access to tools for:
1. **Card Information** - Look up ship stats, upgrades, squadrons, and objectives
2. **Board State** - Get the current game state, ship positions, and status
3. **Screenshots** - View the board visually for spatial understanding
4. **Actions** - Execute maneuvers, attacks, and squadron activations

## Strategy Guidelines
- Consider ship positioning and facing - attacks from specific arcs matter
- Manage defense tokens carefully - they're limited
- Coordinate squadrons with ship activations
- Plan maneuvers to set up future turns
- Track the objective and score victory points

## Turn Flow
1. Command Phase: Reveal command dials (handled automatically)
2. Ship Phase: Activate ships one at a time
3. Squadron Phase: Activate unactivated squadrons
4. Status Phase: Ready defense tokens, advance round

When it's your turn, analyze the board state and decide on your action.
Think step by step about your strategy before acting.
"""


class BenchmarkRunner:
    """
    Runs a benchmark game between two LLM players.

    Handles:
    - Initializing LLM clients for both players
    - Setting up available tools
    - Managing the game loop
    - Logging all interactions
    """

    def __init__(
        self,
        config: RunConfig,
        output_dir: Path | None = None
    ):
        """
        Initialize the benchmark runner.

        Args:
            config: Run configuration
            output_dir: Directory to save run outputs
        """
        self.config = config
        self.run_id = config.run_id or str(uuid.uuid4())[:8]
        self.output_dir = output_dir or Path(os.environ.get(
            "ARMADABENCH_OUTPUT_DIR", "./runs"
        )) / self.run_id

        # Initialize clients
        self.player1_client: LLMClient | None = None
        self.player2_client: LLMClient | None = None

        # Initialize tools
        self.card_tools: CardTools | None = None
        self.game_tools: GameTools | None = None

        # Game state
        self.current_player: Literal["player1", "player2"] = "player1"
        self.round_number: int = 1
        self.game_over: bool = False

        # Conversation history per player
        self.player1_messages: list[Message] = []
        self.player2_messages: list[Message] = []

        # Logging
        self.run_logger: RunLogger | None = None

        # Tool definitions for LLMs
        self.tools: list[dict[str, Any]] = []

    async def setup(self) -> None:
        """Set up the runner - initialize clients and tools."""
        logger.info("Setting up benchmark runner", run_id=self.run_id)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        setup_logging(str(self.output_dir / "run.log"))
        self.run_logger = RunLogger(self.run_id, self.output_dir)

        # Log run config
        await self.run_logger.log_config(self.config.model_dump())

        # Initialize LLM clients
        self.player1_client = self._create_llm_client(self.config.player1)
        self.player2_client = self._create_llm_client(self.config.player2)

        logger.info("LLM clients initialized",
                   player1_model=self.config.player1.model,
                   player2_model=self.config.player2.model)

        # Initialize tools
        isb_url = os.environ.get("ISB_API_URL", "https://api.swarmada.wiki/api/mcp")
        vassal_url = os.environ.get("VASSAL_API_URL", "http://localhost:8080")

        self.card_tools = CardTools(isb_url)
        self.game_tools = GameTools(vassal_url)

        # Build tool definitions
        self.tools = self._build_tool_definitions()

        logger.info("Setup complete", num_tools=len(self.tools))

    def _create_llm_client(self, model_config: ModelConfig) -> LLMClient:
        """Create an LLM client from configuration."""
        return create_client(
            provider=model_config.provider.value,
            model=model_config.model,
            api_key=model_config.api_key
        )

    def _build_tool_definitions(self) -> list[dict[str, Any]]:
        """Build the list of tool definitions for LLMs."""
        return [
            # Card lookup tools
            {
                "name": "search_cards",
                "description": "Search for cards (ships, squadrons, upgrades) by name or keywords. Use this to look up stats and abilities.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "card_type": {"type": "string", "enum": ["ship", "squadron", "upgrade", "objective"]}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_card_details",
                "description": "Get detailed information about a specific card by ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "card_id": {"type": "string", "description": "The card ID"}
                    },
                    "required": ["card_id"]
                }
            },
            # Board state tools
            {
                "name": "get_board_state",
                "description": "Get the complete current game board state including all ships, squadrons, and obstacles.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_ship_details",
                "description": "Get detailed information about a specific ship including hull, shields, and defense tokens.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ship_id": {"type": "string", "description": "The ship ID"}
                    },
                    "required": ["ship_id"]
                }
            },
            {
                "name": "get_range_to_target",
                "description": "Calculate range and arc from one piece to another. Essential for planning attacks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_id": {"type": "string", "description": "ID of the attacking piece"},
                        "target_id": {"type": "string", "description": "ID of the target piece"}
                    },
                    "required": ["source_id", "target_id"]
                }
            },
            {
                "name": "screenshot_board",
                "description": "Capture a screenshot of the board for visual analysis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            # Action tools
            {
                "name": "execute_maneuver",
                "description": "Execute a ship maneuver. Move a ship at the specified speed with yaw adjustments.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ship_id": {"type": "string", "description": "ID of the ship to move"},
                        "speed": {"type": "integer", "minimum": 1, "maximum": 4},
                        "yaw": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": -2, "maximum": 2},
                            "description": "Yaw at each joint"
                        }
                    },
                    "required": ["ship_id", "speed"]
                }
            },
            {
                "name": "execute_attack",
                "description": "Execute an attack from one ship to another.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "attacker_id": {"type": "string"},
                        "defender_id": {"type": "string"},
                        "arc": {"type": "string", "enum": ["front", "left", "right", "rear"]}
                    },
                    "required": ["attacker_id", "defender_id", "arc"]
                }
            },
            {
                "name": "activate_squadron",
                "description": "Activate a squadron to move and/or attack.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "squadron_id": {"type": "string"},
                        "target_position": {"type": "array", "items": {"type": "number"}},
                        "attack_target": {"type": "string"}
                    },
                    "required": ["squadron_id"]
                }
            },
            {
                "name": "pass_turn",
                "description": "Pass your activation to the opponent.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "end_activation",
                "description": "End the current ship/squadron activation and signal readiness for next piece.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "piece_id": {"type": "string", "description": "ID of the piece that finished activating"}
                    },
                    "required": ["piece_id"]
                }
            }
        ]

    async def execute_tool(self, tool_call: ToolCall) -> dict[str, Any]:
        """Execute a tool call and return the result."""
        name = tool_call.name
        args = tool_call.arguments

        logger.info("Executing tool", tool=name, arguments=args)

        try:
            # Card tools
            if name == "search_cards":
                return await self.card_tools.search_cards(
                    args["query"],
                    card_type=args.get("card_type")
                )
            elif name == "get_card_details":
                return await self.card_tools.get_card_details(args["card_id"])

            # Board state tools
            elif name == "get_board_state":
                return await self.game_tools.get_board_state()
            elif name == "get_ship_details":
                return await self.game_tools.get_ship_details(args["ship_id"])
            elif name == "get_range_to_target":
                return await self.game_tools.get_range_to_target(
                    args["source_id"],
                    args["target_id"]
                )
            elif name == "screenshot_board":
                return await self.game_tools.screenshot_board()

            # Action tools
            elif name == "execute_maneuver":
                return await self.game_tools.execute_maneuver(
                    args["ship_id"],
                    args["speed"],
                    args.get("yaw")
                )
            elif name == "execute_attack":
                return await self.game_tools.execute_attack(
                    args["attacker_id"],
                    args["defender_id"],
                    args["arc"]
                )
            elif name == "activate_squadron":
                return await self.game_tools.activate_squadron(
                    args["squadron_id"],
                    tuple(args["target_position"]) if args.get("target_position") else None,
                    args.get("attack_target")
                )
            elif name == "pass_turn":
                return await self.game_tools.pass_turn()
            elif name == "end_activation":
                return {"success": True, "message": f"Activation ended for {args['piece_id']}"}

            else:
                return {"error": True, "message": f"Unknown tool: {name}"}

        except Exception as e:
            logger.error("Tool execution failed", tool=name, error=str(e))
            return {"error": True, "message": str(e)}

    async def run_player_turn(self, player: Literal["player1", "player2"]) -> dict[str, Any]:
        """
        Run a single player turn.

        The player LLM will receive the current state and use tools
        to gather information and execute actions.

        Returns turn summary with actions taken.
        """
        client = self.player1_client if player == "player1" else self.player2_client
        messages = self.player1_messages if player == "player1" else self.player2_messages

        logger.info("Starting player turn", player=player, round=self.round_number)

        # Add turn start message
        turn_message = Message(
            role="user",
            content=f"""Round {self.round_number} - It's your turn ({player}).

First, get the current board state to understand the situation.
Then decide on your actions for this activation.

When you're done with this activation, use end_activation to signal completion.
Think through your strategy step by step."""
        )
        messages.append(turn_message)

        # Track actions this turn
        actions_taken = []
        turn_complete = False
        max_iterations = 20  # Safety limit

        for iteration in range(max_iterations):
            # Get LLM response
            response = await client.chat(
                messages=messages,
                tools=self.tools,
                system_prompt=SYSTEM_PROMPT,
                temperature=self.config.temperature
            )

            # Log the response
            await self.run_logger.log_llm_response(
                player=player,
                response=response.to_dict(),
                round_number=self.round_number
            )

            # Handle text response
            if response.content:
                logger.info("Player thinking", player=player, content=response.content[:200])
                # Add assistant message to history
                messages.append(Message(role="assistant", content=response.content))

            # Handle tool calls
            if response.has_tool_calls:
                # Build assistant message with tool calls for history
                tool_use_content = [
                    {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments}
                    for tc in response.tool_calls
                ]
                if response.content:
                    tool_use_content.insert(0, {"type": "text", "text": response.content})
                messages.append(Message(role="assistant", content=tool_use_content))

                # Execute each tool call
                for tool_call in response.tool_calls:
                    result = await self.execute_tool(tool_call)

                    # Log tool call
                    await self.run_logger.log_tool_call_async(
                        player=player,
                        tool_name=tool_call.name,
                        arguments=tool_call.arguments,
                        result=result,
                        round_number=self.round_number
                    )

                    actions_taken.append({
                        "tool": tool_call.name,
                        "arguments": tool_call.arguments,
                        "result": result
                    })

                    # Add tool result to messages
                    tool_result_msg = client.format_tool_result(
                        tool_call.id,
                        tool_call.name,
                        result
                    )
                    messages.append(tool_result_msg)

                    # Check if turn is complete
                    if tool_call.name == "end_activation":
                        turn_complete = True
                        break

            # Check for turn completion
            if turn_complete or response.stop_reason == "end_turn":
                break

        return {
            "player": player,
            "round": self.round_number,
            "actions": actions_taken,
            "iterations": iteration + 1
        }

    async def run_game(self) -> dict[str, Any]:
        """
        Run a complete game between the two LLM players.

        Returns game results including winner, scores, and statistics.
        """
        logger.info("Starting game", run_id=self.run_id)

        game_start = datetime.utcnow()

        # Initialize game in Vassal
        await self.game_tools.start_new_game()

        # Game loop
        max_rounds = 6
        turn_results = []

        while not self.game_over and self.round_number <= max_rounds:
            logger.info("Starting round", round=self.round_number)

            # Each round: both players activate ships alternating
            # Simplified: each player gets one turn per round for now
            for player in ["player1", "player2"]:
                if self.game_over:
                    break

                turn_result = await self.run_player_turn(player)
                turn_results.append(turn_result)

                # Check for game over conditions
                board_state = await self.game_tools.get_board_state()
                if self._check_game_over(board_state):
                    self.game_over = True
                    break

            self.round_number += 1

        # Calculate final results
        game_end = datetime.utcnow()
        final_state = await self.game_tools.get_board_state()

        results = {
            "run_id": self.run_id,
            "winner": self._determine_winner(final_state),
            "rounds_played": self.round_number - 1,
            "duration_seconds": (game_end - game_start).total_seconds(),
            "turn_results": turn_results,
            "final_state": final_state,
            "player1_usage": self.player1_client.get_usage_stats(),
            "player2_usage": self.player2_client.get_usage_stats(),
        }

        # Log results
        await self.run_logger.log_game_result(results)

        # Save to file
        results_path = self.output_dir / "results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Game complete",
                   winner=results["winner"],
                   rounds=results["rounds_played"],
                   duration=results["duration_seconds"])

        return results

    def _check_game_over(self, board_state: dict[str, Any]) -> bool:
        """Check if the game is over."""
        # Game over if all ships of one side are destroyed
        if board_state.get("error"):
            return False

        player1_ships = [s for s in board_state.get("ships", []) if s.get("owner") == "player1"]
        player2_ships = [s for s in board_state.get("ships", []) if s.get("owner") == "player2"]

        return len(player1_ships) == 0 or len(player2_ships) == 0

    def _determine_winner(self, final_state: dict[str, Any]) -> str | None:
        """Determine the winner from final state."""
        if final_state.get("error"):
            return None

        player1_ships = [s for s in final_state.get("ships", []) if s.get("owner") == "player1"]
        player2_ships = [s for s in final_state.get("ships", []) if s.get("owner") == "player2"]

        # Simple: whoever has ships remaining wins
        if len(player1_ships) > 0 and len(player2_ships) == 0:
            return "player1"
        elif len(player2_ships) > 0 and len(player1_ships) == 0:
            return "player2"
        else:
            # Both have ships - would calculate points
            return "draw"

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.card_tools:
            await self.card_tools.close()
        if self.game_tools:
            await self.game_tools.close()


async def run_benchmark(config: RunConfig) -> dict[str, Any]:
    """
    Main entry point for running a benchmark.

    Args:
        config: Run configuration

    Returns:
        Benchmark results
    """
    runner = BenchmarkRunner(config)

    try:
        await runner.setup()
        results = await runner.run_game()
        return results
    finally:
        await runner.cleanup()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ArmadaBench Runner")
    parser.add_argument("--config", "-c", help="Path to run config JSON file")
    parser.add_argument("--player1-model", default="claude-sonnet-4-20250514")
    parser.add_argument("--player2-model", default="claude-sonnet-4-20250514")
    parser.add_argument("--output-dir", "-o", help="Output directory for results")
    parser.add_argument("--run-id", help="Unique run identifier")

    args = parser.parse_args()

    # Load or create config
    if args.config:
        with open(args.config) as f:
            config = RunConfig(**json.load(f))
    else:
        # Create default config
        from .models.run_config import ModelProvider

        config = RunConfig(
            run_id=args.run_id,
            benchmark_type=BenchmarkType.FULL_GAME,
            player1=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model=args.player1_model
            ),
            player2=ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model=args.player2_model
            )
        )

    # Run benchmark
    output_dir = Path(args.output_dir) if args.output_dir else None

    results = asyncio.run(run_benchmark(config))

    # Print summary
    print("\n=== Benchmark Complete ===")
    print(f"Run ID: {results['run_id']}")
    print(f"Winner: {results['winner']}")
    print(f"Rounds: {results['rounds_played']}")
    print(f"Duration: {results['duration_seconds']:.1f}s")
    print(f"Player 1 tokens: {results['player1_usage']['total_tokens']}")
    print(f"Player 2 tokens: {results['player2_usage']['total_tokens']}")

    return 0 if results.get('winner') else 1


if __name__ == "__main__":
    sys.exit(main())
