"""
ArmadaBench MCP Server

MCP server that exposes Star Wars Armada game tools to LLMs.
Includes both card data tools (via ISB API) and board state tools (via Vassal).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import structlog

from .tools.game_tools import GameTools

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()

# Configuration
VASSAL_API_URL = os.environ.get("VASSAL_API_URL", "http://localhost:8080")

# Create the MCP server
app = Server("armadabench")


# Initialize tools lazily
_game_tools: GameTools | None = None


def get_game_tools() -> GameTools:
    """Get or create GameTools instance."""
    global _game_tools
    if _game_tools is None:
        _game_tools = GameTools(VASSAL_API_URL)
    return _game_tools


# ==================== Tool Definitions ====================

TOOLS = [
    # Board State Tools
    Tool(
        name="get_board_state",
        description="""Get the complete current game board state.

Returns all ships, squadrons, obstacles, and game info including:
- Round number and current phase
- All ships with position, hull, shields, defense tokens
- All squadrons with position and status
- All obstacles

Use this as your primary way to understand the current game situation.""",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="get_ship_details",
        description="""Get detailed information about a specific ship.

Provides comprehensive data including:
- Position (x, y) and rotation
- Current hull and shield values
- Defense tokens and their status
- Equipped upgrades
- Damage cards (face-up crit effects)
- Activation status""",
        inputSchema={
            "type": "object",
            "properties": {
                "ship_id": {
                    "type": "string",
                    "description": "The unique identifier of the ship"
                }
            },
            "required": ["ship_id"]
        }
    ),
    Tool(
        name="get_squadron_details",
        description="""Get detailed information about a specific squadron.

Includes position, hull, engagement status, and abilities.""",
        inputSchema={
            "type": "object",
            "properties": {
                "squadron_id": {
                    "type": "string",
                    "description": "The unique identifier of the squadron"
                }
            },
            "required": ["squadron_id"]
        }
    ),
    Tool(
        name="get_range_to_target",
        description="""Calculate the range and arc between two pieces.

Essential for planning attacks. Returns:
- Range band (close/medium/long)
- Which arc the target is in
- Whether line of sight is obstructed""",
        inputSchema={
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "string",
                    "description": "ID of the attacking/source piece"
                },
                "target_id": {
                    "type": "string",
                    "description": "ID of the target piece"
                }
            },
            "required": ["source_id", "target_id"]
        }
    ),
    Tool(
        name="screenshot_board",
        description="""Capture a screenshot of the current board.

Returns a base64-encoded image that can be analyzed visually.
Useful for understanding spatial relationships and board state.""",
        inputSchema={
            "type": "object",
            "properties": {
                "max_width": {
                    "type": "integer",
                    "description": "Maximum image width (default 1920)",
                    "default": 1920
                },
                "max_height": {
                    "type": "integer",
                    "description": "Maximum image height (default 1080)",
                    "default": 1080
                }
            },
            "required": []
        }
    ),
    # Action Tools
    Tool(
        name="execute_maneuver",
        description="""Execute a ship maneuver at the specified speed.

Moves the ship using its maneuver chart. Yaw values control
how much the ship turns at each joint.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ship_id": {
                    "type": "string",
                    "description": "ID of the ship to move"
                },
                "speed": {
                    "type": "integer",
                    "description": "Speed to move at (1-4)",
                    "minimum": 1,
                    "maximum": 4
                },
                "yaw": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": -2, "maximum": 2},
                    "description": "Yaw adjustments at each joint"
                },
                "validate_only": {
                    "type": "boolean",
                    "description": "If true, only check if move is legal",
                    "default": False
                }
            },
            "required": ["ship_id", "speed"]
        }
    ),
    Tool(
        name="execute_attack",
        description="""Execute an attack from one ship to another.

Resolves the complete attack sequence including dice,
modifications, and damage application.""",
        inputSchema={
            "type": "object",
            "properties": {
                "attacker_id": {
                    "type": "string",
                    "description": "ID of the attacking ship"
                },
                "defender_id": {
                    "type": "string",
                    "description": "ID of the defending ship"
                },
                "arc": {
                    "type": "string",
                    "enum": ["front", "left", "right", "rear"],
                    "description": "Which arc to attack from"
                },
                "dice_modifications": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Modifications to apply (e.g., concentrate_fire)"
                }
            },
            "required": ["attacker_id", "defender_id", "arc"]
        }
    ),
    Tool(
        name="activate_squadron",
        description="""Activate a squadron to move and/or attack.

Squadrons can move their speed value and then attack,
or attack and then move (with specific abilities).""",
        inputSchema={
            "type": "object",
            "properties": {
                "squadron_id": {
                    "type": "string",
                    "description": "ID of the squadron to activate"
                },
                "target_position": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Position to move to [x, y]"
                },
                "attack_target": {
                    "type": "string",
                    "description": "ID of enemy to attack"
                }
            },
            "required": ["squadron_id"]
        }
    ),
    Tool(
        name="pass_turn",
        description="""Pass the current activation.

Use when you want to activate fewer pieces than your opponent.""",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
]


# ==================== Tool Handler ====================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info("Tool called", tool=name, arguments=arguments)

    tools = get_game_tools()

    try:
        # Dispatch to appropriate method
        if name == "get_board_state":
            result = await tools.get_board_state()
        elif name == "get_ship_details":
            result = await tools.get_ship_details(arguments["ship_id"])
        elif name == "get_squadron_details":
            result = await tools.get_squadron_details(arguments["squadron_id"])
        elif name == "get_range_to_target":
            result = await tools.get_range_to_target(
                arguments["source_id"],
                arguments["target_id"]
            )
        elif name == "screenshot_board":
            result = await tools.screenshot_board(
                max_width=arguments.get("max_width", 1920),
                max_height=arguments.get("max_height", 1080)
            )
        elif name == "execute_maneuver":
            result = await tools.execute_maneuver(
                arguments["ship_id"],
                arguments["speed"],
                arguments.get("yaw"),
                arguments.get("validate_only", False)
            )
        elif name == "execute_attack":
            result = await tools.execute_attack(
                arguments["attacker_id"],
                arguments["defender_id"],
                arguments["arc"],
                arguments.get("dice_modifications")
            )
        elif name == "activate_squadron":
            target_pos = arguments.get("target_position")
            result = await tools.activate_squadron(
                arguments["squadron_id"],
                tuple(target_pos) if target_pos else None,
                arguments.get("attack_target")
            )
        elif name == "pass_turn":
            result = await tools.pass_turn()
        else:
            result = {"error": True, "message": f"Unknown tool: {name}"}

        # Convert result to JSON string
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error("Tool execution failed", tool=name, error=str(e))
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"error": True, "message": str(e)})
        )]


# ==================== Main Entry Point ====================

async def run_server():
    """Run the MCP server."""
    logger.info("Starting ArmadaBench MCP Server", vassal_url=VASSAL_API_URL)

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
