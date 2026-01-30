"""
Tests for card tools.

Tests the CardTools class which provides MCP tools for
querying the Star Wars Armada card database.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from armadabench_mcp.tools.card_tools import CardTools
from armadabench_mcp.clients.isb_client import (
    ISBClient,
    SearchResult,
    Ship,
    Squadron,
    Upgrade,
    Objective,
    FleetValidationResult,
    FleetPoints,
    FleetError,
)


class TestCardToolsInit:
    """Tests for CardTools initialization."""

    def test_init_without_client(self):
        """Test creating CardTools without a client."""
        tools = CardTools()
        assert tools._client is None
        assert tools._owns_client is True

    def test_init_with_url(self):
        """Test creating CardTools with a URL string."""
        tools = CardTools("https://api.example.com")
        assert tools._client is not None
        assert tools._owns_client is True

    def test_init_with_client(self):
        """Test creating CardTools with an existing client."""
        mock_client = MagicMock(spec=ISBClient)
        tools = CardTools(mock_client)
        assert tools._client is mock_client
        assert tools._owns_client is False


class TestCardToolsSearchCards:
    """Tests for the search_cards method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ISB client."""
        client = AsyncMock(spec=ISBClient)
        return client

    @pytest.fixture
    def card_tools(self, mock_client):
        """Create CardTools with a mock client."""
        tools = CardTools(mock_client)
        return tools

    @pytest.mark.asyncio
    async def test_search_cards_basic(self, card_tools, mock_client):
        """Test basic card search."""
        mock_client.search.return_value = SearchResult(
            success=True,
            results=[
                {
                    "id": "imperial-i-class-star-destroyer",
                    "name": "Imperial I-class Star Destroyer",
                    "type": "ship",
                    "faction": "empire",
                    "points": 110,
                    "unique": False,
                    "size": "large",
                    "hull": 11,
                }
            ],
            total_count=1,
            returned_count=1,
            query_time_ms=15.5,
        )

        result = await card_tools.search_cards(query="star destroyer")

        assert result["success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "Imperial I-class Star Destroyer"
        assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_search_cards_with_filters(self, card_tools, mock_client):
        """Test card search with filters."""
        mock_client.search.return_value = SearchResult(
            success=True,
            results=[],
            total_count=0,
            returned_count=0,
            query_time_ms=10.0,
        )

        await card_tools.search_cards(
            query="vader",
            type="upgrade",
            faction="empire",
            points="<30",
            unique=True,
            format="standard",
            limit=10,
        )

        mock_client.search.assert_called_once_with(
            query="vader",
            type="upgrade",
            faction="empire",
            points="<30",
            unique=True,
            format="standard",
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_search_cards_simplifies_ship_results(self, card_tools, mock_client):
        """Test that ship results include size and hull."""
        mock_client.search.return_value = SearchResult(
            success=True,
            results=[
                {
                    "id": "victory-ii",
                    "name": "Victory II-class Star Destroyer",
                    "type": "ship",
                    "faction": "empire",
                    "points": 85,
                    "unique": False,
                    "size": "medium",
                    "hull": 8,
                }
            ],
            total_count=1,
            returned_count=1,
            query_time_ms=5.0,
        )

        result = await card_tools.search_cards(query="victory")

        assert result["results"][0]["size"] == "medium"
        assert result["results"][0]["hull"] == 8

    @pytest.mark.asyncio
    async def test_search_cards_simplifies_squadron_results(self, card_tools, mock_client):
        """Test that squadron results include ace_name and abilities."""
        mock_client.search.return_value = SearchResult(
            success=True,
            results=[
                {
                    "id": "darth-vader-squadron",
                    "name": "TIE Advanced Squadron",
                    "ace_name": "Darth Vader",
                    "type": "squadron",
                    "faction": "empire",
                    "points": 21,
                    "unique": True,
                    "abilities": ["Escort", "Counter 1"],
                }
            ],
            total_count=1,
            returned_count=1,
            query_time_ms=5.0,
        )

        result = await card_tools.search_cards(query="vader")

        assert result["results"][0]["ace_name"] == "Darth Vader"
        assert "Escort" in result["results"][0]["abilities"]

    @pytest.mark.asyncio
    async def test_search_cards_simplifies_upgrade_results(self, card_tools, mock_client):
        """Test that upgrade results include upgrade_type."""
        mock_client.search.return_value = SearchResult(
            success=True,
            results=[
                {
                    "id": "gunnery-team",
                    "name": "Gunnery Team",
                    "type": "upgrade",
                    "upgrade_type": "weapons-team",
                    "faction": None,
                    "points": 7,
                    "unique": False,
                }
            ],
            total_count=1,
            returned_count=1,
            query_time_ms=5.0,
        )

        result = await card_tools.search_cards(query="gunnery")

        assert result["results"][0]["upgrade_type"] == "weapons-team"


class TestCardToolsGetCardDetails:
    """Tests for the get_card_details method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ISB client."""
        client = AsyncMock(spec=ISBClient)
        return client

    @pytest.fixture
    def card_tools(self, mock_client):
        """Create CardTools with a mock client."""
        tools = CardTools(mock_client)
        return tools

    @pytest.mark.asyncio
    async def test_get_card_details_success(self, card_tools, mock_client):
        """Test successful card detail retrieval."""
        mock_client.get_card.return_value = {
            "id": "darth-vader-commander",
            "name": "Darth Vader",
            "type": "upgrade",
            "upgrade_type": "commander",
            "faction": "empire",
            "points": 36,
            "unique": True,
            "ability": "While a friendly ship is attacking...",
        }

        result = await card_tools.get_card_details("darth-vader-commander")

        assert result["success"] is True
        assert result["card"]["name"] == "Darth Vader"

    @pytest.mark.asyncio
    async def test_get_card_details_not_found(self, card_tools, mock_client):
        """Test card not found."""
        mock_client.get_card.side_effect = ValueError("Card not found: invalid-id")

        result = await card_tools.get_card_details("invalid-id")

        assert result["success"] is False
        assert "not found" in result["error"]


class TestCardToolsListMethods:
    """Tests for the list_* methods."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ISB client."""
        client = AsyncMock(spec=ISBClient)
        return client

    @pytest.fixture
    def card_tools(self, mock_client):
        """Create CardTools with a mock client."""
        tools = CardTools(mock_client)
        return tools

    @pytest.mark.asyncio
    async def test_list_ships(self, card_tools, mock_client):
        """Test listing ships."""
        mock_client.list_ships.return_value = [
            Ship(
                id="victory-ii",
                name="Victory II-class Star Destroyer",
                faction="empire",
                points=85,
                size="medium",
                hull=8,
                command=3,
                squadron=3,
                engineering=4,
                upgrade_slots=["commander", "officer", "turbolaser"],
            )
        ]

        result = await card_tools.list_ships(faction="empire", size="medium")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["ships"][0]["name"] == "Victory II-class Star Destroyer"

    @pytest.mark.asyncio
    async def test_list_squadrons(self, card_tools, mock_client):
        """Test listing squadrons."""
        mock_client.list_squadrons.return_value = [
            Squadron(
                id="tie-fighter",
                name="TIE Fighter Squadron",
                ace_name=None,
                faction="empire",
                points=8,
                unique=False,
                hull=3,
                speed=4,
                abilities=["Swarm"],
            )
        ]

        result = await card_tools.list_squadrons(faction="empire")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["squadrons"][0]["name"] == "TIE Fighter Squadron"

    @pytest.mark.asyncio
    async def test_list_upgrades(self, card_tools, mock_client):
        """Test listing upgrades."""
        mock_client.list_upgrades.return_value = [
            Upgrade(
                id="gunnery-team",
                name="Gunnery Team",
                upgrade_type="weapons-team",
                faction=None,
                points=7,
                unique=False,
                ability="You can attack from the same hull zone more than once per activation.",
            )
        ]

        result = await card_tools.list_upgrades(upgrade_type="weapons-team")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["upgrades"][0]["name"] == "Gunnery Team"

    @pytest.mark.asyncio
    async def test_list_upgrades_truncates_long_ability(self, card_tools, mock_client):
        """Test that long ability text is truncated."""
        long_ability = "A" * 300
        mock_client.list_upgrades.return_value = [
            Upgrade(
                id="test-upgrade",
                name="Test Upgrade",
                upgrade_type="officer",
                faction=None,
                points=5,
                unique=False,
                ability=long_ability,
            )
        ]

        result = await card_tools.list_upgrades()

        # Should be truncated to 200 chars + "..."
        assert len(result["upgrades"][0]["ability"]) == 203
        assert result["upgrades"][0]["ability"].endswith("...")

    @pytest.mark.asyncio
    async def test_list_objectives(self, card_tools, mock_client):
        """Test listing objectives."""
        mock_client.list_objectives.return_value = [
            Objective(
                id="advanced-gunnery",
                name="Advanced Gunnery",
                objective_type="assault",
                points=0,
            )
        ]

        result = await card_tools.list_objectives(objective_type="assault")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["objectives"][0]["name"] == "Advanced Gunnery"


class TestCardToolsValidateFleet:
    """Tests for the validate_fleet method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ISB client."""
        client = AsyncMock(spec=ISBClient)
        return client

    @pytest.fixture
    def card_tools(self, mock_client):
        """Create CardTools with a mock client."""
        tools = CardTools(mock_client)
        return tools

    @pytest.mark.asyncio
    async def test_validate_fleet_valid(self, card_tools, mock_client):
        """Test validating a valid fleet."""
        mock_client.validate_fleet.return_value = FleetValidationResult(
            success=True,
            valid=True,
            points=FleetPoints(
                ships=150,
                squadrons=50,
                total=200,
                limit=400,
                remaining=200,
            ),
            errors=[],
            warnings=[],
        )

        result = await card_tools.validate_fleet(
            faction="empire",
            ships=[{"id": "victory-ii", "upgrades": ["darth-vader-commander"]}],
            squadrons=["tie-fighter-squadron", "tie-fighter-squadron"],
        )

        assert result["success"] is True
        assert result["valid"] is True
        assert result["points"]["total"] == 200
        assert result["points"]["remaining"] == 200
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_fleet_invalid(self, card_tools, mock_client):
        """Test validating an invalid fleet."""
        mock_client.validate_fleet.return_value = FleetValidationResult(
            success=True,
            valid=False,
            points=FleetPoints(
                ships=450,
                squadrons=50,
                total=500,
                limit=400,
                remaining=-100,
            ),
            errors=[
                FleetError(
                    type="point_limit",
                    message="Fleet exceeds point limit (500/400)",
                    location="fleet",
                )
            ],
            warnings=[],
        )

        result = await card_tools.validate_fleet(
            faction="empire",
            ships=[{"id": "isd-ii", "upgrades": []}],
            squadrons=[],
        )

        assert result["success"] is True
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["type"] == "point_limit"


class TestCardToolsGetUpgradeTypes:
    """Tests for the get_upgrade_types method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock ISB client."""
        client = AsyncMock(spec=ISBClient)
        return client

    @pytest.fixture
    def card_tools(self, mock_client):
        """Create CardTools with a mock client."""
        tools = CardTools(mock_client)
        return tools

    @pytest.mark.asyncio
    async def test_get_upgrade_types(self, card_tools, mock_client):
        """Test getting upgrade types."""
        mock_client.list_upgrade_types.return_value = [
            "commander",
            "officer",
            "weapons-team",
            "turbolaser",
            "ion-cannons",
            "ordnance",
        ]

        result = await card_tools.get_upgrade_types()

        assert result["success"] is True
        assert "commander" in result["upgrade_types"]
        assert "turbolaser" in result["upgrade_types"]


class TestCardToolsClose:
    """Tests for the close method."""

    @pytest.mark.asyncio
    async def test_close_owned_client(self):
        """Test closing an owned client."""
        mock_client = AsyncMock(spec=ISBClient)
        tools = CardTools(mock_client)
        tools._owns_client = True

        await tools.close()

        mock_client.close.assert_called_once()
        assert tools._client is None

    @pytest.mark.asyncio
    async def test_close_not_owned_client(self):
        """Test that non-owned client is not closed."""
        mock_client = AsyncMock(spec=ISBClient)
        tools = CardTools(mock_client)
        tools._owns_client = False

        await tools.close()

        mock_client.close.assert_not_called()
