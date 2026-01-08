"""
Game Tools

MCP tools for interacting with the Vassal game engine.
Provides tools for reading board state, capturing screenshots,
and executing game actions.

Note: These tools require the Java Vassal API server to be running.
"""

from __future__ import annotations

import base64
from typing import Any, Literal
import structlog

from ..vassal_client import VassalClient, BoardState as VassalBoardState
from ..models.game_state import (
    GameState, GamePhase, ShipState, SquadronState, ObstacleState,
    Position, HullValue, ShieldValue, ShieldValues, DefenseToken, TokenStatus,
)

logger = structlog.get_logger()


class GameTools:
    """
    MCP tools for Vassal game state access and actions.

    This class provides all the board-state related tools that LLMs
    need to play Star Wars Armada through Vassal.
    """

    def __init__(self, vassal_url: str = "http://localhost:8080"):
        """
        Initialize GameTools.

        Args:
            vassal_url: URL of the Vassal API server
        """
        self.client = VassalClient(vassal_url)
        self._game_id = "current"  # Single game mode for now

    async def close(self):
        """Close the client connection."""
        await self.client.close()

    # ==================== Game State Tools ====================

    async def get_board_state(self) -> dict[str, Any]:
        """
        Get the complete current board state.

        Returns a comprehensive view of all pieces on the board,
        their positions, stats, and current game phase.

        Returns:
            dict: Complete board state including:
                - game_id: Identifier for this game
                - round: Current round number (1-6)
                - phase: Current game phase
                - active_player: Which player is active
                - ships: List of all ships with full details
                - squadrons: List of all squadrons with details
                - obstacles: List of obstacles on the board
                - score: Current score for both players

        Example:
            state = await get_board_state()
            my_ships = [s for s in state['ships'] if s['owner'] == 'player1']
        """
        logger.info("get_board_state called")

        try:
            vassal_state = await self.client.get_board_state()
            game_state = self._convert_vassal_state(vassal_state)
            return game_state.model_dump()
        except Exception as e:
            logger.error("Failed to get board state", error=str(e))
            return {
                "error": True,
                "message": f"Failed to get board state: {str(e)}",
                "suggestion": "Ensure the Vassal API server is running"
            }

    async def get_ship_details(self, ship_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific ship.

        Provides comprehensive data about a single ship including
        hull, shields, defense tokens, upgrades, and damage.

        Args:
            ship_id: The unique identifier of the ship

        Returns:
            dict: Ship details including:
                - id, name, ship_class, faction, owner
                - position (x, y), rotation, speed
                - hull (current/maximum)
                - shields (front/left/right/rear)
                - defense_tokens with status
                - upgrades and their status
                - damage_cards (face-up crit effects)
                - activated, can_attack, can_move

        Example:
            ship = await get_ship_details("isd-1")
            if ship['hull']['current'] < 4:
                # Ship is badly damaged
        """
        logger.info("get_ship_details called", ship_id=ship_id)

        try:
            ship_data = await self.client.get_ship_details(ship_id)
            ship_state = self._convert_ship_data(ship_data)
            return ship_state.model_dump()
        except Exception as e:
            logger.error("Failed to get ship details", ship_id=ship_id, error=str(e))
            return {
                "error": True,
                "message": f"Ship not found: {ship_id}",
            }

    async def get_squadron_details(self, squadron_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific squadron.

        Args:
            squadron_id: The unique identifier of the squadron

        Returns:
            dict: Squadron details including position, hull, status

        Example:
            squadron = await get_squadron_details("tie-1")
            if squadron['engaged']:
                # Squadron is locked in combat
        """
        logger.info("get_squadron_details called", squadron_id=squadron_id)

        try:
            squadron_data = await self.client.get_squadron_details(squadron_id)
            squadron_state = self._convert_squadron_data(squadron_data)
            return squadron_state.model_dump()
        except Exception as e:
            logger.error("Failed to get squadron details", squadron_id=squadron_id, error=str(e))
            return {
                "error": True,
                "message": f"Squadron not found: {squadron_id}",
            }

    async def get_range_to_target(
        self,
        source_id: str,
        target_id: str
    ) -> dict[str, Any]:
        """
        Calculate the range and arc between two pieces.

        Determines the distance and firing arc from source to target,
        essential for planning attacks and movements.

        Args:
            source_id: ID of the attacking piece
            target_id: ID of the target piece

        Returns:
            dict: Range information including:
                - range: "close", "medium", or "long"
                - distance: Exact distance in game units
                - arc: Which arc the target is in (front/left/right/rear)
                - in_arc: Whether target is in a firing arc
                - obstructed: Whether line of sight is obstructed

        Example:
            range_info = await get_range_to_target("isd-1", "cr90-1")
            if range_info['range'] == 'close' and range_info['arc'] == 'front':
                # Perfect attack opportunity!
        """
        logger.info("get_range_to_target called", source=source_id, target=target_id)

        # Get positions of both pieces
        try:
            state = await self.client.get_board_state()

            source = None
            target = None

            # Find source piece
            for ship in state.ships:
                if ship.id == source_id:
                    source = ship
                    break
            if not source:
                for sq in state.squadrons:
                    if sq.id == source_id:
                        source = sq
                        break

            # Find target piece
            for ship in state.ships:
                if ship.id == target_id:
                    target = ship
                    break
            if not target:
                for sq in state.squadrons:
                    if sq.id == target_id:
                        target = sq
                        break

            if not source or not target:
                return {
                    "error": True,
                    "message": f"Piece not found: {source_id if not source else target_id}"
                }

            # Calculate distance
            import math
            dx = target.x - source.x
            dy = target.y - source.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Determine range band (approximate - actual uses range ruler)
            # These values are rough estimates in Vassal units
            if distance < 100:
                range_band = "close"
            elif distance < 200:
                range_band = "medium"
            else:
                range_band = "long"

            # Determine arc (simplified - assumes rotation 0 = facing up)
            angle = math.degrees(math.atan2(dx, -dy))  # Relative angle
            if hasattr(source, 'rotation'):
                angle -= source.rotation
            angle = angle % 360

            if angle < 45 or angle >= 315:
                arc = "front"
            elif 45 <= angle < 135:
                arc = "right"
            elif 135 <= angle < 225:
                arc = "rear"
            else:
                arc = "left"

            return {
                "range": range_band,
                "distance": round(distance, 2),
                "arc": arc,
                "in_arc": True,  # Simplified
                "obstructed": False,  # Would need obstacle checking
            }

        except Exception as e:
            logger.error("Failed to calculate range", error=str(e))
            return {"error": True, "message": str(e)}

    # ==================== Screenshot Tools ====================

    async def screenshot_board(
        self,
        annotate: bool = True,
        max_width: int = 1920,
        max_height: int = 1080
    ) -> dict[str, Any]:
        """
        Capture a screenshot of the current board state.

        Returns an image of the Vassal board that can be used for
        visual analysis by multimodal LLMs.

        Args:
            annotate: Whether to add piece ID labels (not yet implemented)
            max_width: Maximum image width (for LLM token efficiency)
            max_height: Maximum image height

        Returns:
            dict: Screenshot data including:
                - image_url: Base64-encoded data URL (data:image/png;base64,...)
                - timestamp: When the screenshot was taken
                - board_state: Snapshot of game state at capture time

        Example:
            screenshot = await screenshot_board()
            # The image_url can be passed directly to vision-capable LLMs
        """
        logger.info("screenshot_board called", max_width=max_width, max_height=max_height)

        try:
            # Get screenshot as base64
            result = await self.client.capture_screenshot_base64()

            # Also get current state for context
            state = await self.client.get_board_state()

            return {
                "image_url": result.get("image_url"),
                "timestamp": result.get("timestamp"),
                "format": "png",
                "board_state_summary": {
                    "ships": len(state.ships),
                    "squadrons": len(state.squadrons),
                    "obstacles": len(state.obstacles),
                    "round": state.round_number,
                }
            }
        except Exception as e:
            logger.error("Failed to capture screenshot", error=str(e))
            return {
                "error": True,
                "message": f"Failed to capture screenshot: {str(e)}",
                "suggestion": "Ensure Vassal is running with a game loaded"
            }

    # ==================== Action Tools ====================

    async def execute_maneuver(
        self,
        ship_id: str,
        speed: int,
        yaw: list[int] | None = None,
        validate_only: bool = False
    ) -> dict[str, Any]:
        """
        Execute a ship maneuver.

        Moves a ship using the maneuver tool at the specified speed,
        with yaw adjustments at each joint.

        Args:
            ship_id: ID of the ship to move
            speed: Speed to move at (1-4)
            yaw: Yaw values at each joint [-2, -1, 0, 1, 2]
                 e.g., [0, 1, 0] for slight right turn at joint 2
            validate_only: If True, only check if move is legal

        Returns:
            dict: Result including:
                - success: Whether the maneuver completed
                - new_position: Final x, y, rotation
                - collisions: Any collisions that occurred
                - error: Error message if failed

        Example:
            result = await execute_maneuver("isd-1", speed=2, yaw=[0, 1, 1])
            if result['success']:
                print(f"Ship moved to {result['new_position']}")
        """
        logger.info("execute_maneuver called", ship_id=ship_id, speed=speed, yaw=yaw)

        # For now, we simplify to just moving to calculated position
        # Full maneuver tool implementation is complex

        return {
            "success": False,
            "message": "Maneuver execution not yet implemented in Vassal integration",
            "suggestion": "This feature requires the Java Vassal API to be extended",
            "ship_id": ship_id,
            "speed": speed,
            "yaw": yaw
        }

    async def execute_attack(
        self,
        attacker_id: str,
        defender_id: str,
        arc: Literal["front", "left", "right", "rear"],
        dice_modifications: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Execute an attack from one ship to another.

        Resolves a complete attack sequence including dice rolling,
        modifications, and damage application.

        Args:
            attacker_id: ID of the attacking ship
            defender_id: ID of the defending ship
            arc: Which arc to attack from
            dice_modifications: Modifications to apply
                               (e.g., ["concentrate_fire", "leading_shots"])

        Returns:
            dict: Attack result including:
                - success: Whether attack was executed
                - dice_rolled: What dice were rolled
                - final_pool: Dice after modifications
                - damage_dealt: Total damage
                - shields_depleted: Shields removed
                - hull_damage: Hull damage dealt
                - critical_effects: Any face-up damage cards

        Example:
            result = await execute_attack("isd-1", "cr90-1", "front")
            print(f"Dealt {result['damage_dealt']} damage!")
        """
        logger.info("execute_attack called",
                   attacker=attacker_id, defender=defender_id, arc=arc)

        try:
            result = await self.client.execute_attack(
                attacker_id, defender_id, arc
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Attack execution not yet fully implemented"
            }

    async def spend_defense_token(
        self,
        ship_id: str,
        token_type: Literal["evade", "brace", "redirect", "scatter", "contain", "salvo"],
        exhaust: bool = False
    ) -> dict[str, Any]:
        """
        Spend a defense token on a ship.

        Used during the defender's portion of an attack to modify damage.

        Args:
            ship_id: ID of the defending ship
            token_type: Type of token to spend
            exhaust: Whether to exhaust (ready->exhausted) vs discard

        Returns:
            dict: Result including:
                - success: Whether token was spent
                - token_status: New status of the token
                - remaining_tokens: Tokens still available
        """
        logger.info("spend_defense_token called",
                   ship_id=ship_id, token_type=token_type)

        return {
            "success": False,
            "message": "Defense token spending not yet implemented",
            "ship_id": ship_id,
            "token_type": token_type
        }

    async def activate_squadron(
        self,
        squadron_id: str,
        target_position: tuple[float, float] | None = None,
        attack_target: str | None = None
    ) -> dict[str, Any]:
        """
        Activate a squadron to move and/or attack.

        Args:
            squadron_id: ID of the squadron to activate
            target_position: Position to move to (x, y)
            attack_target: ID of enemy to attack (ship or squadron)

        Returns:
            dict: Activation result including:
                - success: Whether activation completed
                - moved_to: Final position
                - attack_result: Result of attack if performed
        """
        logger.info("activate_squadron called", squadron_id=squadron_id)

        return {
            "success": False,
            "message": "Squadron activation not yet implemented",
            "squadron_id": squadron_id
        }

    async def pass_turn(self) -> dict[str, Any]:
        """
        Pass the current activation, giving initiative to opponent.

        Used when you want to activate fewer pieces than opponent.

        Returns:
            dict: Result including new active player
        """
        logger.info("pass_turn called")

        return {
            "success": True,
            "message": "Pass recorded",
            "note": "Full turn management not yet implemented"
        }

    # ==================== Game Lifecycle Tools ====================

    async def start_new_game(self) -> dict[str, Any]:
        """
        Start a new game in Vassal.

        Initializes a fresh game state for fleet deployment.

        Returns:
            dict: New game state
        """
        logger.info("start_new_game called")

        try:
            result = await self.client.start_new_game()
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def load_saved_game(self, save_path: str) -> dict[str, Any]:
        """
        Load a saved game file.

        Args:
            save_path: Path to .vsav or .vlog file

        Returns:
            dict: Loaded game state
        """
        logger.info("load_saved_game called", path=save_path)

        try:
            result = await self.client.load_game(save_path)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== Helper Methods ====================

    def _convert_vassal_state(self, vassal_state: VassalBoardState) -> GameState:
        """Convert Vassal board state to our GameState model."""
        ships = [self._convert_ship_data(s) for s in vassal_state.ships]
        squadrons = [self._convert_squadron_data(s) for s in vassal_state.squadrons]
        obstacles = [
            ObstacleState(
                id=o.id,
                type=o.type,
                position=Position(x=o.x, y=o.y),
                rotation=o.rotation
            )
            for o in vassal_state.obstacles
        ]

        return GameState(
            game_id=self._game_id,
            round=vassal_state.round_number,
            phase=GamePhase.SHIP_PHASE,  # Default
            active_player=vassal_state.active_player or "player1",
            ships=ships,
            squadrons=squadrons,
            obstacles=obstacles,
        )

    def _convert_ship_data(self, ship) -> ShipState:
        """Convert Vassal ship data to ShipState."""
        # Build shield values
        shields = ShieldValues(
            front=ShieldValue(
                current=ship.current_shields.get("front", 0),
                maximum=ship.max_shields.get("front", 0)
            ),
            left=ShieldValue(
                current=ship.current_shields.get("left", 0),
                maximum=ship.max_shields.get("left", 0)
            ),
            right=ShieldValue(
                current=ship.current_shields.get("right", 0),
                maximum=ship.max_shields.get("right", 0)
            ),
            rear=ShieldValue(
                current=ship.current_shields.get("rear", 0),
                maximum=ship.max_shields.get("rear", 0)
            ),
        )

        # Convert defense tokens
        tokens = [
            DefenseToken(
                type=t.get("type", "brace"),
                status=TokenStatus(t.get("state", "ready"))
            )
            for t in ship.defense_tokens
        ]

        return ShipState(
            id=ship.id,
            name=ship.name,
            ship_class=ship.ship_type or "Unknown",
            faction=ship.faction or "Unknown",
            owner="player1" if ship.player_id == "1" else "player2",
            points=0,  # Not available from Vassal
            position=Position(x=ship.x, y=ship.y),
            rotation=ship.rotation,
            speed=ship.speed,
            hull=HullValue(current=ship.current_hull, maximum=ship.max_hull),
            shields=shields,
            command=3,  # Default
            squadron_value=3,
            engineering_value=4,
            defense_tokens=tokens,
            activated=ship.activated,
        )

    def _convert_squadron_data(self, sq) -> SquadronState:
        """Convert Vassal squadron data to SquadronState."""
        return SquadronState(
            id=sq.id,
            name=sq.name,
            squadron_type=sq.squadron_type or "Unknown",
            faction=sq.faction or "Unknown",
            owner="player1" if sq.player_id == "1" else "player2",
            points=0,
            unique=False,
            position=Position(x=sq.x, y=sq.y),
            hull=HullValue(current=sq.current_hull, maximum=sq.max_hull),
            speed=sq.speed,
            activated=sq.activated,
            engaged=sq.engaged,
        )
