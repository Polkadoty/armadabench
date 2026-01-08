"""
HTTP client for communicating with the Vassal Integration Java server.
"""

import httpx
from typing import Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ShipData(BaseModel):
    """Ship data from Vassal."""
    id: str
    name: str
    ship_type: Optional[str] = None
    faction: Optional[str] = None
    player_id: Optional[str] = None
    x: float
    y: float
    rotation: float = 0
    current_hull: int = 0
    max_hull: int = 0
    current_shields: dict[str, int] = {}
    max_shields: dict[str, int] = {}
    defense_tokens: list[dict] = []
    upgrades: list[dict] = []
    damage_cards: list[dict] = []
    activated: bool = False
    speed: int = 0
    command_dial: Optional[str] = None

    class Config:
        populate_by_name = True


class SquadronData(BaseModel):
    """Squadron data from Vassal."""
    id: str
    name: str
    squadron_type: Optional[str] = None
    faction: Optional[str] = None
    player_id: Optional[str] = None
    x: float
    y: float
    current_hull: int = 0
    max_hull: int = 0
    activated: bool = False
    engaged: bool = False
    keywords: list[str] = []
    speed: int = 0


class ObstacleData(BaseModel):
    """Obstacle data from Vassal."""
    id: str
    type: str
    x: float
    y: float
    rotation: float = 0
    width: float = 0
    height: float = 0


class TokenData(BaseModel):
    """Token data from Vassal."""
    id: str
    type: str
    x: float
    y: float
    owner: Optional[str] = None
    attached_to: Optional[str] = None


class ObjectiveData(BaseModel):
    """Objective data."""
    id: str
    name: str
    type: str
    text: Optional[str] = None
    victory_points: int = 0


class BoardState(BaseModel):
    """Complete board state from Vassal."""
    round_number: int = 1
    current_phase: str = "Unknown"
    active_player: Optional[str] = None
    ships: list[ShipData] = []
    squadrons: list[SquadronData] = []
    obstacles: list[ObstacleData] = []
    tokens: list[TokenData] = []
    objective: Optional[ObjectiveData] = None
    timestamp: int = 0


class VassalClient:
    """
    HTTP client for the Vassal Integration Java server.

    This client communicates with the Java REST API to access
    Vassal game state and execute actions.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> dict[str, Any]:
        """Make an HTTP request to the Vassal API."""
        url = f"{self.base_url}{path}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise

    async def health_check(self) -> dict[str, Any]:
        """Check if the Vassal server is healthy."""
        return await self._request("GET", "/api/health")

    async def is_connected(self) -> bool:
        """Check if we can connect to the Vassal server."""
        try:
            health = await self.health_check()
            return health.get("status") == "ok"
        except Exception:
            return False

    # Game State Methods

    async def get_board_state(self) -> BoardState:
        """Get the complete current board state."""
        data = await self._request("GET", "/api/state")
        return BoardState(**self._snake_case_keys(data))

    async def get_ship_details(self, ship_id: str) -> ShipData:
        """Get details for a specific ship."""
        data = await self._request("GET", f"/api/ship/{ship_id}")
        return ShipData(**self._snake_case_keys(data))

    async def get_squadron_details(self, squadron_id: str) -> SquadronData:
        """Get details for a specific squadron."""
        data = await self._request("GET", f"/api/squadron/{squadron_id}")
        return SquadronData(**self._snake_case_keys(data))

    # Screenshot Methods

    async def capture_screenshot(
        self,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> bytes:
        """Capture a screenshot of the board as PNG bytes."""
        params = {}
        if max_width:
            params["maxWidth"] = max_width
        if max_height:
            params["maxHeight"] = max_height

        url = f"{self.base_url}/api/screenshot"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.content

    async def capture_screenshot_base64(self) -> dict[str, Any]:
        """Capture a screenshot as base64 data URL."""
        return await self._request("GET", "/api/screenshot/base64")

    # Action Methods

    async def execute_move(
        self,
        piece_id: str,
        target_x: float,
        target_y: float,
        rotation: float = 0,
        validate_only: bool = False
    ) -> dict[str, Any]:
        """Execute a move action."""
        return await self._request(
            "POST",
            "/api/action/move",
            json={
                "pieceId": piece_id,
                "targetX": target_x,
                "targetY": target_y,
                "rotation": rotation,
                "validateOnly": validate_only
            }
        )

    async def execute_attack(
        self,
        attacker_id: str,
        defender_id: str,
        arc: str,
        range_band: str = "medium"
    ) -> dict[str, Any]:
        """Execute an attack action."""
        return await self._request(
            "POST",
            "/api/action/attack",
            json={
                "attackerId": attacker_id,
                "defenderId": defender_id,
                "arc": arc,
                "range": range_band
            }
        )

    # Game Lifecycle

    async def start_new_game(self) -> dict[str, Any]:
        """Start a new game."""
        return await self._request("POST", "/api/game/new")

    async def load_game(self, save_path: str) -> dict[str, Any]:
        """Load a saved game file."""
        return await self._request(
            "POST",
            "/api/game/load",
            json={"path": save_path}
        )

    # Utility Methods

    def _snake_case_keys(self, data: dict) -> dict:
        """Convert camelCase keys to snake_case."""
        import re

        def to_snake(name: str) -> str:
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        if isinstance(data, dict):
            return {to_snake(k): self._snake_case_keys(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._snake_case_keys(item) for item in data]
        else:
            return data
