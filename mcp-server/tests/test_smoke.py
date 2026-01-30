"""
Smoke tests for the ArmadaBench MCP server.

These tests verify that all modules can be imported without errors,
catching syntax errors, missing dependencies, and circular imports early.
"""

import pytest


class TestModuleImports:
    """Test that all modules can be imported."""

    def test_import_models_game_state(self):
        """Test importing game state models."""
        from armadabench_mcp.models import game_state
        assert hasattr(game_state, "GameState")
        assert hasattr(game_state, "ShipState")
        assert hasattr(game_state, "SquadronState")

    def test_import_models_run_config(self):
        """Test importing run config models."""
        from armadabench_mcp.models import run_config
        assert run_config is not None

    def test_import_tools_card_tools(self):
        """Test importing card tools."""
        from armadabench_mcp.tools import card_tools
        assert hasattr(card_tools, "CardTools")

    def test_import_tools_game_tools(self):
        """Test importing game tools."""
        from armadabench_mcp.tools import game_tools
        assert game_tools is not None

    def test_import_clients_isb_client(self):
        """Test importing ISB client."""
        from armadabench_mcp.clients import isb_client
        assert hasattr(isb_client, "ISBClient")

    def test_import_clients_llm_client(self):
        """Test importing LLM client."""
        from armadabench_mcp.clients import llm_client
        assert llm_client is not None

    def test_import_vassal_client(self):
        """Test importing Vassal client."""
        from armadabench_mcp import vassal_client
        assert vassal_client is not None

    def test_import_server(self):
        """Test importing server module."""
        from armadabench_mcp import server
        assert server is not None

    def test_import_runner(self):
        """Test importing runner module."""
        from armadabench_mcp import runner
        assert runner is not None

    def test_import_utils_logging(self):
        """Test importing logging utilities."""
        from armadabench_mcp.utils import logging
        assert logging is not None


class TestModelInstantiation:
    """Test that models can be instantiated with minimal data."""

    def test_position_instantiation(self):
        """Test creating a Position."""
        from armadabench_mcp.models.game_state import Position
        pos = Position(x=0, y=0)
        assert pos.x == 0
        assert pos.y == 0

    def test_game_state_minimal(self):
        """Test creating a minimal GameState."""
        from armadabench_mcp.models.game_state import GameState
        state = GameState(game_id="test")
        assert state.game_id == "test"
        assert state.round == 1
        assert len(state.ships) == 0

    def test_score_defaults(self):
        """Test Score with default values."""
        from armadabench_mcp.models.game_state import Score
        score = Score()
        assert score.player1 == 0
        assert score.player2 == 0


class TestToolsInstantiation:
    """Test that tool classes can be instantiated."""

    def test_card_tools_instantiation(self):
        """Test creating CardTools without a client."""
        from armadabench_mcp.tools.card_tools import CardTools
        tools = CardTools()
        assert tools is not None
        assert tools._client is None  # No client until first use

    def test_card_tools_with_url(self):
        """Test creating CardTools with a custom URL."""
        from armadabench_mcp.tools.card_tools import CardTools
        tools = CardTools("https://custom-api.example.com")
        assert tools is not None
        assert tools._owns_client is True


class TestEnums:
    """Test that all enums have expected values."""

    def test_game_phase_values(self):
        """Test GamePhase enum values."""
        from armadabench_mcp.models.game_state import GamePhase
        assert len(GamePhase) == 6
        assert GamePhase.SETUP.value == "setup"

    def test_token_status_values(self):
        """Test TokenStatus enum values."""
        from armadabench_mcp.models.game_state import TokenStatus
        assert len(TokenStatus) == 3
        assert TokenStatus.READY.value == "ready"

    def test_command_dial_values(self):
        """Test CommandDial enum values."""
        from armadabench_mcp.models.game_state import CommandDial
        assert len(CommandDial) == 4
        assert CommandDial.NAVIGATE.value == "navigate"

    def test_obstacle_type_values(self):
        """Test ObstacleType enum values."""
        from armadabench_mcp.models.game_state import ObstacleType
        assert len(ObstacleType) == 4
        assert ObstacleType.ASTEROID.value == "asteroid"
