"""
Game State Models

Models representing the state of a Star Wars Armada game,
including ships, squadrons, obstacles, and overall game state.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class Position(BaseModel):
    """2D position on the game board."""
    x: float
    y: float


class GamePhase(str, Enum):
    """Current phase of the game."""
    SETUP = "setup"
    COMMAND = "command"
    SHIP_PHASE = "ship_phase"
    SQUADRON_PHASE = "squadron_phase"
    STATUS_PHASE = "status_phase"
    GAME_OVER = "game_over"


class TokenStatus(str, Enum):
    """Status of a defense token."""
    READY = "ready"
    SPENT = "spent"
    EXHAUSTED = "exhausted"


class DefenseToken(BaseModel):
    """A defense token with its current status."""
    type: Literal["evade", "brace", "redirect", "scatter", "contain", "salvo"]
    status: TokenStatus = TokenStatus.READY


class HullValue(BaseModel):
    """Current and maximum hull value."""
    current: int
    maximum: int


class ShieldValue(BaseModel):
    """Shield value for a single hull zone."""
    current: int
    maximum: int


class ShieldValues(BaseModel):
    """Shield values for all hull zones."""
    front: ShieldValue
    left: ShieldValue
    right: ShieldValue
    rear: ShieldValue


class CommandDial(str, Enum):
    """Command dial choices."""
    NAVIGATE = "navigate"
    SQUADRON = "squadron"
    ENGINEERING = "engineering"
    CONCENTRATE_FIRE = "concentrate_fire"


class CommandTokens(BaseModel):
    """Command tokens held by a ship."""
    navigate: int = 0
    squadron: int = 0
    engineering: int = 0
    concentrate_fire: int = 0


class UpgradeState(BaseModel):
    """State of an upgrade card on a ship."""
    id: str
    name: str
    type: str
    exhausted: bool = False


class DamageCard(BaseModel):
    """A damage card assigned to a ship."""
    id: str
    name: str
    face_up: bool
    effect: str = ""


class ShipState(BaseModel):
    """
    Complete state of a ship during a game.

    Includes position, damage, tokens, upgrades, and available actions.
    """
    id: str
    name: str
    ship_class: str
    faction: str
    owner: Literal["player1", "player2"]
    points: int

    # Position and movement
    position: Position
    rotation: float  # degrees, 0 = facing up
    speed: int

    # Stats
    hull: HullValue
    shields: ShieldValues
    command: int
    squadron_value: int
    engineering_value: int

    # Tokens and state
    defense_tokens: list[DefenseToken] = Field(default_factory=list)
    command_dials: list[CommandDial] = Field(default_factory=list)
    command_tokens: CommandTokens = Field(default_factory=CommandTokens)

    # Upgrades and damage
    upgrades: list[UpgradeState] = Field(default_factory=list)
    damage_cards: list[DamageCard] = Field(default_factory=list)

    # Activation
    activated: bool = False
    can_activate: bool = True
    can_attack: bool = True
    can_move: bool = True


class SquadronState(BaseModel):
    """
    Complete state of a squadron during a game.
    """
    id: str
    name: str
    squadron_type: str
    faction: str
    owner: Literal["player1", "player2"]
    points: int
    unique: bool = False

    # Position
    position: Position

    # Stats
    hull: HullValue
    speed: int

    # Tokens
    defense_tokens: list[DefenseToken] = Field(default_factory=list)

    # State
    activated: bool = False
    engaged: bool = False
    engaged_by: list[str] = Field(default_factory=list)

    # Abilities
    abilities: list[str] = Field(default_factory=list)

    # Available actions
    can_activate: bool = True
    can_move: bool = True
    can_attack: bool = True


class ObstacleType(str, Enum):
    """Type of obstacle."""
    ASTEROID = "asteroid"
    DEBRIS = "debris"
    STATION = "station"
    PURRGIL = "purrgil"


class ObstacleState(BaseModel):
    """State of an obstacle on the board."""
    id: str
    type: ObstacleType
    position: Position
    rotation: float = 0


class ObjectiveState(BaseModel):
    """State of objectives for a player."""
    id: str
    name: str
    points: int = 0


class Score(BaseModel):
    """Score for both players."""
    player1: int = 0
    player2: int = 0


class GameState(BaseModel):
    """
    Complete state of a Star Wars Armada game.

    This is the primary data structure passed to LLMs for decision making.
    """
    # Game identification
    game_id: str
    round: int = 1
    phase: GamePhase = GamePhase.SETUP
    active_player: Literal["player1", "player2"] = "player1"

    # Pieces
    ships: list[ShipState] = Field(default_factory=list)
    squadrons: list[SquadronState] = Field(default_factory=list)
    obstacles: list[ObstacleState] = Field(default_factory=list)

    # Objectives
    objectives: dict[str, ObjectiveState] = Field(default_factory=dict)

    # Score
    score: Score = Field(default_factory=Score)

    # Metadata
    first_player: Literal["player1", "player2"] = "player1"
    deployment_complete: bool = False

    def get_ship_by_id(self, ship_id: str) -> ShipState | None:
        """Get a ship by its ID."""
        for ship in self.ships:
            if ship.id == ship_id:
                return ship
        return None

    def get_squadron_by_id(self, squadron_id: str) -> SquadronState | None:
        """Get a squadron by its ID."""
        for squadron in self.squadrons:
            if squadron.id == squadron_id:
                return squadron
        return None

    def get_player_ships(self, player: str) -> list[ShipState]:
        """Get all ships belonging to a player."""
        return [ship for ship in self.ships if ship.owner == player]

    def get_player_squadrons(self, player: str) -> list[SquadronState]:
        """Get all squadrons belonging to a player."""
        return [sq for sq in self.squadrons if sq.owner == player]

    def get_unactivated_ships(self, player: str) -> list[ShipState]:
        """Get ships that haven't activated this round."""
        return [
            ship for ship in self.ships
            if ship.owner == player and not ship.activated and ship.can_activate
        ]

    def get_unactivated_squadrons(self, player: str) -> list[SquadronState]:
        """Get squadrons that haven't activated this round."""
        return [
            sq for sq in self.squadrons
            if sq.owner == player and not sq.activated and sq.can_activate
        ]
