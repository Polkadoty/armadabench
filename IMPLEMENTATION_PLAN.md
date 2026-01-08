# ArmadaBench - Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for building the ArmadaBench benchmarking suite. The plan is organized by component and development phase.

## Prerequisites

### Required Software
- Java 17+ (for Vassal integration)
- Python 3.10+ (for MCP server and benchmarking)
- Vassal Engine 3.7+ installed
- Star Wars Armada Vassal Module (latest version)
- Git for version control
- Docker (optional, for containerization)

### Required Access
- Star Forge API endpoint and documentation
- Star Forge card database schema
- Armada rules reference document (PDF or structured data)
- Vassal module source code access

---

## Phase 1: Foundation & Infrastructure

### 1.1 Project Structure Setup

**Goal**: Establish repository structure and build system

```
armadabench/
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── API_REFERENCE.md
├── vassal-integration/            # Java component
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── com/armadabench/vassal/
│   │   │   │       ├── VassalController.java
│   │   │   │       ├── GameStateReader.java
│   │   │   │       ├── ActionExecutor.java
│   │   │   │       ├── ScreenshotCapture.java
│   │   │   │       └── server/
│   │   │   │           └── VassalApiServer.java
│   │   │   └── resources/
│   │   └── test/
│   ├── pom.xml / build.gradle
│   └── README.md
├── mcp-server/                    # Python MCP server
│   ├── src/
│   │   ├── armadabench_mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py          # Main MCP server
│   │   │   ├── tools/             # MCP tool implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── game_state.py
│   │   │   │   ├── game_actions.py
│   │   │   │   ├── list_building.py
│   │   │   │   └── analysis.py
│   │   │   ├── resources/         # MCP resources
│   │   │   │   ├── __init__.py
│   │   │   │   └── card_database.py
│   │   │   ├── vassal_client.py   # Client for Vassal integration
│   │   │   ├── starforge_client.py
│   │   │   └── vision/
│   │   │       ├── __init__.py
│   │   │       ├── screenshot.py
│   │   │       └── annotation.py
│   │   └── tests/
│   ├── pyproject.toml
│   └── README.md
├── benchmarks/                    # Benchmarking framework
│   ├── src/
│   │   ├── armadabench/
│   │   │   ├── __init__.py
│   │   │   ├── test_runner.py
│   │   │   ├── metrics.py
│   │   │   ├── scenarios/
│   │   │   └── baselines/
│   │   └── tests/
│   ├── data/                      # Test scenarios
│   │   ├── rules_knowledge/
│   │   ├── list_building/
│   │   ├── spatial_reasoning/
│   │   ├── tactical_play/
│   │   └── full_games/
│   ├── pyproject.toml
│   └── README.md
├── docker/                        # Containerization
│   ├── Dockerfile.vassal
│   ├── Dockerfile.mcp
│   └── docker-compose.yml
└── README.md
```

**Tasks**:
- [ ] Create repository structure
- [ ] Initialize Java project (Maven/Gradle)
- [ ] Initialize Python projects (Poetry/pip)
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Configure linting and formatting (Ruff, Black, Checkstyle)
- [ ] Create Docker configuration

**Estimated Effort**: 1-2 days

---

### 1.2 Vassal Integration - Basic Setup

**Goal**: Launch Vassal programmatically and load Armada module

**Files to Create**:
- `VassalController.java` - Main controller for Vassal
- `VassalModuleLoader.java` - Load and initialize modules

**Key Implementation Steps**:

```java
// VassalController.java
public class VassalController {
    private GameModule gameModule;

    public void initialize(String modulePath) {
        // Load Vassal module
        // Initialize GameModule
        // Set up event listeners
    }

    public void loadGame(String savedGamePath) {
        // Load saved game state
    }

    public void startNewGame() {
        // Initialize new game
    }
}
```

**Vassal API Research Needed**:
- How to launch Vassal headless vs. with GUI
- How to programmatically load a module (.vmod file)
- How to initialize a new game vs. load saved game
- Event system for game state changes

**Tasks**:
- [ ] Research Vassal module loading API
- [ ] Implement basic Vassal launcher
- [ ] Test loading Armada module
- [ ] Verify module loads correctly with GUI
- [ ] Test headless mode (if available)
- [ ] Document any Vassal API quirks or limitations

**Estimated Effort**: 3-5 days

---

### 1.3 MCP Server - Basic Setup

**Goal**: Create functioning MCP server with one simple tool

**Files to Create**:
- `server.py` - Main MCP server entry point
- `tools/ping.py` - Simple test tool

**Key Implementation Steps**:

```python
# server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import Tool

app = Server("armadabench")

@app.tool()
async def ping() -> str:
    """Test tool to verify MCP server is running."""
    return "pong"

async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Tasks**:
- [ ] Set up Python environment with MCP SDK
- [ ] Create basic MCP server
- [ ] Implement test tool (ping)
- [ ] Test server with Claude Desktop or MCP client
- [ ] Set up logging (not stdout!)
- [ ] Create MCP server configuration file

**Estimated Effort**: 1-2 days

---

### 1.4 Star Forge Integration - API Client

**Goal**: Create Python client for existing Star Forge API

**Files to Create**:
- `starforge_client.py` - API client for Star Forge
- `models/cards.py` - Data models for cards

**Key Implementation Steps**:

```python
# starforge_client.py
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Ship:
    id: str
    name: str
    faction: str
    points: int
    hull: int
    shields: dict[str, int]  # front, left, right, rear
    # ... other attributes

class StarForgeClient:
    def __init__(self, api_base_url: str):
        self.base_url = api_base_url

    async def search_cards(
        self,
        query: str,
        card_type: Optional[str] = None,
        faction: Optional[str] = None
    ) -> List[dict]:
        """Search for cards matching criteria."""
        # Implement API call
        pass

    async def get_card_details(self, card_id: str) -> dict:
        """Get full details for a specific card."""
        # Implement API call
        pass

    async def validate_fleet(self, fleet_data: dict) -> dict:
        """Validate fleet composition and point total."""
        # Implement validation logic
        pass
```

**Information Needed from User**:
- Star Forge API endpoint URL
- API authentication method (if any)
- API documentation or OpenAPI spec
- Example JSON responses for ships, upgrades, squadrons
- Existing validation logic details

**Tasks**:
- [ ] Document Star Forge API endpoints
- [ ] Create data models for all card types
- [ ] Implement API client methods
- [ ] Add caching layer
- [ ] Write unit tests for client
- [ ] Create mock API for testing

**Estimated Effort**: 2-3 days

---

## Phase 2: Game State Reading

### 2.1 Vassal Game State Reader

**Goal**: Extract complete game state from Vassal

**Files to Create**:
- `GameStateReader.java` - Read current game state
- `models/BoardState.java` - Data model for game state

**Key Implementation Steps**:

```java
// GameStateReader.java
public class GameStateReader {
    private final GameModule gameModule;

    public BoardState getCurrentState() {
        BoardState state = new BoardState();

        // Get the main map
        Map map = gameModule.getComponentsOf(Map.class).get(0);

        // Iterate through all pieces
        for (GamePiece piece : map.getPieces()) {
            if (isShip(piece)) {
                state.addShip(extractShipData(piece));
            } else if (isSquadron(piece)) {
                state.addSquadron(extractSquadronData(piece));
            } else if (isObstacle(piece)) {
                state.addObstacle(extractObstacleData(piece));
            }
        }

        return state;
    }

    private ShipData extractShipData(GamePiece piece) {
        // Extract all relevant ship data:
        // - Position (x, y)
        // - Rotation
        // - Ship type/name
        // - Current hull
        // - Current shields (per zone)
        // - Defense tokens (available, spent)
        // - Upgrade cards
        // - Activation status
        // - Damage cards
    }
}
```

**Vassal API Challenges**:
- Identifying piece types (ships vs squadrons vs tokens)
- Extracting custom properties from pieces
- Reading shield dials and hull values
- Accessing stacked pieces (damage cards, tokens)
- Understanding Armada module's specific structure

**Tasks**:
- [ ] Research Armada module structure
- [ ] Map GamePiece types to Armada components
- [ ] Implement ship data extraction
- [ ] Implement squadron data extraction
- [ ] Implement obstacle/terrain extraction
- [ ] Extract defense tokens and upgrade cards
- [ ] Test with various game states
- [ ] Handle edge cases (destroyed ships, etc.)

**Estimated Effort**: 5-7 days

---

### 2.2 REST API for Game State

**Goal**: Expose game state via HTTP API

**Files to Create**:
- `server/VassalApiServer.java` - REST API server
- `server/handlers/GameStateHandler.java` - Handler for state requests

**Technology Options**:
1. **JAX-RS** (Jersey, RESTEasy) - Standard Java REST
2. **Spring Boot** - Full framework with REST support
3. **Javalin** - Lightweight Kotlin/Java web framework
4. **Vert.x** - Reactive, polyglot toolkit

**Recommended**: Javalin for simplicity

```java
// VassalApiServer.java
import io.javalin.Javalin;

public class VassalApiServer {
    private final GameStateReader stateReader;
    private final ActionExecutor actionExecutor;

    public void start(int port) {
        Javalin app = Javalin.create().start(port);

        // GET /api/state - Get current game state
        app.get("/api/state", ctx -> {
            BoardState state = stateReader.getCurrentState();
            ctx.json(state);
        });

        // GET /api/ship/{id} - Get specific ship details
        app.get("/api/ship/{id}", ctx -> {
            String shipId = ctx.pathParam("id");
            ShipData ship = stateReader.getShipById(shipId);
            ctx.json(ship);
        });

        // POST /api/action - Execute game action
        app.post("/api/action", ctx -> {
            GameAction action = ctx.bodyAsClass(GameAction.class);
            ActionResult result = actionExecutor.execute(action);
            ctx.json(result);
        });
    }
}
```

**Tasks**:
- [ ] Choose and integrate web framework
- [ ] Define REST API endpoints
- [ ] Implement serialization to JSON
- [ ] Add error handling
- [ ] Add request validation
- [ ] Document API with OpenAPI/Swagger
- [ ] Test with HTTP clients

**Estimated Effort**: 3-4 days

---

### 2.3 Python Client for Vassal API

**Goal**: Python client to communicate with Java Vassal integration

**Files to Create**:
- `vassal_client.py` - HTTP client for Vassal API

```python
# vassal_client.py
import httpx
from typing import Optional

class VassalClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_board_state(self) -> dict:
        """Get current complete board state."""
        response = await self.client.get(f"{self.base_url}/api/state")
        response.raise_for_status()
        return response.json()

    async def get_ship_details(self, ship_id: str) -> dict:
        """Get details for specific ship."""
        response = await self.client.get(
            f"{self.base_url}/api/ship/{ship_id}"
        )
        response.raise_for_status()
        return response.json()

    async def execute_action(self, action: dict) -> dict:
        """Execute a game action."""
        response = await self.client.post(
            f"{self.base_url}/api/action",
            json=action
        )
        response.raise_for_status()
        return response.json()
```

**Tasks**:
- [ ] Implement async HTTP client
- [ ] Add retry logic with exponential backoff
- [ ] Add connection pooling
- [ ] Handle timeouts gracefully
- [ ] Add client-side validation
- [ ] Create mock client for testing
- [ ] Write integration tests

**Estimated Effort**: 1-2 days

---

### 2.4 MCP Tools for Game State

**Goal**: Expose game state as MCP tools

**Files to Create**:
- `tools/game_state.py` - MCP tools for state queries

```python
# tools/game_state.py
from mcp import Tool
from ..vassal_client import VassalClient

class GameStateTools:
    def __init__(self, vassal_client: VassalClient):
        self.vassal = vassal_client

    @Tool
    async def get_board_state(self) -> dict:
        """
        Get the complete current board state.

        Returns:
            dict: Board state including all ships, squadrons, obstacles,
                  their positions, current status, and available actions.
        """
        return await self.vassal.get_board_state()

    @Tool
    async def get_ship_details(self, ship_id: str) -> dict:
        """
        Get detailed information about a specific ship.

        Args:
            ship_id: Unique identifier for the ship

        Returns:
            dict: Ship details including hull, shields, defense tokens,
                  upgrades, damage cards, and current status.
        """
        return await self.vassal.get_ship_details(ship_id)

    @Tool
    async def get_available_actions(self, piece_id: str) -> list[dict]:
        """
        Get all legal actions available for a game piece.

        Args:
            piece_id: Unique identifier for ship or squadron

        Returns:
            list[dict]: Available actions with details
        """
        # Implementation
        pass
```

**Tasks**:
- [ ] Implement all game state tools
- [ ] Add comprehensive docstrings
- [ ] Add input validation
- [ ] Create tool response schemas
- [ ] Test tools with Claude Desktop
- [ ] Add error handling for disconnected Vassal

**Estimated Effort**: 2-3 days

---

## Phase 3: Game Action Execution

### 3.1 Vassal Action Executor

**Goal**: Execute game actions programmatically in Vassal

**Files to Create**:
- `ActionExecutor.java` - Execute game actions
- `actions/*.java` - Specific action types

**Key Implementation Steps**:

```java
// ActionExecutor.java
public class ActionExecutor {
    private final GameModule gameModule;

    public ActionResult executeManeuver(
        String shipId,
        int speed,
        String joint
    ) {
        // 1. Find ship GamePiece
        GamePiece ship = findPieceById(shipId);

        // 2. Select appropriate maneuver tool
        ManeuverTool tool = getManeuverTool(speed, joint);

        // 3. Execute maneuver
        // This is complex - may need to simulate user actions
        // via Command pattern or direct manipulation

        // 4. Validate final position (collisions, etc.)

        // 5. Update ship state

        return new ActionResult(success, newPosition, messages);
    }

    public ActionResult executeAttack(
        String attackerId,
        String defenderId,
        String arc,
        String range
    ) {
        // 1. Validate attack is legal
        // 2. Gather dice pool
        // 3. Execute attack sequence
        // 4. Apply damage
        // 5. Return results
    }
}
```

**Major Challenges**:
- Simulating user interactions vs. direct piece manipulation
- Validating moves against game rules
- Handling maneuver tools programmatically
- Resolving attacks and dice rolls
- Managing game timing and windows

**Research Needed**:
- Can we directly manipulate GamePiece positions?
- How does Vassal handle Commands for multiplayer sync?
- Can we trigger maneuver tool programmatically?
- How to handle dice rolling (random vs. deterministic for testing)?

**Tasks**:
- [ ] Research Vassal Command pattern
- [ ] Implement ship movement/maneuvers
- [ ] Implement squadron movement
- [ ] Implement attack execution
- [ ] Implement defense token spending
- [ ] Implement upgrade card effects (subset)
- [ ] Add move validation
- [ ] Test action execution thoroughly

**Estimated Effort**: 7-10 days (complex!)

---

### 3.2 MCP Tools for Game Actions

**Goal**: Expose game actions as MCP tools

**Files to Create**:
- `tools/game_actions.py` - MCP tools for actions

```python
# tools/game_actions.py
@Tool
async def execute_maneuver(
    ship_id: str,
    speed: int,
    joint: str,
    validate_only: bool = False
) -> dict:
    """
    Execute a ship maneuver or validate if it would be legal.

    Args:
        ship_id: ID of ship to move
        speed: Speed (1-4 for most ships)
        joint: Maneuver joint ('left', 'right', 'straight')
        validate_only: If True, only check if legal without executing

    Returns:
        dict: Result including success, final position, any warnings
    """
    action = {
        'type': 'maneuver',
        'ship_id': ship_id,
        'speed': speed,
        'joint': joint,
        'validate_only': validate_only
    }
    return await self.vassal.execute_action(action)

@Tool
async def execute_attack(
    attacker_id: str,
    defender_id: str,
    arc: str,
    dice_modifications: list[str] = None
) -> dict:
    """
    Execute an attack from one ship to another.

    Args:
        attacker_id: ID of attacking ship
        defender_id: ID of defending ship
        arc: Firing arc ('front', 'left', 'right', 'rear')
        dice_modifications: List of modifications to apply

    Returns:
        dict: Attack results including damage dealt, tokens spent
    """
    # Implementation
    pass
```

**Tasks**:
- [ ] Implement movement tools
- [ ] Implement attack tools
- [ ] Implement defense token tools
- [ ] Implement command dial tools
- [ ] Add validation-only modes
- [ ] Test tool call sequences
- [ ] Document common action patterns

**Estimated Effort**: 3-4 days

---

## Phase 4: List Building Integration

### 4.1 Card Database MCP Resource

**Goal**: Expose card database as searchable MCP resource

**Files to Create**:
- `resources/card_database.py` - MCP resource for cards

```python
# resources/card_database.py
from mcp import Resource

@Resource
async def card_database() -> dict:
    """
    Searchable database of all Star Wars Armada cards.

    Includes ships, squadrons, upgrades, and objectives with
    full card text, point costs, and restrictions.
    """
    # Return card database
    # Or return URI to query endpoint
    pass
```

**Tasks**:
- [ ] Integrate with Star Forge API
- [ ] Create card search interface
- [ ] Add filtering by type, faction, cost
- [ ] Cache card data locally
- [ ] Create card detail views
- [ ] Add card legality information (banned/restricted)

**Estimated Effort**: 2-3 days

---

### 4.2 Fleet Building MCP Tools

**Goal**: Tools for constructing and validating fleets

**Files to Create**:
- `tools/list_building.py` - Fleet construction tools
- `models/fleet.py` - Fleet data models

```python
# tools/list_building.py
@Tool
async def search_cards(
    query: str = "",
    card_type: str = None,
    faction: str = None,
    max_cost: int = None
) -> list[dict]:
    """
    Search for cards by name, type, faction, or cost.

    Args:
        query: Text search in card name or text
        card_type: Filter by type (ship, squadron, upgrade_*, objective)
        faction: Filter by faction (empire, rebel, republic, separatist)
        max_cost: Maximum point cost

    Returns:
        list[dict]: Matching cards with basic info
    """
    return await self.starforge.search_cards(
        query, card_type, faction, max_cost
    )

@Tool
async def build_fleet_add_ship(
    fleet_id: str,
    ship_card_id: str
) -> dict:
    """
    Add a ship to the fleet being built.

    Args:
        fleet_id: ID of fleet in progress
        ship_card_id: ID of ship card to add

    Returns:
        dict: Updated fleet with new ship added
    """
    # Implementation
    pass

@Tool
async def validate_fleet(fleet_data: dict) -> dict:
    """
    Validate complete fleet for legality and point total.

    Args:
        fleet_data: Fleet composition

    Returns:
        dict: Validation result, point total, warnings/errors
    """
    return await self.starforge.validate_fleet(fleet_data)
```

**Tasks**:
- [ ] Implement card search tool
- [ ] Implement fleet construction tools
- [ ] Implement fleet validation
- [ ] Add upgrade slot compatibility checking
- [ ] Implement fleet export to Vassal format
- [ ] Test complete list building flow
- [ ] Create example list building prompts

**Estimated Effort**: 4-5 days

---

## Phase 5: Visual Understanding

### 5.1 Screenshot Capture

**Goal**: Capture screenshots of Vassal board

**Files to Create**:
- `ScreenshotCapture.java` - Java screenshot utility
- `vision/screenshot.py` - Python screenshot handler

```java
// ScreenshotCapture.java
import java.awt.Robot;
import java.awt.Rectangle;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;

public class ScreenshotCapture {
    private final Map vassalMap;

    public byte[] captureBoard() throws Exception {
        // Get Map component bounds
        Rectangle bounds = vassalMap.getView().getBounds();

        // Capture screenshot
        Robot robot = new Robot();
        BufferedImage screenshot = robot.createScreenCapture(bounds);

        // Convert to bytes
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(screenshot, "PNG", baos);
        return baos.toByteArray();
    }

    public byte[] captureBoardWithAnnotations(
        List<String> highlightPieceIds
    ) {
        // Capture and annotate
    }
}
```

**Tasks**:
- [ ] Implement basic screenshot capture in Java
- [ ] Add API endpoint for screenshots
- [ ] Implement screenshot tool in Python
- [ ] Add image format options (PNG, JPEG)
- [ ] Test with different Vassal window sizes
- [ ] Handle headless mode (if available)

**Estimated Effort**: 2-3 days

---

### 5.2 Image Annotation

**Goal**: Annotate screenshots with game information

**Files to Create**:
- `vision/annotation.py` - Image annotation utilities

```python
# vision/annotation.py
from PIL import Image, ImageDraw, ImageFont

class BoardAnnotator:
    def annotate_screenshot(
        self,
        image_bytes: bytes,
        board_state: dict,
        options: dict
    ) -> bytes:
        """
        Annotate screenshot with labels and overlays.

        Args:
            image_bytes: Raw screenshot
            board_state: Current game state
            options: Annotation options (show_ranges, show_arcs, etc.)

        Returns:
            bytes: Annotated image
        """
        img = Image.open(BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)

        # Annotate ships with IDs
        for ship in board_state['ships']:
            x, y = ship['position']
            draw.text((x, y), ship['id'], fill='red')

        # Draw firing arcs if requested
        if options.get('show_arcs'):
            self._draw_arcs(draw, board_state)

        # Draw range rulers if requested
        if options.get('show_ranges'):
            self._draw_ranges(draw, board_state)

        # Save annotated image
        output = BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()
```

**Tasks**:
- [ ] Implement ship ID labels
- [ ] Draw firing arcs overlay
- [ ] Draw range rulers
- [ ] Highlight specific ships/zones
- [ ] Add measurement tools
- [ ] Test annotation accuracy
- [ ] Optimize for LLM vision consumption

**Estimated Effort**: 3-4 days

---

### 5.3 Screenshot MCP Tool

**Goal**: MCP tool for capturing annotated screenshots

```python
@Tool
async def screenshot_board(
    perspective: str = "overhead",
    annotate: bool = True,
    highlight_ships: list[str] = None,
    show_ranges: bool = False,
    show_arcs: bool = False
) -> dict:
    """
    Capture screenshot of current board state.

    Args:
        perspective: View angle (overhead, player1, player2)
        annotate: Add ship IDs and labels
        highlight_ships: List of ship IDs to highlight
        show_ranges: Overlay range measurements
        show_arcs: Show firing arcs

    Returns:
        dict: {
            'image_url': 'data:image/png;base64,...',
            'timestamp': '2026-01-08T12:34:56',
            'board_state_snapshot': {...}
        }
    """
    # Get screenshot from Vassal
    image_bytes = await self.vassal.capture_screenshot()

    # Get current state for annotation
    board_state = await self.vassal.get_board_state()

    # Annotate if requested
    if annotate:
        image_bytes = self.annotator.annotate_screenshot(
            image_bytes,
            board_state,
            {'show_ranges': show_ranges, 'show_arcs': show_arcs}
        )

    # Encode as data URL
    import base64
    image_b64 = base64.b64encode(image_bytes).decode()

    return {
        'image_url': f'data:image/png;base64,{image_b64}',
        'timestamp': datetime.now().isoformat(),
        'board_state_snapshot': board_state
    }
```

**Tasks**:
- [ ] Implement screenshot tool
- [ ] Test with Claude's vision capabilities
- [ ] Optimize image size/quality
- [ ] Add perspective options
- [ ] Test annotation visibility

**Estimated Effort**: 2 days

---

## Phase 6: Benchmarking Framework

### 6.1 Test Scenario Definitions

**Goal**: Define comprehensive test scenarios

**Directory Structure**:
```
benchmarks/data/
├── rules_knowledge/
│   ├── basic_rules.json
│   ├── edge_cases.json
│   └── timing_windows.json
├── list_building/
│   ├── build_competitive_fleet.json
│   ├── build_counter_fleet.json
│   └── identify_illegal_fleets.json
├── spatial_reasoning/
│   ├── predict_positions.json
│   ├── collision_detection.json
│   └── arc_calculations.json
├── tactical_play/
│   ├── scenarios/
│   │   ├── opening_engagement.json
│   │   ├── late_game_cleanup.json
│   │   └── objective_play.json
│   └── full_games/
│       ├── game_001.json
│       └── game_002.json
```

**Example Test Scenario**:
```json
{
  "id": "spatial_reasoning_001",
  "name": "Predict ISD Maneuver",
  "category": "spatial_reasoning",
  "description": "Predict final position of ISD after speed-2 maneuver",
  "setup": {
    "board_state": "...",
    "ship_id": "isd-1",
    "current_position": {"x": 100, "y": 200, "rotation": 0}
  },
  "task": "Predict the final position after speed-2 left joint maneuver",
  "expected_output": {
    "x": 95,
    "y": 250,
    "rotation": 315,
    "tolerance_mm": 5
  },
  "metrics": ["position_accuracy", "rotation_accuracy", "collision_detected"]
}
```

**Tasks**:
- [ ] Define test scenario schema
- [ ] Create rules knowledge tests (50+ questions)
- [ ] Create list building challenges (20+ scenarios)
- [ ] Create spatial reasoning tests (30+ scenarios)
- [ ] Create tactical scenarios (10+ openings)
- [ ] Create full game scenarios (5+ games)
- [ ] Validate all test scenarios
- [ ] Document expected behaviors

**Estimated Effort**: 7-10 days

---

### 6.2 Test Runner

**Goal**: Execute tests and collect results

**Files to Create**:
- `test_runner.py` - Main test execution engine
- `metrics.py` - Metrics collection and calculation

```python
# test_runner.py
class BenchmarkRunner:
    def __init__(self, mcp_client, model_name: str):
        self.mcp_client = mcp_client
        self.model_name = model_name

    async def run_scenario(self, scenario: dict) -> dict:
        """Run a single test scenario."""
        # 1. Set up board state
        await self.setup_scenario(scenario['setup'])

        # 2. Present task to model via MCP
        result = await self.execute_task(scenario['task'])

        # 3. Compare result to expected output
        metrics = self.calculate_metrics(
            result,
            scenario['expected_output'],
            scenario['metrics']
        )

        # 4. Record results
        return {
            'scenario_id': scenario['id'],
            'model': self.model_name,
            'result': result,
            'metrics': metrics,
            'passed': metrics['overall_pass'],
            'timestamp': datetime.now().isoformat()
        }

    async def run_suite(self, suite_name: str) -> dict:
        """Run complete test suite."""
        scenarios = self.load_scenarios(suite_name)
        results = []

        for scenario in scenarios:
            result = await self.run_scenario(scenario)
            results.append(result)

        summary = self.summarize_results(results)
        return {
            'suite': suite_name,
            'model': self.model_name,
            'results': results,
            'summary': summary
        }
```

**Tasks**:
- [ ] Implement test runner core
- [ ] Add scenario loading
- [ ] Implement metric calculation
- [ ] Add result persistence (JSON/SQLite)
- [ ] Create summary reports
- [ ] Add progress tracking
- [ ] Implement timeout handling
- [ ] Add retry logic for flaky tests

**Estimated Effort**: 5-7 days

---

### 6.3 Baseline AI Implementation

**Goal**: Create baseline AI for comparison

**Approaches**:
1. **Rule-based AI** - Simple heuristics
2. **Random AI** - Valid random actions
3. **Scripted AI** - Predefined strategies

```python
# baselines/random_ai.py
class RandomAI:
    """Baseline AI that makes valid random moves."""

    async def choose_action(self, game_state: dict) -> dict:
        available_actions = await self.get_available_actions(
            game_state
        )
        return random.choice(available_actions)

# baselines/heuristic_ai.py
class HeuristicAI:
    """Baseline AI using simple heuristics."""

    async def choose_action(self, game_state: dict) -> dict:
        # Simple heuristics:
        # 1. Activate most damaged ship first
        # 2. Move to maximize enemy ships at close range
        # 3. Focus fire on lowest hull enemy
        # 4. Spend defense tokens conservatively
        pass
```

**Tasks**:
- [ ] Implement random AI
- [ ] Implement rule-based AI
- [ ] Test baseline AIs
- [ ] Benchmark baseline performance
- [ ] Document baseline strategies

**Estimated Effort**: 4-5 days

---

## Phase 7: Advanced Features

### 7.1 Movement Prediction Tool

**Goal**: Accurate movement prediction with collision detection

```python
@Tool
async def predict_ship_position(
    ship_id: str,
    maneuver: dict,
    check_collisions: bool = True
) -> dict:
    """
    Predict ship's final position after maneuver.

    Args:
        ship_id: Ship to predict for
        maneuver: Maneuver details (speed, joint)
        check_collisions: Check for collisions with other objects

    Returns:
        dict: Predicted position, rotation, collision warnings
    """
    # Get current ship state
    ship = await self.vassal.get_ship_details(ship_id)

    # Calculate maneuver geometry
    final_pos = self.calculate_maneuver(
        ship['position'],
        ship['rotation'],
        maneuver
    )

    # Check collisions if requested
    if check_collisions:
        board_state = await self.vassal.get_board_state()
        collisions = self.check_collisions(
            ship,
            final_pos,
            board_state
        )
        final_pos['collisions'] = collisions

    return final_pos
```

**Tasks**:
- [ ] Research Armada maneuver templates
- [ ] Implement movement calculation
- [ ] Implement collision detection
- [ ] Test against actual Vassal movements
- [ ] Handle edge cases (board edges)
- [ ] Optimize performance

**Estimated Effort**: 5-7 days

---

### 7.2 Rules Reference Integration

**Goal**: Provide rules lookup as MCP resource

```python
@Resource
async def rules_reference() -> dict:
    """
    Star Wars Armada rules reference.

    Searchable rules text, FAQ, and errata.
    """
    return {
        'uri': 'armadabench://rules',
        'description': 'Armada rules reference'
    }

@Tool
async def search_rules(query: str) -> list[dict]:
    """
    Search rules reference for specific topics.

    Args:
        query: Search term (e.g., "squadron activation", "overlapping")

    Returns:
        list[dict]: Relevant rule sections
    """
    # Search through rules PDF or structured rules data
    pass
```

**Tasks**:
- [ ] Convert rules PDF to structured data
- [ ] Implement rules search
- [ ] Add FAQ integration
- [ ] Add errata tracking
- [ ] Test rule lookup accuracy

**Estimated Effort**: 3-4 days

---

## Phase 8: Integration & Testing

### 8.1 End-to-End Integration Testing

**Goal**: Verify all components work together

**Test Scenarios**:
1. **Complete game flow**
   - Initialize Vassal
   - Load module
   - Build fleets via MCP
   - Load fleets into Vassal
   - Play complete game
   - Capture final state

2. **Visual + State consistency**
   - Take screenshot
   - Get board state JSON
   - Verify they match

3. **Action validation**
   - Execute move
   - Verify state update
   - Screenshot confirms visual change

**Tasks**:
- [ ] Write integration test suite
- [ ] Test with real LLM (Claude)
- [ ] Test with multiple models
- [ ] Performance testing
- [ ] Stress testing (long games)
- [ ] Error recovery testing

**Estimated Effort**: 5-7 days

---

### 8.2 Documentation

**Goal**: Comprehensive documentation for users and developers

**Documents to Create**:
- [ ] `README.md` - Project overview and quick start
- [ ] `ARCHITECTURE.md` - System architecture (✓ done)
- [ ] `IMPLEMENTATION_PLAN.md` - This document (✓ done)
- [ ] `API_REFERENCE.md` - All MCP tools and endpoints
- [ ] `BENCHMARKS.md` - How to run benchmarks
- [ ] `CONTRIBUTING.md` - Development guidelines
- [ ] `VASSAL_INTEGRATION.md` - Vassal-specific details
- [ ] `MCP_TOOLS.md` - Detailed tool documentation

**Estimated Effort**: 3-4 days

---

## Total Estimated Timeline

| Phase | Effort | Duration (if 1 dev) |
|-------|--------|---------------------|
| Phase 1: Foundation | 10-14 days | 2-3 weeks |
| Phase 2: Game State | 11-16 days | 2-3 weeks |
| Phase 3: Actions | 10-14 days | 2-3 weeks |
| Phase 4: List Building | 6-8 days | 1-2 weeks |
| Phase 5: Visual | 7-9 days | 1.5-2 weeks |
| Phase 6: Benchmarks | 16-22 days | 3-4 weeks |
| Phase 7: Advanced | 8-11 days | 2 weeks |
| Phase 8: Integration | 8-11 days | 2 weeks |
| **TOTAL** | **76-105 days** | **~4-5 months** |

## Risk Factors & Contingencies

### High Risk Items
1. **Vassal API limitations** - May not support all needed operations
   - Mitigation: Early prototyping, alternative approaches (UI automation)

2. **Movement precision** - Matching Vassal's movement exactly
   - Mitigation: Tolerance-based testing, calibration tools

3. **Action execution complexity** - Simulating user actions is hard
   - Mitigation: Study Vassal source code, use Command pattern

4. **Performance** - Java ↔ Python communication overhead
   - Mitigation: Connection pooling, caching, async operations

### Medium Risk Items
- Star Forge API integration complexity
- Screenshot quality for LLM vision
- Benchmark scenario quality
- Rules ambiguity handling

## Next Steps

1. **Immediate**: Set up project structure and build system
2. **Week 1**: Basic Vassal integration and MCP server
3. **Week 2**: Star Forge client and first MCP tools
4. **Week 3**: Game state reading and REST API
5. **Week 4**: Begin action execution research

## Success Criteria

### Minimum Viable Product (MVP)
- [ ] Load Armada module in Vassal
- [ ] Read complete board state via API
- [ ] Execute basic ship movement
- [ ] MCP server with 5+ core tools
- [ ] Screenshot capture working
- [ ] One complete test scenario runs

### Full Release (v1.0)
- [ ] All game actions supported
- [ ] Complete fleet building integration
- [ ] 100+ test scenarios
- [ ] Benchmark results for 3+ models
- [ ] Documentation complete
- [ ] CI/CD pipeline operational
