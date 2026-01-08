# ArmadaBench MCP Server

MCP (Model Context Protocol) server that enables LLMs to interact with Star Wars Armada through the Vassal game engine.

## Overview

This MCP server provides tools for:

- **Board State** - Read current game state, ship details, squadron positions
- **Screenshots** - Capture visual board state for multimodal analysis
- **Game Actions** - Execute maneuvers, attacks, and squadron activations
- **Card Data** - Search and retrieve card information (via ISB API)

## Installation

```bash
cd armadabench/mcp-server

# Install with pip
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Configuration

Set environment variables:

```bash
# Vassal API server URL (default: http://localhost:8080)
export VASSAL_API_URL="http://localhost:8080"
```

## Running the Server

### Standalone

```bash
# Run the MCP server
armadabench-mcp
```

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "armadabench": {
      "command": "python",
      "args": ["-m", "armadabench_mcp.server"],
      "env": {
        "VASSAL_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

## Available Tools

### Board State Tools

#### `get_board_state`

Get the complete current game state.

```python
# Returns:
{
    "game_id": "current",
    "round": 3,
    "phase": "ship_phase",
    "active_player": "player1",
    "ships": [...],
    "squadrons": [...],
    "obstacles": [...]
}
```

#### `get_ship_details`

Get detailed information about a specific ship.

```python
# Arguments:
{
    "ship_id": "isd-1"
}

# Returns:
{
    "id": "isd-1",
    "name": "Imperial Star Destroyer II",
    "position": {"x": 250, "y": 400},
    "rotation": 45,
    "hull": {"current": 9, "maximum": 11},
    "shields": {
        "front": {"current": 4, "maximum": 4},
        "left": {"current": 3, "maximum": 3},
        "right": {"current": 3, "maximum": 3},
        "rear": {"current": 2, "maximum": 2}
    },
    "defense_tokens": [
        {"type": "brace", "status": "ready"},
        {"type": "redirect", "status": "spent"}
    ],
    "activated": false
}
```

#### `get_range_to_target`

Calculate range and arc between two pieces.

```python
# Arguments:
{
    "source_id": "isd-1",
    "target_id": "cr90-1"
}

# Returns:
{
    "range": "medium",
    "distance": 156.7,
    "arc": "front",
    "in_arc": true,
    "obstructed": false
}
```

### Screenshot Tools

#### `screenshot_board`

Capture a screenshot of the current board.

```python
# Arguments:
{
    "max_width": 1920,
    "max_height": 1080
}

# Returns:
{
    "image_url": "data:image/png;base64,...",
    "timestamp": 1704729600000,
    "format": "png"
}
```

### Action Tools

#### `execute_maneuver`

Move a ship at the specified speed.

```python
# Arguments:
{
    "ship_id": "isd-1",
    "speed": 2,
    "yaw": [0, 1, 0],  # Yaw at each joint
    "validate_only": false
}
```

#### `execute_attack`

Execute an attack from one ship to another.

```python
# Arguments:
{
    "attacker_id": "isd-1",
    "defender_id": "cr90-1",
    "arc": "front",
    "dice_modifications": ["concentrate_fire"]
}
```

#### `activate_squadron`

Activate a squadron to move and/or attack.

```python
# Arguments:
{
    "squadron_id": "tie-1",
    "target_position": [150, 300],
    "attack_target": "x-wing-1"
}
```

#### `pass_turn`

Pass the current activation.

```python
# No arguments required
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              LLM (Claude, etc.)              │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol
                  │
┌─────────────────▼───────────────────────────┐
│            MCP Server                        │
│  ┌─────────────────────────────────────┐    │
│  │ server.py                           │    │
│  │ - Tool registration                 │    │
│  │ - Request routing                   │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ tools/game_tools.py                 │    │
│  │ - Board state tools                 │    │
│  │ - Screenshot tools                  │    │
│  │ - Action tools                      │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ vassal_client.py                    │    │
│  │ - HTTP client for Vassal API        │    │
│  └─────────────────────────────────────┘    │
└─────────────────┬───────────────────────────┘
                  │ HTTP/REST
                  │
┌─────────────────▼───────────────────────────┐
│     Java Vassal Integration Server          │
│     (see vassal-integration/)               │
└─────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
ruff check src/
ruff format src/
```

## Benchmark Runner

Run complete games between LLMs:

```bash
# Using default settings (Claude vs Claude)
armadabench-run

# With specific models
armadabench-run --player1-model claude-sonnet-4-20250514 --player2-model gpt-4o

# With a config file
armadabench-run --config configs/sample_run.json --output-dir ./runs
```

### Configuration

Create a run configuration JSON file:

```json
{
  "run_id": "experiment-001",
  "benchmark_type": "full_game",
  "player1": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.7
  },
  "player2": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  }
}
```

### Output

Each run produces:

```
runs/<run_id>/
├── results.json        # Final game results
├── <run_id>_events.json # All logged events
└── run.log             # Detailed log file
```

## Docker Usage

Build and run benchmarks in Docker:

```bash
cd docker

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Build the container
docker-compose build

# Run a single benchmark
docker-compose up runner

# Run multiple benchmarks in parallel
docker-compose up --scale runner=4
```

## Requirements

- Python 3.10+
- Java Vassal Integration server running (see `../vassal-integration/`)
- Vassal with Star Wars Armada module loaded

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ISB_API_URL` | ISB API base URL | `https://api.swarmada.wiki/api/mcp` |
| `VASSAL_API_URL` | Vassal server URL | `http://localhost:8080` |
| `ARMADABENCH_OUTPUT_DIR` | Results directory | `./runs` |
| `ARMADABENCH_LOG_LEVEL` | Logging level | `INFO` |

## Current Limitations

- Maneuver execution returns placeholder (Java integration pending)
- Attack resolution partially implemented
- Squadron engagement detection simplified

These will be addressed as the Java Vassal integration is completed.
