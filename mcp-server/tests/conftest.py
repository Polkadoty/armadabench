"""
Pytest configuration and shared fixtures for ArmadaBench tests.
"""

import pytest
from armadabench_mcp.models.game_state import (
    Position,
    GamePhase,
    TokenStatus,
    DefenseToken,
    HullValue,
    ShieldValue,
    ShieldValues,
    CommandDial,
    CommandTokens,
    ShipState,
    SquadronState,
    ObstacleState,
    ObstacleType,
    GameState,
    Score,
)


@pytest.fixture
def sample_position() -> Position:
    """Create a sample position."""
    return Position(x=100.0, y=200.0)


@pytest.fixture
def sample_defense_tokens() -> list[DefenseToken]:
    """Create sample defense tokens."""
    return [
        DefenseToken(type="brace", status=TokenStatus.READY),
        DefenseToken(type="redirect", status=TokenStatus.READY),
        DefenseToken(type="evade", status=TokenStatus.SPENT),
    ]


@pytest.fixture
def sample_hull_value() -> HullValue:
    """Create a sample hull value."""
    return HullValue(current=8, maximum=8)


@pytest.fixture
def sample_shield_values() -> ShieldValues:
    """Create sample shield values."""
    return ShieldValues(
        front=ShieldValue(current=4, maximum=4),
        left=ShieldValue(current=3, maximum=3),
        right=ShieldValue(current=3, maximum=3),
        rear=ShieldValue(current=2, maximum=2),
    )


@pytest.fixture
def sample_ship_state(
    sample_position: Position,
    sample_hull_value: HullValue,
    sample_shield_values: ShieldValues,
    sample_defense_tokens: list[DefenseToken],
) -> ShipState:
    """Create a sample ship state for testing."""
    return ShipState(
        id="ship-1",
        name="Victory II-class Star Destroyer",
        ship_class="victory-ii",
        faction="empire",
        owner="player1",
        points=85,
        position=sample_position,
        rotation=0.0,
        speed=2,
        hull=sample_hull_value,
        shields=sample_shield_values,
        command=3,
        squadron_value=3,
        engineering_value=4,
        defense_tokens=sample_defense_tokens,
        command_dials=[CommandDial.NAVIGATE],
        command_tokens=CommandTokens(navigate=1),
    )


@pytest.fixture
def sample_squadron_state(sample_position: Position) -> SquadronState:
    """Create a sample squadron state for testing."""
    return SquadronState(
        id="squad-1",
        name="TIE Fighter Squadron",
        squadron_type="tie-fighter",
        faction="empire",
        owner="player1",
        points=8,
        unique=False,
        position=Position(x=150.0, y=250.0),
        hull=HullValue(current=3, maximum=3),
        speed=4,
        abilities=["Swarm"],
    )


@pytest.fixture
def sample_obstacle(sample_position: Position) -> ObstacleState:
    """Create a sample obstacle."""
    return ObstacleState(
        id="obstacle-1",
        type=ObstacleType.ASTEROID,
        position=Position(x=300.0, y=300.0),
        rotation=45.0,
    )


@pytest.fixture
def sample_game_state(
    sample_ship_state: ShipState,
    sample_squadron_state: SquadronState,
    sample_obstacle: ObstacleState,
) -> GameState:
    """Create a sample game state for testing."""
    # Create a second ship for player2
    player2_ship = ShipState(
        id="ship-2",
        name="CR90 Corvette A",
        ship_class="cr90-a",
        faction="rebel",
        owner="player2",
        points=44,
        position=Position(x=500.0, y=400.0),
        rotation=180.0,
        speed=3,
        hull=HullValue(current=4, maximum=4),
        shields=ShieldValues(
            front=ShieldValue(current=2, maximum=2),
            left=ShieldValue(current=2, maximum=2),
            right=ShieldValue(current=2, maximum=2),
            rear=ShieldValue(current=1, maximum=1),
        ),
        command=1,
        squadron_value=1,
        engineering_value=2,
        defense_tokens=[
            DefenseToken(type="evade", status=TokenStatus.READY),
            DefenseToken(type="evade", status=TokenStatus.READY),
            DefenseToken(type="redirect", status=TokenStatus.READY),
        ],
    )

    return GameState(
        game_id="test-game-1",
        round=2,
        phase=GamePhase.SHIP_PHASE,
        active_player="player1",
        ships=[sample_ship_state, player2_ship],
        squadrons=[sample_squadron_state],
        obstacles=[sample_obstacle],
        score=Score(player1=50, player2=30),
        first_player="player1",
        deployment_complete=True,
    )
