# ArmadaBench 🎯

> A comprehensive benchmarking suite for evaluating frontier multimodal language models on their ability to learn, strategize, and play Star Wars Armada through the Vassal game engine.

## Overview

ArmadaBench tests language models across multiple cognitive dimensions:

- **📚 Rules Understanding** - Comprehend complex game rules and interactions
- **🛠️ Tool Use** - Effectively use tool calls to interact with game systems
- **👁️ Visual Comprehension** - Understand board state from screenshots
- **📐 Spatial Reasoning** - Predict positions and plan movement sequences
- **🎲 Strategic Planning** - Build competitive fleets and execute tactics
- **❓ Ambiguity Handling** - Resolve edge cases and unclear game states

## Why Star Wars Armada?

Star Wars Armada provides an ideal testbed for multimodal LLMs:

1. **Complex Rules** - Rich rules system with timing windows, card interactions, and edge cases
2. **Spatial Reasoning** - Requires predicting ship positions after complex maneuvers
3. **Strategic Depth** - List building and tactical play require long-term planning
4. **Visual & Structured Data** - Tests both vision capabilities and structured data processing
5. **Ambiguity** - Many situations require rule interpretation and handling uncertainty
6. **Measurable Outcomes** - Win/loss, accuracy metrics, and comparative performance

## System Architecture

```
┌─────────────────────────────────────────────────┐
│     Language Model (Claude, GPT-4, Gemini)      │
│     Tests: Rules, Tactics, List Building        │
└──────────────────┬──────────────────────────────┘
                   │
                   │ MCP Protocol
                   │ (40+ specialized tools)
                   │
┌──────────────────▼──────────────────────────────┐
│         MCP Server (Python)                      │
│  • Game state queries                            │
│  • Action execution                              │
│  • Fleet building                                │
│  • Visual analysis                               │
│  • Rule lookups                                  │
└───┬──────────────┬──────────────┬───────────────┘
    │              │              │
    ▼              ▼              ▼
┌────────┐   ┌──────────┐   ┌─────────────┐
│ Vassal │   │  Star    │   │ Benchmark   │
│ Engine │   │  Forge   │   │ Framework   │
│ (Java) │   │   API    │   │  (Python)   │
└────────┘   └──────────┘   └─────────────┘
```

## Quick Start

### Prerequisites

- **Java 17+** (for Vassal integration)
- **Python 3.10+** (for MCP server and benchmarking)
- **Vassal Engine 3.7+**
- **Star Wars Armada Vassal Module** (latest version)
- **Star Forge API** access

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/armadabench.git
cd armadabench

# Set up Java component (Vassal integration)
cd vassal-integration
./gradlew build
./gradlew run

# Set up Python components (in separate terminal)
cd ../mcp-server
pip install -e .

# Configure MCP server
export STARFORGE_API_URL="your-api-url"
export VASSAL_API_URL="http://localhost:8080"

# Run MCP server
python -m armadabench_mcp.server
```

### Running Benchmarks

```bash
cd benchmarks
python -m armadabench.test_runner \
  --model claude-3-5-sonnet-20241022 \
  --suite spatial_reasoning \
  --output results/
```

## Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed system architecture and components
- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Phase-by-phase implementation guide
- **[MCP_TOOLS_SPECIFICATION.md](./MCP_TOOLS_SPECIFICATION.md)** - Complete MCP tool reference
- **[QUESTIONS_AND_RESEARCH.md](./QUESTIONS_AND_RESEARCH.md)** - Open questions and research items

## Project Status

🚧 **Currently in Planning Phase** 🚧

This is a greenfield project. The documentation outlines the complete architecture and implementation plan.

### Completed
- ✅ Architecture design
- ✅ MCP tools specification
- ✅ Implementation roadmap
- ✅ Research on Vassal API

### In Progress
- 🔄 Vassal integration layer prototype
- 🔄 Star Forge API client
- 🔄 Basic MCP server

### Upcoming
- ⏳ Game state reading
- ⏳ Action execution
- ⏳ Screenshot & vision system
- ⏳ Benchmark scenario creation

## Key Components

### 1. Vassal Integration Layer (Java)

Interfaces with Vassal Engine to:
- Load and control Star Wars Armada module
- Read complete game state (ships, squadrons, obstacles)
- Execute game actions (movement, attacks, token spending)
- Capture board screenshots
- Validate moves and rule compliance

**API**: REST API on port 8080 exposing game state and actions

### 2. MCP Server (Python)

Exposes 40+ tools to language models via Model Context Protocol:

**Game State Tools**:
- `get_board_state()` - Complete current state
- `get_ship_details(id)` - Detailed ship info
- `get_range_and_arc(source, target)` - Range calculation

**Action Tools**:
- `execute_maneuver(ship, maneuver)` - Move ships
- `execute_attack(attacker, defender, arc)` - Resolve attacks
- `spend_defense_token(ship, token)` - Use tokens

**List Building Tools**:
- `search_cards(query, filters)` - Find cards
- `create_fleet(faction, points)` - Start fleet
- `add_ship_to_fleet(fleet, ship)` - Build fleet
- `validate_fleet(fleet)` - Check legality

**Visual Tools**:
- `screenshot_board(options)` - Capture annotated images
- `predict_ship_position(ship, maneuver)` - Movement prediction

**Analysis Tools**:
- `calculate_dice_probabilities(pool)` - Attack math
- `analyze_board_position()` - Tactical analysis

### 3. Star Forge Integration

Connects to existing Star Forge list builder API:
- Comprehensive card database (ships, squadrons, upgrades, objectives)
- Card search and filtering
- Fleet validation logic
- Point cost calculations
- Upgrade compatibility checking

### 4. Benchmarking Framework

Evaluates LLM performance across dimensions:

**Test Categories**:
1. **Rules Knowledge** (50+ questions) - Edge cases, timing, interactions
2. **List Building** (20+ scenarios) - Build competitive fleets, counter lists
3. **Spatial Reasoning** (30+ tests) - Position prediction, collision detection
4. **Tactical Play** (10+ scenarios) - Opening plays, objective scoring
5. **Full Games** (5+ games) - Complete games vs. baseline AI

**Metrics**:
- Rules accuracy percentage
- List competitiveness scores
- Spatial prediction error (mm)
- Win rate vs. baselines
- Tool call efficiency
- Time to complete actions

## Example Usage

### Building a Fleet

```python
# LLM uses MCP tools to build a 400-point Imperial fleet

# 1. Search for flagship
ships = await search_cards(
    query="Star Destroyer",
    filters={"faction": "empire", "type": "ship"}
)

# 2. Create fleet and add ship
fleet = await create_fleet(faction="empire", point_limit=400)
await add_ship_to_fleet(fleet["fleet_id"], "isd-ii")

# 3. Add commander and upgrades
await add_upgrade_to_ship(fleet["fleet_id"], "ship-1", "vader-commander")
await add_upgrade_to_ship(fleet["fleet_id"], "ship-1", "gunnery-team")

# 4. Validate and export
validation = await validate_fleet(fleet["fleet_id"])
await export_fleet_to_vassal(fleet["fleet_id"])
```

### Playing a Turn

```python
# LLM activates and moves ship

# 1. Check what can be activated
activations = await get_available_activations()

# 2. Get ship details
ship = await get_ship_details("isd-1")

# 3. Predict movement
prediction = await predict_ship_position(
    ship_id="isd-1",
    maneuver={"speed": 2, "joint": "straight"}
)

# 4. Execute if safe
if prediction["valid"] and not prediction["collisions"]:
    result = await execute_maneuver("isd-1", {"speed": 2, "joint": "straight"})

# 5. Attack target
ranges = await get_range_and_arc("isd-1", "cr90-1")
if ranges["can_attack"]:
    attack = await execute_attack("isd-1", "cr90-1", "front")
```

### Visual Understanding

```python
# LLM captures and analyzes board state

# 1. Get screenshot with annotations
screenshot = await screenshot_board({
    "annotate": True,
    "show_ranges": True,
    "show_arcs": True,
    "highlight_ships": ["isd-1", "mc80-1"]
})

# 2. LLM vision processes image
# 3. Cross-reference with structured data
board_state = await get_board_state()

# LLM now has both visual and structured understanding
```

## Research Questions

Key questions we're investigating:

### Vassal Engine
- ❓ Can we run Vassal headless or do we need a display?
- ❓ How exactly do we programmatically execute maneuvers?
- ❓ Can we hook into Vassal's random number generator for deterministic tests?
- ❓ What's the best way to identify piece types in the Armada module?

### Star Forge API
- ❓ What is the API endpoint and authentication method?
- ❓ Can we get complete card data including abilities and restrictions?
- ❓ Does existing validation logic cover all fleet building rules?

### Benchmarking
- ❓ What performance constitutes "good" for an LLM?
- ❓ How many test scenarios needed for statistical significance?
- ❓ Should we test against human players or just AI baselines?

See [QUESTIONS_AND_RESEARCH.md](./QUESTIONS_AND_RESEARCH.md) for complete list.

## Development Roadmap

### Phase 1: Foundation (Weeks 1-3)
- Set up project structure
- Basic Vassal integration
- Minimal MCP server
- Star Forge API client

### Phase 2: Game State (Weeks 4-6)
- Read complete board state
- Ship/squadron details
- REST API for state queries
- Python client for Vassal API

### Phase 3: Actions (Weeks 7-9)
- Execute ship movement
- Execute attacks
- Defense token spending
- Move validation

### Phase 4: List Building (Weeks 10-11)
- Card search integration
- Fleet construction tools
- Validation and export
- Vassal fleet loading

### Phase 5: Visual (Weeks 12-13)
- Screenshot capture
- Image annotation
- Multi-perspective views
- Arc and range overlays

### Phase 6: Benchmarks (Weeks 14-17)
- Test scenario creation
- Test runner implementation
- Baseline AI
- Metrics collection

### Phase 7: Integration (Weeks 18-19)
- End-to-end testing
- Multi-model testing
- Performance optimization
- Documentation

**Total Timeline**: ~4-5 months for v1.0

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for detailed breakdown.

## Contributing

This project is in early development. Contributions welcome!

Areas where we need help:
- **Vassal experts** - Help understand Vassal API and module structure
- **Armada experts** - Create test scenarios and validate rule implementations
- **Java developers** - Build Vassal integration layer
- **Python developers** - Build MCP server and benchmarking framework
- **ML researchers** - Design evaluation metrics and benchmarks

## Use Cases

### 1. Model Evaluation
Benchmark different LLMs on complex strategy game performance

### 2. Research
Study how models handle:
- Long-term planning
- Spatial reasoning
- Visual + structured data fusion
- Tool use in complex domains

### 3. AI Training
Use as reinforcement learning environment or training data generation

### 4. Game AI Development
Build AI opponents for Star Wars Armada

## Technical Requirements

### Minimum System Requirements
- **CPU**: 4+ cores (for parallel testing)
- **RAM**: 8GB+ (Vassal + JVM + Python)
- **Storage**: 2GB (Vassal, modules, test data)
- **OS**: Linux, macOS, or Windows with WSL

### Recommended
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **GPU**: Optional, for visual analysis tasks

## License

[TBD - Suggest MIT or Apache 2.0]

## Acknowledgments

- **Vassal Engine** - Open-source board game engine
- **Fantasy Flight Games / Atomic Mass Games** - Star Wars Armada
- **Star Forge** - List building tool and API
- **Armada Community** - Module maintenance and rules expertise
- **Anthropic** - Model Context Protocol specification

## Contact

[Your contact information or organization]

## Links

- **Vassal Engine**: https://vassalengine.org/
- **Star Wars Armada**: https://www.atomicmassgames.com/star-wars-armada-documents
- **MCP Specification**: https://modelcontextprotocol.io/
- **Discussion Forum**: [TBD]

---

**Status**: 🚧 Planning Phase - See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for next steps

Built with ❤️ for the Star Wars Armada and AI research communities
