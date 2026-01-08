"""
ISB API Client

Python client for the ISB (Imperial Security Bureau) API that provides
Star Wars Armada card data for the ArmadaBench benchmark.

API documentation: https://api.swarmada.wiki/api/mcp/schema
"""

from __future__ import annotations

import httpx
from typing import Any, Literal
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


# Response Models
class DicePool(BaseModel):
    """Dice pool representation (red, blue, black)."""
    red: int = 0
    blue: int = 0
    black: int = 0


class ShieldValues(BaseModel):
    """Shield values by hull zone."""
    front: int
    left: int
    right: int
    rear: int


class DefenseTokens(BaseModel):
    """Defense token counts."""
    scatter: int = 0
    evade: int = 0
    brace: int = 0
    redirect: int = 0
    contain: int = 0
    salvo: int = 0


class ShipArmament(BaseModel):
    """Ship armament by hull zone."""
    front: DicePool
    left: DicePool
    right: DicePool
    rear: DicePool
    anti_squadron: DicePool


class Ship(BaseModel):
    """Ship card data."""
    id: str
    chassis_id: str
    name: str
    type: Literal["ship"] = "ship"
    faction: str
    points: int
    unique: bool = False
    size: str
    hull: int
    speed_chart: dict[str, list[int]]
    shields: ShieldValues
    defense_tokens: DefenseTokens
    command: int
    squadron: int
    engineering: int
    armament: ShipArmament
    upgrade_slots: list[str]
    nicknames: list[str] = Field(default_factory=list)
    image_url: str | None = None


class SquadronArmament(BaseModel):
    """Squadron armament."""
    anti_squadron: DicePool
    anti_ship: DicePool


class SquadronDefenseTokens(BaseModel):
    """Squadron defense tokens (limited set)."""
    scatter: int = 0
    evade: int = 0
    brace: int = 0


class Squadron(BaseModel):
    """Squadron card data."""
    id: str
    name: str
    ace_name: str | None = None
    type: Literal["squadron"] = "squadron"
    squadron_type: str
    faction: str
    points: int
    unique: bool = False
    ace: bool = False
    irregular: bool = False
    hull: int
    speed: int
    defense_tokens: SquadronDefenseTokens
    armament: SquadronArmament
    abilities: list[str] = Field(default_factory=list)
    ability_text: str = ""
    unique_class: list[str] = Field(default_factory=list)
    nicknames: list[str] = Field(default_factory=list)
    image_url: str | None = None


class UpgradeRestrictions(BaseModel):
    """Upgrade card restrictions."""
    traits: list[str] = Field(default_factory=list)
    size: list[str] = Field(default_factory=list)
    disqualified_upgrades: list[str] = Field(default_factory=list)
    disabled_upgrades: list[str] = Field(default_factory=list)
    enabled_upgrades: list[str] = Field(default_factory=list)
    flagship: bool = False
    bound_ship: str | None = None


class Upgrade(BaseModel):
    """Upgrade card data."""
    id: str
    name: str
    type: Literal["upgrade"] = "upgrade"
    upgrade_type: str
    faction: list[str]
    points: int
    unique: bool = False
    modification: bool = False
    ability: str = ""
    restrictions: UpgradeRestrictions
    exhaust: dict | None = None
    unique_class: list[str] = Field(default_factory=list)
    nicknames: list[str] = Field(default_factory=list)
    rules: list[dict] = Field(default_factory=list)
    image_url: str | None = None


class Objective(BaseModel):
    """Objective card data."""
    id: str
    name: str
    type: Literal["objective"] = "objective"
    objective_type: str
    points: int = 0
    setup: str = ""
    special_rule: str = ""
    end_of_round: str = ""
    end_of_game: str = ""
    image_url: str | None = None


class FleetPoints(BaseModel):
    """Fleet point breakdown."""
    ships: int
    squadrons: int
    total: int
    limit: int
    remaining: int


class FleetError(BaseModel):
    """Fleet validation error."""
    type: str
    message: str
    location: str


class FleetValidationResult(BaseModel):
    """Result of fleet validation."""
    success: bool
    valid: bool
    points: FleetPoints
    errors: list[FleetError]
    warnings: list[FleetError]


class SearchResult(BaseModel):
    """Search result container."""
    success: bool
    query: dict
    results: list[dict]
    total_count: int
    returned_count: int
    query_time_ms: int


# Fleet building models
class FleetShip(BaseModel):
    """Ship in a fleet with upgrades."""
    id: str
    upgrades: list[str] = Field(default_factory=list)


class Fleet(BaseModel):
    """Fleet composition for validation."""
    faction: str
    ships: list[FleetShip] = Field(default_factory=list)
    squadrons: list[str] = Field(default_factory=list)


class ISBClient:
    """
    Client for the ISB API (Imperial Security Bureau).

    Provides access to Star Wars Armada card data including ships,
    squadrons, upgrades, and objectives.

    Example:
        ```python
        async with ISBClient() as client:
            ships = await client.list_ships(faction="empire")
            vader = await client.search("vader", type="upgrade")
        ```
    """

    DEFAULT_BASE_URL = "https://api.swarmada.wiki/api/mcp"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        default_format: str = "legacy"
    ):
        """
        Initialize the ISB API client.

        Args:
            base_url: Base URL for the API. Defaults to api.swarmada.wiki
            timeout: Request timeout in seconds
            default_format: Default game format (legacy, standard, nexus, etc.)
        """
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.default_format = default_format
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "ISBClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating one if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}/{endpoint}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _post(self, endpoint: str, data: dict) -> dict:
        """Make a POST request to the API."""
        url = f"{self.base_url}/{endpoint}"
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    # Schema and metadata
    async def get_schema(self) -> dict:
        """
        Get the API schema with tool documentation.

        Returns:
            API schema including available tools and parameters
        """
        return await self._get("schema")

    # Search
    async def search(
        self,
        query: str = "",
        type: str | None = None,
        faction: str | None = None,
        points: str | None = None,
        unique: bool | None = None,
        format: str | None = None,
        limit: int = 50,
        include_ships: bool = True,
        include_squadrons: bool = True,
        include_upgrades: bool = True,
        include_objectives: bool = True,
    ) -> SearchResult:
        """
        Search for cards across all types.

        Args:
            query: Text search in card names
            type: Filter by card type (ship, squadron, upgrade, objective)
            faction: Filter by faction (empire, rebel, republic, separatist)
            points: Point filter (e.g., "50-100", ">50", "<=30")
            unique: Filter by unique status
            format: Game format (legacy, standard, nexus, etc.)
            limit: Maximum results to return
            include_ships: Include ships in results
            include_squadrons: Include squadrons in results
            include_upgrades: Include upgrades in results
            include_objectives: Include objectives in results

        Returns:
            SearchResult with matching cards
        """
        params = {
            "query": query,
            "format": format or self.default_format,
            "limit": str(limit),
            "include_ships": str(include_ships).lower(),
            "include_squadrons": str(include_squadrons).lower(),
            "include_upgrades": str(include_upgrades).lower(),
            "include_objectives": str(include_objectives).lower(),
        }
        if type:
            params["type"] = type
        if faction:
            params["faction"] = faction
        if points:
            params["points"] = points
        if unique is not None:
            params["unique"] = str(unique).lower()

        data = await self._get("search", params)
        return SearchResult(**data)

    # Get specific card
    async def get_card(self, card_id: str, format: str | None = None) -> dict:
        """
        Get full details for a specific card by ID.

        Args:
            card_id: The card identifier
            format: Game format

        Returns:
            Card details dict
        """
        params = {"format": format or self.default_format}
        data = await self._get(f"cards/{card_id}", params)
        if data.get("success"):
            return data.get("card", {})
        raise ValueError(f"Card not found: {card_id}")

    # Ships
    async def list_ships(
        self,
        faction: str | None = None,
        size: str | None = None,
        points: str | None = None,
        format: str | None = None,
        limit: int = 100,
    ) -> list[Ship]:
        """
        List all ships with optional filters.

        Args:
            faction: Filter by faction
            size: Filter by ship size (small, medium, large, huge)
            points: Point filter
            format: Game format
            limit: Maximum results

        Returns:
            List of Ship objects
        """
        params = {
            "format": format or self.default_format,
            "limit": str(limit),
        }
        if faction:
            params["faction"] = faction
        if size:
            params["size"] = size
        if points:
            params["points"] = points

        data = await self._get("ships", params)
        return [Ship(**ship) for ship in data.get("ships", [])]

    async def get_ship(self, ship_id: str, format: str | None = None) -> Ship:
        """Get a specific ship by ID."""
        card = await self.get_card(ship_id, format)
        return Ship(**card)

    # Squadrons
    async def list_squadrons(
        self,
        faction: str | None = None,
        ace: bool | None = None,
        unique: bool | None = None,
        points: str | None = None,
        format: str | None = None,
        limit: int = 100,
    ) -> list[Squadron]:
        """
        List all squadrons with optional filters.

        Args:
            faction: Filter by faction
            ace: Filter for ace squadrons
            unique: Filter by unique status
            points: Point filter
            format: Game format
            limit: Maximum results

        Returns:
            List of Squadron objects
        """
        params = {
            "format": format or self.default_format,
            "limit": str(limit),
        }
        if faction:
            params["faction"] = faction
        if ace is not None:
            params["ace"] = str(ace).lower()
        if unique is not None:
            params["unique"] = str(unique).lower()
        if points:
            params["points"] = points

        data = await self._get("squadrons", params)
        return [Squadron(**sq) for sq in data.get("squadrons", [])]

    async def get_squadron(self, squadron_id: str, format: str | None = None) -> Squadron:
        """Get a specific squadron by ID."""
        card = await self.get_card(squadron_id, format)
        return Squadron(**card)

    # Upgrades
    async def list_upgrades(
        self,
        faction: str | None = None,
        upgrade_type: str | None = None,
        unique: bool | None = None,
        points: str | None = None,
        format: str | None = None,
        limit: int = 200,
    ) -> list[Upgrade]:
        """
        List all upgrades with optional filters.

        Args:
            faction: Filter by faction
            upgrade_type: Filter by upgrade type (commander, officer, etc.)
            unique: Filter by unique status
            points: Point filter
            format: Game format
            limit: Maximum results

        Returns:
            List of Upgrade objects
        """
        params = {
            "format": format or self.default_format,
            "limit": str(limit),
        }
        if faction:
            params["faction"] = faction
        if upgrade_type:
            params["upgrade_type"] = upgrade_type
        if unique is not None:
            params["unique"] = str(unique).lower()
        if points:
            params["points"] = points

        data = await self._get("upgrades", params)
        return [Upgrade(**up) for up in data.get("upgrades", [])]

    async def get_upgrade(self, upgrade_id: str, format: str | None = None) -> Upgrade:
        """Get a specific upgrade by ID."""
        card = await self.get_card(upgrade_id, format)
        return Upgrade(**card)

    async def list_upgrade_types(self, format: str | None = None) -> list[str]:
        """Get list of available upgrade slot types."""
        params = {"format": format or self.default_format}
        data = await self._get("upgrade-types", params)
        return data.get("upgrade_types", [])

    # Objectives
    async def list_objectives(
        self,
        objective_type: str | None = None,
        limit: int = 50,
    ) -> list[Objective]:
        """
        List all objectives with optional filters.

        Args:
            objective_type: Filter by objective type (assault, defense, navigation)
            limit: Maximum results

        Returns:
            List of Objective objects
        """
        params = {"limit": str(limit)}
        if objective_type:
            params["objective_type"] = objective_type

        data = await self._get("objectives", params)
        return [Objective(**obj) for obj in data.get("objectives", [])]

    async def get_objective(self, objective_id: str) -> Objective:
        """Get a specific objective by ID."""
        card = await self.get_card(objective_id)
        return Objective(**card)

    # Fleet validation
    async def validate_fleet(
        self,
        fleet: Fleet,
        format: str | None = None,
        point_limit: int = 400,
    ) -> FleetValidationResult:
        """
        Validate a fleet composition for legality.

        Args:
            fleet: Fleet composition to validate
            format: Game format
            point_limit: Point limit for validation

        Returns:
            FleetValidationResult with errors and warnings
        """
        data = await self._post("validate-fleet", {
            "fleet": fleet.model_dump(),
            "format": format or self.default_format,
            "point_limit": point_limit,
        })
        return FleetValidationResult(**data)

    # Convenience methods for fleet building
    async def find_commanders(self, faction: str, format: str | None = None) -> list[Upgrade]:
        """Find all commander upgrades for a faction."""
        return await self.list_upgrades(
            faction=faction,
            upgrade_type="commander",
            format=format
        )

    async def find_ship_upgrades(
        self,
        ship: Ship,
        format: str | None = None
    ) -> dict[str, list[Upgrade]]:
        """
        Find all upgrades that can be equipped on a ship.

        Args:
            ship: The ship to find upgrades for
            format: Game format

        Returns:
            Dict mapping upgrade slot type to available upgrades
        """
        all_upgrades = await self.list_upgrades(
            faction=ship.faction,
            format=format,
            limit=500
        )

        available: dict[str, list[Upgrade]] = {}
        for slot in ship.upgrade_slots:
            available[slot] = [
                up for up in all_upgrades
                if up.upgrade_type == slot
            ]

        return available
