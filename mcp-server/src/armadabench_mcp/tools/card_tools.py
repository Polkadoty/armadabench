"""
Card Database Tools

MCP tools for querying the Star Wars Armada card database.
These tools are exposed to LLMs for card lookup and fleet building.
"""

from __future__ import annotations

from typing import Any
import structlog

from ..clients.isb_client import ISBClient, Fleet, FleetShip

logger = structlog.get_logger()


class CardTools:
    """
    MCP tools for querying card data.

    These tools wrap the ISB API client and provide a clean interface
    for LLMs to search for cards, get details, and validate fleets.
    """

    def __init__(self, client_or_url: ISBClient | str | None = None):
        """
        Initialize card tools.

        Args:
            client_or_url: ISB API client instance, base URL string, or None for default.
        """
        if isinstance(client_or_url, str):
            self._client = ISBClient(base_url=client_or_url)
            self._owns_client = True
        elif client_or_url is None:
            self._client = None
            self._owns_client = True
        else:
            self._client = client_or_url
            self._owns_client = False

    async def _get_client(self) -> ISBClient:
        """Get or create the API client."""
        if self._client is None:
            self._client = ISBClient()
        return self._client

    async def close(self) -> None:
        """Close the client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.close()
            self._client = None

    # Tool definitions follow MCP patterns
    async def search_cards(
        self,
        query: str = "",
        type: str | None = None,
        faction: str | None = None,
        points: str | None = None,
        unique: bool | None = None,
        format: str = "legacy",
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for cards across all types (ships, squadrons, upgrades, objectives).

        Use this tool to find cards by name, filter by faction, point cost, or type.

        Args:
            query: Text to search for in card names (e.g., "vader", "star destroyer")
            type: Filter by card type: "ship", "squadron", "upgrade", or "objective"
            faction: Filter by faction: "empire", "rebel", "republic", "separatist"
            points: Point cost filter. Examples: "50-100", ">50", "<=30", "25"
            unique: If true, only return unique cards. If false, only non-unique.
            format: Game format: "legacy", "standard", "nexus" (default: "legacy")
            limit: Maximum number of results to return (default: 20)

        Returns:
            Dictionary with:
            - success: Whether the search succeeded
            - results: List of matching cards with basic info
            - total_count: Total number of matches
            - query_time_ms: How long the search took

        Example:
            To find Imperial commanders under 30 points:
            search_cards(type="upgrade", faction="empire", points="<30")

            To find ships with "destroyer" in the name:
            search_cards(query="destroyer", type="ship")
        """
        client = await self._get_client()
        logger.info("search_cards", query=query, type=type, faction=faction, points=points)

        result = await client.search(
            query=query,
            type=type,
            faction=faction,
            points=points,
            unique=unique,
            format=format,
            limit=limit,
        )

        # Simplify results for LLM consumption
        simplified_results = []
        for card in result.results:
            simplified = {
                "id": card.get("id"),
                "name": card.get("name"),
                "type": card.get("type"),
                "faction": card.get("faction"),
                "points": card.get("points"),
                "unique": card.get("unique", False),
            }
            # Add type-specific fields
            if card.get("type") == "ship":
                simplified["size"] = card.get("size")
                simplified["hull"] = card.get("hull")
            elif card.get("type") == "squadron":
                simplified["ace_name"] = card.get("ace_name")
                simplified["abilities"] = card.get("abilities", [])
            elif card.get("type") == "upgrade":
                simplified["upgrade_type"] = card.get("upgrade_type")

            simplified_results.append(simplified)

        return {
            "success": result.success,
            "results": simplified_results,
            "total_count": result.total_count,
            "returned_count": result.returned_count,
            "query_time_ms": result.query_time_ms,
        }

    async def get_card_details(
        self,
        card_id: str,
        format: str = "legacy",
    ) -> dict[str, Any]:
        """
        Get complete details for a specific card by its ID.

        Use this tool when you need full information about a card,
        including abilities, upgrade slots, armament, etc.

        Args:
            card_id: The unique identifier for the card (e.g., "imperial-star-destroyer-i")
            format: Game format: "legacy", "standard", "nexus" (default: "legacy")

        Returns:
            Complete card data including all stats and abilities.

        Example:
            get_card_details("darth-vader-commander")
            get_card_details("imperial-i-class-star-destroyer")
        """
        client = await self._get_client()
        logger.info("get_card_details", card_id=card_id)

        try:
            card = await client.get_card(card_id, format=format)
            return {"success": True, "card": card}
        except ValueError as e:
            return {"success": False, "error": str(e)}

    async def list_ships(
        self,
        faction: str | None = None,
        size: str | None = None,
        points: str | None = None,
        format: str = "legacy",
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List all available ships, optionally filtered by faction or size.

        Use this tool to see what ships are available for fleet building.

        Args:
            faction: Filter by faction: "empire", "rebel", "republic", "separatist"
            size: Filter by ship size: "small", "medium", "large", "huge"
            points: Point cost filter (e.g., "50-100", ">80")
            format: Game format (default: "legacy")
            limit: Maximum results (default: 50)

        Returns:
            List of ships with key stats.

        Example:
            list_ships(faction="empire", size="large")
            list_ships(faction="rebel", points="<60")
        """
        client = await self._get_client()
        logger.info("list_ships", faction=faction, size=size, points=points)

        ships = await client.list_ships(
            faction=faction,
            size=size,
            points=points,
            format=format,
            limit=limit,
        )

        return {
            "success": True,
            "ships": [
                {
                    "id": s.id,
                    "name": s.name,
                    "faction": s.faction,
                    "points": s.points,
                    "size": s.size,
                    "hull": s.hull,
                    "command": s.command,
                    "squadron": s.squadron,
                    "engineering": s.engineering,
                    "upgrade_slots": s.upgrade_slots,
                }
                for s in ships
            ],
            "count": len(ships),
        }

    async def list_squadrons(
        self,
        faction: str | None = None,
        ace: bool | None = None,
        unique: bool | None = None,
        points: str | None = None,
        format: str = "legacy",
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List all available squadrons, optionally filtered.

        Use this tool to see what squadrons are available for fleet building.

        Args:
            faction: Filter by faction: "empire", "rebel", "republic", "separatist"
            ace: If true, only show ace (unique named) squadrons
            unique: If true, only unique squadrons
            points: Point cost filter
            format: Game format (default: "legacy")
            limit: Maximum results (default: 50)

        Returns:
            List of squadrons with key stats.

        Example:
            list_squadrons(faction="empire", ace=True)
            list_squadrons(faction="rebel", points="<15")
        """
        client = await self._get_client()
        logger.info("list_squadrons", faction=faction, ace=ace)

        squadrons = await client.list_squadrons(
            faction=faction,
            ace=ace,
            unique=unique,
            points=points,
            format=format,
            limit=limit,
        )

        return {
            "success": True,
            "squadrons": [
                {
                    "id": s.id,
                    "name": s.name,
                    "ace_name": s.ace_name,
                    "faction": s.faction,
                    "points": s.points,
                    "unique": s.unique,
                    "hull": s.hull,
                    "speed": s.speed,
                    "abilities": s.abilities,
                }
                for s in squadrons
            ],
            "count": len(squadrons),
        }

    async def list_upgrades(
        self,
        faction: str | None = None,
        upgrade_type: str | None = None,
        unique: bool | None = None,
        points: str | None = None,
        format: str = "legacy",
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        List all available upgrades, optionally filtered.

        Use this tool to find upgrades for ships in your fleet.

        Args:
            faction: Filter by faction (some upgrades are faction-specific)
            upgrade_type: Filter by slot type: "commander", "officer", "weapons-team",
                         "offensive-retro", "defensive-retro", "turbolaser",
                         "ion-cannons", "ordnance", "title", etc.
            unique: If true, only unique upgrades
            points: Point cost filter
            format: Game format (default: "legacy")
            limit: Maximum results (default: 100)

        Returns:
            List of upgrades with key info.

        Example:
            list_upgrades(faction="empire", upgrade_type="commander")
            list_upgrades(upgrade_type="turbolaser", points="<10")
        """
        client = await self._get_client()
        logger.info("list_upgrades", faction=faction, upgrade_type=upgrade_type)

        upgrades = await client.list_upgrades(
            faction=faction,
            upgrade_type=upgrade_type,
            unique=unique,
            points=points,
            format=format,
            limit=limit,
        )

        return {
            "success": True,
            "upgrades": [
                {
                    "id": u.id,
                    "name": u.name,
                    "upgrade_type": u.upgrade_type,
                    "faction": u.faction,
                    "points": u.points,
                    "unique": u.unique,
                    "ability": u.ability[:200] + "..." if len(u.ability) > 200 else u.ability,
                }
                for u in upgrades
            ],
            "count": len(upgrades),
        }

    async def list_objectives(
        self,
        objective_type: str | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """
        List all available objectives.

        Use this tool to see objectives for fleet building.

        Args:
            objective_type: Filter by type: "assault", "defense", "navigation"
            limit: Maximum results (default: 30)

        Returns:
            List of objectives.

        Example:
            list_objectives(objective_type="assault")
        """
        client = await self._get_client()
        logger.info("list_objectives", objective_type=objective_type)

        objectives = await client.list_objectives(
            objective_type=objective_type,
            limit=limit,
        )

        return {
            "success": True,
            "objectives": [
                {
                    "id": o.id,
                    "name": o.name,
                    "objective_type": o.objective_type,
                    "points": o.points,
                }
                for o in objectives
            ],
            "count": len(objectives),
        }

    async def validate_fleet(
        self,
        faction: str,
        ships: list[dict[str, Any]],
        squadrons: list[str],
        format: str = "legacy",
        point_limit: int = 400,
    ) -> dict[str, Any]:
        """
        Validate a fleet composition for legality.

        Use this tool to check if a fleet is legal before finalizing it.
        It checks point limits, unique card restrictions, upgrade slot compatibility, etc.

        Args:
            faction: Fleet faction: "empire", "rebel", "republic", "separatist"
            ships: List of ships, each with format: {"id": "ship-id", "upgrades": ["upgrade-id", ...]}
            squadrons: List of squadron IDs
            format: Game format (default: "legacy")
            point_limit: Point limit for the fleet (default: 400)

        Returns:
            Validation result with:
            - valid: Whether the fleet is legal
            - points: Point breakdown (ships, squadrons, total)
            - errors: List of errors that make the fleet illegal
            - warnings: List of warnings (legal but suboptimal)

        Example:
            validate_fleet(
                faction="empire",
                ships=[
                    {"id": "imperial-i-class-star-destroyer", "upgrades": ["darth-vader-commander"]}
                ],
                squadrons=["tie-fighter-squadron", "tie-fighter-squadron"],
                point_limit=400
            )
        """
        client = await self._get_client()
        logger.info("validate_fleet", faction=faction, num_ships=len(ships), num_squadrons=len(squadrons))

        fleet = Fleet(
            faction=faction,
            ships=[FleetShip(**s) for s in ships],
            squadrons=squadrons,
        )

        result = await client.validate_fleet(
            fleet=fleet,
            format=format,
            point_limit=point_limit,
        )

        return {
            "success": result.success,
            "valid": result.valid,
            "points": {
                "ships": result.points.ships,
                "squadrons": result.points.squadrons,
                "total": result.points.total,
                "limit": result.points.limit,
                "remaining": result.points.remaining,
            },
            "errors": [{"type": e.type, "message": e.message, "location": e.location} for e in result.errors],
            "warnings": [{"type": w.type, "message": w.message, "location": w.location} for w in result.warnings],
        }

    async def get_upgrade_types(self, format: str = "legacy") -> dict[str, Any]:
        """
        Get list of all upgrade slot types.

        Use this to understand what types of upgrades exist.

        Args:
            format: Game format (default: "legacy")

        Returns:
            List of upgrade type names (e.g., "commander", "officer", "turbolaser")
        """
        client = await self._get_client()
        types = await client.list_upgrade_types(format=format)
        return {"success": True, "upgrade_types": types}
