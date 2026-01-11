# Vlog Loading Implementation

## Overview

Successfully implemented loading of Star Forge exported `.vlog` fleet files into the Vassal-based ArmadaBench system. This allows fleets created in the Star Forge fleet builder to be imported directly into Vassal for benchmarking.

## Technical Details

### Vlog File Format

Vlog files are zip archives containing:
- `moduledata` - Module version info
- `savedata` - Save metadata
- `savedGame` - The actual game state (obfuscated)

### Obfuscation Format

The `savedGame` entry uses Vassal's obfuscation:
- Header: `!VCSK` (5 bytes)
- Key: 2 hex characters representing the XOR key
- Content: Each byte XOR'd with the key, encoded as 2 hex characters

Decoded using `VASSAL.tools.io.DeobfuscatingInputStream`.

### Command Structure

After deobfuscation, commands are separated by ESC (char 27):
```
begin_save[ESC]end_save[ESC]LOG[TAB]CHAT...[ESC]LOG[TAB]+/pieceId/...[ESC]...
```

Command types:
- `begin_save` → `SetupCommand(false)`
- `end_save` → `SetupCommand(true)`
- `LOG[TAB]...` → `LogCommand` wrapping actual commands
- `+/...` → `AddPiece` command (piece placement)

### Key Implementation Challenges

1. **SetupCommand blocks on wizard**: The `SetupCommand.execute()` calls `setup(true)` which shows a wizard dialog, blocking in headless mode. Solution: Skip SetupCommand and only execute the wrapped commands.

2. **LogCommand wraps actual commands**: `LogCommand.executeCommand()` is empty - the actual command is in the `logged` field. Solution: Use `getLoggedCommand()` to extract and execute the underlying command.

3. **Recursive command extraction**: Commands are nested (SetupCommand → LogCommand → AddPiece). Solution: Recursive `collectExecutableCommands()` method.

## API Endpoint

```
POST /api/game/load?path=/app/saves/fleet.vlog
```

Response:
```json
{
  "success": true,
  "message": "success: Loaded 39 commands",
  "piece_count": 37,
  "game_started": false,
  "path": "/app/saves/fleet.vlog"
}
```

## Test Results

| File | Pieces | Commands | Ships | Squadrons |
|------|--------|----------|-------|-----------|
| Texas_Champs_Yularen_Fleet.vlog | 37 | 39 | 5 | 5 |
| Truthi_Worlds_List.vlog | 71 | 36 | - | - |

## Ship/Squadron Detection

Updated `isShipPiece()` to handle various naming conventions:
- `-class)` or `-class ` patterns
- Ship type endings: "ship", "cruiser", "frigate", etc.
- Specific names: "acclamator", "venator", "victory i", etc.

## Code Location

Main implementation in:
- `vassal-extension/src/main/java/com/armadabench/extension/EmbeddedApiServer.java`
  - `handleLoadGame()` - API endpoint handler
  - `collectExecutableCommands()` - Recursive command extraction

## Usage

1. Export fleet from Star Forge as .vlog
2. Copy to `docker/saves/` directory
3. Call load API endpoint
4. Query state with `/api/state`

## Remaining Work

- [ ] Fix board background display (pieces stacked at origin)
- [ ] Implement piece movement API endpoint
- [ ] Set up MCP server Python component
