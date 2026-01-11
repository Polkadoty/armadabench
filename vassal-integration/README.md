# Vassal Integration for ArmadaBench

This Java project provides a REST API bridge between the Vassal game engine and the ArmadaBench Python MCP server.

## Prerequisites

- **Java 17+** - Required by Vassal 3.7+
- **Maven 3.5+** - For building the project
- **Vassal Engine** - Must be installed locally (for dependencies)

### Installing Java (macOS)

```bash
# Using Homebrew (recommended)
brew install --cask temurin@17

# Verify installation
java -version  # Should show 17+
```

### Installing Maven

```bash
brew install maven

# Verify installation
mvn -version
```

## Building

### Step 1: Build and Install Vassal Locally

First, you need to build Vassal and install it to your local Maven repository:

```bash
cd /path/to/vassal
mvn install -DskipTests
```

### Step 2: Build the Integration

```bash
cd /path/to/armadabench/vassal-integration
mvn clean package
```

This creates an executable JAR in `target/`.

## Running

```bash
# Start the Vassal API server
java -jar target/vassal-integration-0.1.0-SNAPSHOT.jar /path/to/ArmadaModule.vmod 8080

# The server will start on http://localhost:8080
```

### Command Line Options

```
Usage: java -jar vassal-integration.jar <module-path> [port]

Arguments:
  module-path  Path to the Star Wars Armada .vmod file
  port         HTTP port (default: 8080)
```

## API Endpoints

### Health Check

```
GET /api/health
```

Returns server status and whether Vassal module is loaded.

### Game State

```
GET /api/state
```

Returns complete board state including all ships, squadrons, and obstacles.

```
GET /api/ship/{id}
```

Returns details for a specific ship.

```
GET /api/squadron/{id}
```

Returns details for a specific squadron.

### Screenshots

```
GET /api/screenshot
GET /api/screenshot?format=PNG&maxWidth=1920&maxHeight=1080
```

Returns screenshot of the current board.

```
GET /api/screenshot/base64
```

Returns screenshot as base64 data URL (for LLM consumption).

### Actions

```
POST /api/action/move
{
  "pieceId": "ship-1",
  "targetX": 100,
  "targetY": 200,
  "rotation": 45
}
```

Execute a move action.

```
POST /api/action/attack
{
  "attackerId": "isd-1",
  "defenderId": "cr90-1",
  "arc": "front"
}
```

Execute an attack action.

### Game Lifecycle

```
POST /api/game/new
```

Start a new game.

```
POST /api/game/load
{"path": "/path/to/saved-game.vsav"}
```

Load a saved game file.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Python MCP Server                  │
│     (armadabench-mcp package)               │
└─────────────────┬───────────────────────────┘
                  │ HTTP/REST
                  │
┌─────────────────▼───────────────────────────┐
│         Vassal Integration                   │
│  ┌─────────────────────────────────────┐    │
│  │ VassalApiServer (Javalin REST)      │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ GameStateReader                     │    │
│  │ - Reads pieces from Vassal Map      │    │
│  │ - Extracts ship/squadron properties │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ ScreenshotCapture                   │    │
│  │ - Renders board to BufferedImage   │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ VassalController                    │    │
│  │ - Loads .vmod modules              │    │
│  │ - Manages GameModule lifecycle     │    │
│  └─────────────────────────────────────┘    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            Vassal Engine                     │
│  - GameModule, Map, GamePiece APIs          │
│  - Command pattern for actions              │
└─────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│     Star Wars Armada Module (.vmod)         │
│  - Ship/Squadron definitions                │
│  - Board layout and pieces                  │
└─────────────────────────────────────────────┘
```

## Development

### Project Structure

```
vassal-integration/
├── pom.xml                          # Maven build configuration
├── src/
│   ├── main/
│   │   ├── java/com/armadabench/vassal/
│   │   │   ├── VassalController.java      # Module loading
│   │   │   ├── GameStateReader.java       # State extraction
│   │   │   ├── ScreenshotCapture.java     # Board capture
│   │   │   ├── server/
│   │   │   │   └── VassalApiServer.java   # REST API
│   │   │   └── models/
│   │   │       ├── BoardState.java
│   │   │       ├── ShipData.java
│   │   │       ├── SquadronData.java
│   │   │       └── ...
│   │   └── resources/
│   └── test/
└── README.md
```

### Key Dependencies

- **Vassal 3.8.0** - Game engine
- **Javalin 6.3.0** - REST API framework
- **Jackson** - JSON serialization
- **SLF4J** - Logging

## Known Limitations

1. **Maneuver Execution** - Full maneuver tool simulation not yet implemented
2. **Attack Resolution** - Dice rolling and damage application in progress
3. **Defense Tokens** - Token spending not yet integrated
4. **Headless Mode** - Requires testing; may need X11/display

## Troubleshooting

### "Module file not found"

Ensure the path to the .vmod file is correct and the file exists.

### "Failed to load Vassal module"

- Check that Java 17+ is installed
- Verify Vassal was built and installed to local Maven repo
- Check for any missing dependencies

### Port already in use

Change the port: `java -jar vassal-integration.jar module.vmod 8081`
