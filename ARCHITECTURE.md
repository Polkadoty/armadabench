# Armada Bench - Architecture Overview

## Project Vision

ArmadaBench is a comprehensive benchmarking suite for frontier multimodal language models, testing their ability to:
- **Understand complex game rules** (Star Wars Armada)
- **Use tool calls** to interact with game systems
- **Visual comprehension** of board state through screenshots
- **Spatial reasoning** to predict component positions and movement
- **Strategic planning** including list building and tactical play
- **Handle ambiguity** in game states and rule interpretations

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Language Model (LLM)                      │
│           (Claude, GPT-4, Gemini, etc.)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ MCP Protocol
                     │
┌────────────────────▼────────────────────────────────────────┐
│              MCP Server (Python)                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tools:                                                 │ │
│  │  - get_board_state()                                   │ │
│  │  - move_ship(id, maneuver)                             │ │
│  │  - execute_attack(attacker, defender, arc)             │ │
│  │  - screenshot_board()                                  │ │
│  │  - get_ship_details(id)                                │ │
│  │  - search_cards(query)                                 │ │
│  │  - build_fleet(faction, points)                        │ │
│  │  - validate_fleet(fleet_data)                          │ │
│  │                                                          │ │
│  │  Resources:                                             │ │
│  │  - Card database (ships, squadrons, upgrades)          │ │
│  │  - Rules reference                                      │ │
│  │  - Game state history                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────────┐
│   Vassal     │ │ Star Forge  │ │  Benchmarking    │
│  Integration │ │    API      │ │   Framework      │
│   (Java)     │ │  (Existing) │ │   (Python)       │
└──────────────┘ └─────────────┘ └──────────────────┘
        │
        ▼
┌──────────────┐
│ Star Wars    │
│   Armada     │
│ Vassal Module│
└──────────────┘
```

## Core Components

### 1. Vassal Integration Layer (Java)

**Purpose**: Bridge between Vassal engine and Python MCP server

**Key Responsibilities**:
- Launch and control Vassal game engine
- Access game state via Vassal API
- Execute game actions programmatically
- Capture screenshots of board state
- Monitor and validate game rules

**Technology**: Java 17+ (matching Vassal requirements)

**Critical Vassal API Classes**:
- `VASSAL.build.GameModule` - Main entry point, singleton access
- `VASSAL.counters.GamePiece` - Individual game pieces (ships, squadrons)
- `VASSAL.build.module.Map` - Board/map management, `Map.getPieces()` for state
- `VASSAL.command.Command` - Command pattern for game actions
- `VASSAL.tools.DataArchive` - Access to module images and data

**Communication**:
- REST API or gRPC server exposing Vassal operations
- JSON-RPC for bidirectional communication with Python
- WebSocket for real-time game state updates

### 2. MCP Server (Python)

**Purpose**: Provide LLM-friendly interface to game systems

**MCP Tools to Expose**:

#### Game State Tools
- `get_board_state()` - Returns JSON representation of current board
- `get_ship_details(ship_id)` - Hull, shields, upgrades, current damage
- `get_squadron_details(squadron_id)` - Type, health, engagement status
- `get_available_actions(piece_id)` - Valid moves for a piece
- `screenshot_board(perspective?)` - Capture visual board state
- `get_range_to_target(source, target)` - Calculate range and arc

#### Game Action Tools
- `activate_ship(ship_id)` - Begin ship activation
- `execute_maneuver(ship_id, speed, joint)` - Move ship
- `execute_attack(attacker, defender, arc, dice_pool)` - Resolve attack
- `spend_defense_token(ship_id, token_type)` - Use defense token
- `activate_squadron(squadron_id)` - Activate squadron
- `move_squadron(squadron_id, position)` - Move squadron
- `pass_turn()` - End current activation

#### List Building Tools
- `search_cards(query, type, faction)` - Find ships/upgrades/objectives
- `get_card_details(card_id)` - Full card text and stats
- `validate_card_legality(card_id, fleet_context)` - Check restrictions
- `build_fleet_add_ship(fleet, ship_id)` - Add ship to fleet
- `build_fleet_add_upgrade(fleet, ship, upgrade_id)` - Add upgrade
- `validate_fleet(fleet_data)` - Check point limit, legality
- `export_fleet_to_vassal(fleet_data)` - Generate Vassal setup

#### Analysis Tools
- `predict_ship_position(ship_id, maneuver)` - Calculate end position
- `get_threat_range(ship_id)` - Show firing arcs and ranges
- `evaluate_dice_pool(pool, modifications)` - Calculate probabilities
- `get_game_history()` - Return previous actions/states

**MCP Resources to Provide**:
- Card database (searchable)
- Rules reference document
- FAQ and errata
- Game state snapshots
- Common tactical patterns

**Technology**:
- Python 3.10+ with official MCP SDK
- FastMCP for rapid tool development
- Integration with Star Forge API

### 3. Star Forge Integration

**Purpose**: Provide comprehensive card data to LLMs

**Integration Points**:
- Existing Star Forge JSON API for card data
- Card search and filtering
- Fleet validation logic
- Point cost calculations
- Upgrade slot compatibility

**Data Needed**:
- Ships (hull values, shields, command, squadron, engineering values)
- Squadrons (hull, speed, abilities)
- Upgrades (all types: commander, titles, weapons, support, etc.)
- Objectives (setup effects, end-of-round scoring)
- Card restrictions and errata

### 4. Screenshot & Vision System

**Purpose**: Provide visual understanding of board state

**Capabilities**:
- Capture full board screenshots
- Annotate with ship IDs, ranges, arcs
- Multiple perspectives (player 1, player 2, overhead)
- Highlight specific areas of interest
- Sequence of screenshots for move prediction

**Implementation**:
- Java AWT/Robot for Vassal window capture
- Python PIL/OpenCV for annotation
- Standardized image formats for LLM consumption

### 5. Benchmarking Framework

**Purpose**: Evaluate and compare LLM performance

**Test Categories**:

#### 1. Rules Knowledge
- Multiple choice questions about rules
- Edge case scenarios
- Timing and priority questions

#### 2. List Building
- Build competitive fleet for given faction
- Build counter-list to opponent fleet
- Optimize fleet for specific objective set
- Identify illegal fleet compositions

#### 3. Spatial Reasoning
- Predict ship position after maneuver
- Calculate optimal firing arcs
- Plan multi-turn movement sequences
- Avoid obstacles and board edges

#### 4. Tactical Play
- Execute complete game against baseline AI
- Respond to specific board states
- Prioritize targets effectively
- Manage resources (tokens, activation order)

#### 5. Ambiguity Handling
- Resolve simultaneous effects
- Interpret complex card interactions
- Handle unclear board states

**Metrics**:
- Accuracy of rules interpretations
- Fleet competitiveness scores
- Win rate against baselines
- Position prediction accuracy
- Tool call efficiency
- Time to complete actions

**Technology**: Python with pytest, pandas for analysis

## Data Flow Examples

### Example 1: Ship Movement

```
1. LLM decides to move ship
   → Calls: get_available_actions(ship_id="isd-1")

2. MCP Server queries Vassal Integration
   → Vassal returns: valid maneuvers based on current ship state

3. LLM analyzes options and predicts
   → Calls: predict_ship_position(ship_id="isd-1", maneuver="speed-2-left")

4. MCP Server calculates position
   → Returns: predicted coordinates, rotation, collision check

5. LLM commits to move
   → Calls: execute_maneuver(ship_id="isd-1", speed=2, joint="left")

6. Vassal Integration executes
   → Updates game state
   → Returns: success, new position

7. Benchmarking framework records
   → Logs: predicted vs actual position accuracy
```

### Example 2: List Building

```
1. LLM receives task: "Build 400pt Imperial fleet"
   → Calls: search_cards(faction="empire", type="ship")

2. Star Forge returns available ships
   → LLM analyzes options

3. LLM selects flagship
   → Calls: build_fleet_add_ship(fleet, ship_id="isd-ii")
   → Calls: get_card_details("isd-ii")

4. LLM adds commander and upgrades
   → Calls: search_cards(type="commander", faction="empire")
   → Calls: build_fleet_add_upgrade(fleet, ship, upgrade_id="vader-commander")
   → Calls: validate_card_legality(...)

5. Repeat for remaining ships/squadrons

6. Final validation
   → Calls: validate_fleet(fleet_data)
   → Returns: point total, legality, suggestions

7. Export to Vassal
   → Calls: export_fleet_to_vassal(fleet_data)
   → Vassal Integration loads fleet into module
```

### Example 3: Visual Board Analysis

```
1. LLM needs to understand board
   → Calls: screenshot_board(perspective="player-1")

2. Vision system captures and annotates
   → Returns: image with labeled ships, ranges

3. LLM analyzes visually
   → Identifies threats, opportunities

4. LLM cross-references with state data
   → Calls: get_board_state()
   → Calls: get_ship_details(ship_id) for each visible ship

5. LLM formulates strategy
   → Uses combined visual + structured data
```

## Technology Stack Summary

| Component | Primary Language | Key Dependencies |
|-----------|-----------------|------------------|
| Vassal Integration | Java 17+ | Vassal 3.7+, JAX-RS or gRPC |
| MCP Server | Python 3.10+ | MCP SDK 1.2+, FastMCP, httpx |
| Star Forge Integration | Python | Existing Star Forge codebase |
| Benchmarking | Python | pytest, pandas, numpy |
| Vision System | Python | PIL, OpenCV, matplotlib |

## Development Phases

### Phase 1: Foundation
- Set up Vassal Integration Layer (Java)
- Create basic MCP server with minimal tools
- Integrate Star Forge API for card data
- Implement basic screenshot capability

### Phase 2: Game State
- Comprehensive board state reading
- Ship/squadron detail queries
- Movement prediction tools
- Basic game action execution

### Phase 3: List Building
- Full card search and filtering
- Fleet construction tools
- Validation and export to Vassal
- Integration with existing Star Forge

### Phase 4: Visual Understanding
- Advanced screenshot annotation
- Multi-perspective views
- Visual diff for movement
- Arc and range visualization

### Phase 5: Benchmarking
- Test suite development
- Baseline AI implementation
- Metrics collection and analysis
- Leaderboard and comparison tools

### Phase 6: Full Gameplay
- Complete game execution
- Turn management
- Complex interactions and timing
- Tournament simulation

## Security & Safety Considerations

- **Sandboxing**: Vassal runs in controlled environment
- **API Rate Limiting**: Prevent abuse of MCP tools
- **Validation**: All game actions validated before execution
- **Audit Logging**: Complete record of LLM actions
- **Isolation**: Each benchmark test in separate instance

## Performance Considerations

- **Caching**: Card data cached in MCP server
- **Lazy Loading**: Vassal module loaded on-demand
- **Parallel Testing**: Multiple benchmark instances
- **State Snapshots**: Quick save/restore for testing
- **Connection Pooling**: Efficient Vassal ↔ Python communication
