"""
Tests for game state models.

Tests the Pydantic models used to represent game state,
including validation, serialization, and helper methods.
"""

import pytest
from pydantic import ValidationError

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
    UpgradeState,
    DamageCard,
    ObjectiveState,
)


class TestPosition:
    """Tests for the Position model."""

    def test_position_creation(self):
        """Test creating a position with valid coordinates."""
        pos = Position(x=100.5, y=200.5)
        assert pos.x == 100.5
        assert pos.y == 200.5

    def test_position_serialization(self):
        """Test that position serializes to dict correctly."""
        pos = Position(x=100.0, y=200.0)
        data = pos.model_dump()
        assert data == {"x": 100.0, "y": 200.0}

    def test_position_from_dict(self):
        """Test creating position from dictionary."""
        pos = Position.model_validate({"x": 50.0, "y": 75.0})
        assert pos.x == 50.0
        assert pos.y == 75.0


class TestGamePhase:
    """Tests for the GamePhase enum."""

    def test_all_phases_exist(self):
        """Test that all expected game phases exist."""
        expected_phases = ["setup", "command", "ship_phase", "squadron_phase", "status_phase", "game_over"]
        actual_phases = [phase.value for phase in GamePhase]
        assert sorted(actual_phases) == sorted(expected_phases)

    def test_phase_string_value(self):
        """Test that phases have correct string values."""
        assert GamePhase.SETUP.value == "setup"
        assert GamePhase.SHIP_PHASE.value == "ship_phase"
        assert GamePhase.GAME_OVER.value == "game_over"


class TestTokenStatus:
    """Tests for the TokenStatus enum."""

    def test_all_statuses_exist(self):
        """Test that all expected token statuses exist."""
        expected_statuses = ["ready", "spent", "exhausted"]
        actual_statuses = [status.value for status in TokenStatus]
        assert sorted(actual_statuses) == sorted(expected_statuses)


class TestDefenseToken:
    """Tests for the DefenseToken model."""

    def test_defense_token_creation(self):
        """Test creating defense tokens with valid types."""
        valid_types = ["evade", "brace", "redirect", "scatter", "contain", "salvo"]
        for token_type in valid_types:
            token = DefenseToken(type=token_type)
            assert token.type == token_type
            assert token.status == TokenStatus.READY  # Default status

    def test_defense_token_with_status(self):
        """Test creating defense token with specific status."""
        token = DefenseToken(type="brace", status=TokenStatus.SPENT)
        assert token.type == "brace"
        assert token.status == TokenStatus.SPENT

    def test_defense_token_invalid_type(self):
        """Test that invalid token types raise validation error."""
        with pytest.raises(ValidationError):
            DefenseToken(type="invalid_token")


class TestHullValue:
    """Tests for the HullValue model."""

    def test_hull_value_creation(self):
        """Test creating hull values."""
        hull = HullValue(current=5, maximum=8)
        assert hull.current == 5
        assert hull.maximum == 8

    def test_hull_value_full(self):
        """Test hull at full health."""
        hull = HullValue(current=8, maximum=8)
        assert hull.current == hull.maximum


class TestShieldValues:
    """Tests for the ShieldValues model."""

    def test_shield_values_creation(self, sample_shield_values: ShieldValues):
        """Test creating shield values for all zones."""
        assert sample_shield_values.front.current == 4
        assert sample_shield_values.left.current == 3
        assert sample_shield_values.right.current == 3
        assert sample_shield_values.rear.current == 2


class TestCommandTokens:
    """Tests for the CommandTokens model."""

    def test_command_tokens_defaults(self):
        """Test that command tokens default to zero."""
        tokens = CommandTokens()
        assert tokens.navigate == 0
        assert tokens.squadron == 0
        assert tokens.engineering == 0
        assert tokens.concentrate_fire == 0

    def test_command_tokens_with_values(self):
        """Test creating command tokens with specific values."""
        tokens = CommandTokens(navigate=1, engineering=2)
        assert tokens.navigate == 1
        assert tokens.engineering == 2
        assert tokens.squadron == 0


class TestShipState:
    """Tests for the ShipState model."""

    def test_ship_state_creation(self, sample_ship_state: ShipState):
        """Test creating a ship state with all fields."""
        assert sample_ship_state.id == "ship-1"
        assert sample_ship_state.name == "Victory II-class Star Destroyer"
        assert sample_ship_state.faction == "empire"
        assert sample_ship_state.owner == "player1"
        assert sample_ship_state.points == 85

    def test_ship_state_defaults(self, sample_ship_state: ShipState):
        """Test that ship state has correct defaults."""
        assert sample_ship_state.activated is False
        assert sample_ship_state.can_activate is True
        assert sample_ship_state.can_attack is True
        assert sample_ship_state.can_move is True

    def test_ship_state_serialization(self, sample_ship_state: ShipState):
        """Test that ship state serializes correctly."""
        data = sample_ship_state.model_dump()
        assert data["id"] == "ship-1"
        assert data["position"]["x"] == 100.0
        assert data["hull"]["current"] == 8

    def test_ship_state_invalid_owner(self):
        """Test that invalid owner raises validation error."""
        with pytest.raises(ValidationError):
            ShipState(
                id="test",
                name="Test Ship",
                ship_class="test",
                faction="empire",
                owner="invalid_player",  # Invalid: must be "player1" or "player2"
                points=50,
                position=Position(x=0, y=0),
                rotation=0,
                speed=2,
                hull=HullValue(current=5, maximum=5),
                shields=ShieldValues(
                    front=ShieldValue(current=2, maximum=2),
                    left=ShieldValue(current=2, maximum=2),
                    right=ShieldValue(current=2, maximum=2),
                    rear=ShieldValue(current=1, maximum=1),
                ),
                command=2,
                squadron_value=2,
                engineering_value=3,
            )


class TestSquadronState:
    """Tests for the SquadronState model."""

    def test_squadron_state_creation(self, sample_squadron_state: SquadronState):
        """Test creating a squadron state."""
        assert sample_squadron_state.id == "squad-1"
        assert sample_squadron_state.name == "TIE Fighter Squadron"
        assert sample_squadron_state.faction == "empire"
        assert sample_squadron_state.points == 8

    def test_squadron_state_defaults(self, sample_squadron_state: SquadronState):
        """Test squadron state defaults."""
        assert sample_squadron_state.activated is False
        assert sample_squadron_state.engaged is False
        assert sample_squadron_state.engaged_by == []

    def test_squadron_with_abilities(self, sample_squadron_state: SquadronState):
        """Test squadron with abilities."""
        assert "Swarm" in sample_squadron_state.abilities


class TestObstacleState:
    """Tests for the ObstacleState model."""

    def test_obstacle_creation(self, sample_obstacle: ObstacleState):
        """Test creating an obstacle."""
        assert sample_obstacle.id == "obstacle-1"
        assert sample_obstacle.type == ObstacleType.ASTEROID
        assert sample_obstacle.rotation == 45.0

    def test_all_obstacle_types(self):
        """Test all obstacle types are valid."""
        for obstacle_type in ObstacleType:
            obstacle = ObstacleState(
                id="test",
                type=obstacle_type,
                position=Position(x=0, y=0),
            )
            assert obstacle.type == obstacle_type


class TestScore:
    """Tests for the Score model."""

    def test_score_defaults(self):
        """Test that scores default to zero."""
        score = Score()
        assert score.player1 == 0
        assert score.player2 == 0

    def test_score_with_values(self):
        """Test creating score with values."""
        score = Score(player1=150, player2=75)
        assert score.player1 == 150
        assert score.player2 == 75


class TestGameState:
    """Tests for the GameState model."""

    def test_game_state_creation(self, sample_game_state: GameState):
        """Test creating a complete game state."""
        assert sample_game_state.game_id == "test-game-1"
        assert sample_game_state.round == 2
        assert sample_game_state.phase == GamePhase.SHIP_PHASE
        assert len(sample_game_state.ships) == 2
        assert len(sample_game_state.squadrons) == 1
        assert len(sample_game_state.obstacles) == 1

    def test_get_ship_by_id(self, sample_game_state: GameState):
        """Test retrieving a ship by its ID."""
        ship = sample_game_state.get_ship_by_id("ship-1")
        assert ship is not None
        assert ship.name == "Victory II-class Star Destroyer"

        # Test non-existent ship
        assert sample_game_state.get_ship_by_id("non-existent") is None

    def test_get_squadron_by_id(self, sample_game_state: GameState):
        """Test retrieving a squadron by its ID."""
        squadron = sample_game_state.get_squadron_by_id("squad-1")
        assert squadron is not None
        assert squadron.name == "TIE Fighter Squadron"

        # Test non-existent squadron
        assert sample_game_state.get_squadron_by_id("non-existent") is None

    def test_get_player_ships(self, sample_game_state: GameState):
        """Test retrieving ships by player."""
        player1_ships = sample_game_state.get_player_ships("player1")
        assert len(player1_ships) == 1
        assert player1_ships[0].faction == "empire"

        player2_ships = sample_game_state.get_player_ships("player2")
        assert len(player2_ships) == 1
        assert player2_ships[0].faction == "rebel"

    def test_get_player_squadrons(self, sample_game_state: GameState):
        """Test retrieving squadrons by player."""
        player1_squadrons = sample_game_state.get_player_squadrons("player1")
        assert len(player1_squadrons) == 1

        player2_squadrons = sample_game_state.get_player_squadrons("player2")
        assert len(player2_squadrons) == 0

    def test_get_unactivated_ships(self, sample_game_state: GameState):
        """Test retrieving unactivated ships."""
        unactivated = sample_game_state.get_unactivated_ships("player1")
        assert len(unactivated) == 1  # The ship hasn't activated yet

        # Activate the ship
        sample_game_state.ships[0].activated = True
        unactivated = sample_game_state.get_unactivated_ships("player1")
        assert len(unactivated) == 0

    def test_get_unactivated_squadrons(self, sample_game_state: GameState):
        """Test retrieving unactivated squadrons."""
        unactivated = sample_game_state.get_unactivated_squadrons("player1")
        assert len(unactivated) == 1

        # Activate the squadron
        sample_game_state.squadrons[0].activated = True
        unactivated = sample_game_state.get_unactivated_squadrons("player1")
        assert len(unactivated) == 0

    def test_game_state_serialization(self, sample_game_state: GameState):
        """Test that game state serializes to JSON-compatible dict."""
        data = sample_game_state.model_dump()
        assert data["game_id"] == "test-game-1"
        assert data["phase"] == "ship_phase"
        assert len(data["ships"]) == 2

    def test_game_state_from_json(self, sample_game_state: GameState):
        """Test recreating game state from JSON."""
        data = sample_game_state.model_dump()
        restored = GameState.model_validate(data)
        assert restored.game_id == sample_game_state.game_id
        assert restored.round == sample_game_state.round
        assert len(restored.ships) == len(sample_game_state.ships)


class TestUpgradeState:
    """Tests for the UpgradeState model."""

    def test_upgrade_state_creation(self):
        """Test creating an upgrade state."""
        upgrade = UpgradeState(
            id="darth-vader-commander",
            name="Darth Vader",
            type="commander",
        )
        assert upgrade.id == "darth-vader-commander"
        assert upgrade.name == "Darth Vader"
        assert upgrade.exhausted is False

    def test_exhausted_upgrade(self):
        """Test an exhausted upgrade."""
        upgrade = UpgradeState(
            id="engine-techs",
            name="Engine Techs",
            type="support-team",
            exhausted=True,
        )
        assert upgrade.exhausted is True


class TestDamageCard:
    """Tests for the DamageCard model."""

    def test_damage_card_face_down(self):
        """Test a face-down damage card."""
        card = DamageCard(
            id="damage-1",
            name="Standard Damage",
            face_up=False,
        )
        assert card.face_up is False
        assert card.effect == ""

    def test_damage_card_face_up(self):
        """Test a face-up damage card with effect."""
        card = DamageCard(
            id="structural-damage",
            name="Structural Damage",
            face_up=True,
            effect="Reduce engineering value by 1",
        )
        assert card.face_up is True
        assert card.effect == "Reduce engineering value by 1"


class TestObjectiveState:
    """Tests for the ObjectiveState model."""

    def test_objective_state_creation(self):
        """Test creating an objective state."""
        objective = ObjectiveState(
            id="advanced-gunnery",
            name="Advanced Gunnery",
            points=15,
        )
        assert objective.id == "advanced-gunnery"
        assert objective.name == "Advanced Gunnery"
        assert objective.points == 15
