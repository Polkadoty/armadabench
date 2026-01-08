# ArmadaBench MCP Tools Specification

This document provides detailed specifications for all MCP tools that will be exposed to language models.

## Tool Design Principles

1. **Descriptive Names**: Tool names clearly indicate their purpose
2. **Rich Docstrings**: Comprehensive descriptions with examples
3. **Type Safety**: Strong typing for parameters and returns
4. **Error Messages**: Clear, actionable error messages
5. **Validation**: Client-side validation before calling Vassal
6. **Consistency**: Similar operations use similar patterns

---

## Game State Query Tools

### `get_board_state()`

**Purpose**: Get complete current game state

**Parameters**: None

**Returns**:
```typescript
{
  "round": number,
  "phase": "ship_phase" | "squadron_phase" | "status_phase",
  "active_player": "player1" | "player2",
  "ships": [
    {
      "id": string,
      "name": string,
      "owner": "player1" | "player2",
      "position": {"x": number, "y": number},
      "rotation": number,  // degrees, 0 = north
      "speed": number,
      "hull": {"current": number, "maximum": number},
      "shields": {
        "front": {"current": number, "maximum": number},
        "left": {"current": number, "maximum": number},
        "right": {"current": number, "maximum": number},
        "rear": {"current": number, "maximum": number}
      },
      "defense_tokens": [
        {
          "type": "evade" | "brace" | "redirect" | "scatter" | "contain",
          "status": "ready" | "spent" | "exhausted"
        }
      ],
      "command_dials": ["navigate", "squadron", "engineering", "concentrate_fire"],
      "command_tokens": {"navigate": number, "squadron": number, "engineering": number, "concentrate_fire": number},
      "upgrades": [
        {"id": string, "name": string, "type": string, "exhausted": boolean}
      ],
      "damage_cards": [
        {"id": string, "name": string, "face_up": boolean}
      ],
      "activated": boolean,
      "restrictions": {
        "can_activate": boolean,
        "can_attack": boolean,
        "can_move": boolean
      }
    }
  ],
  "squadrons": [
    {
      "id": string,
      "name": string,
      "owner": "player1" | "player2",
      "position": {"x": number, "y": number},
      "hull": {"current": number, "maximum": number},
      "activated": boolean,
      "engaged": boolean,
      "engaged_by": [string],  // squadron IDs
      "restrictions": {
        "can_activate": boolean,
        "can_move": boolean,
        "can_attack": boolean
      }
    }
  ],
  "obstacles": [
    {
      "id": string,
      "type": "asteroid" | "debris",
      "position": {"x": number, "y": number},
      "rotation": number
    }
  ],
  "objectives": {
    "player1": {"id": string, "name": string, "points": number},
    "player2": {"id": string, "name": string, "points": number}
  },
  "score": {
    "player1": number,
    "player2": number
  }
}
```

**Errors**:
- `VASSAL_NOT_CONNECTED`: Vassal integration not available
- `NO_GAME_LOADED`: No game currently loaded in Vassal

---

### `get_ship_details(ship_id: str)`

**Purpose**: Get detailed information about a specific ship

**Parameters**:
- `ship_id` (string, required): Unique identifier for the ship

**Returns**:
```typescript
{
  "id": string,
  "name": string,
  "class": string,  // e.g., "Imperial I-class Star Destroyer"
  "faction": "empire" | "rebel" | "republic" | "separatist",
  "owner": "player1" | "player2",
  "points": number,

  // Current state
  "position": {"x": number, "y": number},
  "rotation": number,
  "speed": number,
  "activated": boolean,

  // Stats
  "hull": {"current": number, "maximum": number},
  "command": number,
  "squadron_value": number,
  "engineering_value": number,

  // Shields by zone
  "shields": {
    "front": {"current": number, "maximum": number},
    "left": {"current": number, "maximum": number},
    "right": {"current": number, "maximum": number},
    "rear": {"current": number, "maximum": number}
  },

  // Armament by zone
  "armament": {
    "front": {"red": number, "blue": number, "black": number},
    "left": {"red": number, "blue": number, "black": number},
    "right": {"red": number, "blue": number, "black": number},
    "rear": {"red": number, "blue": number, "black": number}
  },

  // Defense tokens
  "defense_tokens": [
    {
      "type": "evade" | "brace" | "redirect" | "scatter" | "contain",
      "status": "ready" | "spent" | "exhausted"
    }
  ],

  // Upgrades
  "upgrades": [
    {
      "id": string,
      "name": string,
      "type": "commander" | "officer" | "weapons_team" | "offensive_retrofit" | "defensive_retrofit" | "turbolasers" | "ion_cannons" | "ordnance" | "title",
      "points": number,
      "exhausted": boolean,
      "ability": string
    }
  ],

  // Damage
  "damage_cards": [
    {
      "id": string,
      "name": string,
      "face_up": boolean,
      "effect": string
    }
  ],

  // Available actions
  "available_actions": {
    "can_activate": boolean,
    "can_move": boolean,
    "can_attack": boolean,
    "valid_speeds": [number],
    "attack_targets": [
      {
        "target_id": string,
        "arcs": ["front" | "left" | "right" | "rear"],
        "range": "close" | "medium" | "long" | "extreme"
      }
    ]
  }
}
```

**Errors**:
- `SHIP_NOT_FOUND`: No ship with given ID exists

---

### `get_squadron_details(squadron_id: str)`

**Purpose**: Get detailed information about a specific squadron

**Parameters**:
- `squadron_id` (string, required): Unique identifier for the squadron

**Returns**:
```typescript
{
  "id": string,
  "name": string,
  "type": string,  // e.g., "TIE Fighter Squadron"
  "faction": "empire" | "rebel" | "republic" | "separatist",
  "owner": "player1" | "player2",
  "points": number,
  "unique": boolean,

  // Current state
  "position": {"x": number, "y": number},
  "hull": {"current": number, "maximum": number},
  "activated": boolean,
  "engaged": boolean,
  "engaged_by": [string],  // squadron IDs

  // Stats
  "speed": number,
  "anti_squadron": number,
  "anti_ship": number,
  "defense_tokens": [
    {
      "type": "evade" | "brace" | "scatter",
      "status": "ready" | "spent" | "exhausted"
    }
  ],

  // Keywords
  "keywords": [string],  // e.g., ["Swarm", "Bomber"]

  // Available actions
  "available_actions": {
    "can_activate": boolean,
    "can_move": boolean,
    "can_attack_squadron": boolean,
    "can_attack_ship": boolean,
    "must_attack_engaged": boolean
  }
}
```

---

### `get_range_and_arc(source_id: str, target_id: str)`

**Purpose**: Calculate range and arc from one piece to another

**Parameters**:
- `source_id` (string, required): ID of attacking/measuring piece
- `target_id` (string, required): ID of target piece

**Returns**:
```typescript
{
  "range": "close" | "medium" | "long" | "extreme" | "out_of_range",
  "distance_mm": number,
  "in_arc": {
    "front": boolean,
    "left": boolean,
    "right": boolean,
    "rear": boolean
  },
  "line_of_sight": boolean,
  "obstructed_by": [string],  // IDs of obstacles
  "can_attack": boolean,
  "notes": [string]  // e.g., ["Target in front arc", "Obstructed by asteroid"]
}
```

---

### `get_available_activations()`

**Purpose**: Get list of pieces that can be activated

**Parameters**: None

**Returns**:
```typescript
{
  "ships": [
    {
      "id": string,
      "name": string,
      "command_value": number,
      "priority": number  // higher = recommended to activate earlier
    }
  ],
  "squadrons": [
    {
      "id": string,
      "name": string,
      "engaged": boolean
    }
  ],
  "phase": "ship_phase" | "squadron_phase"
}
```

---

## Movement & Positioning Tools

### `predict_ship_position(ship_id: str, maneuver: object)`

**Purpose**: Predict final position of ship after maneuver without executing

**Parameters**:
- `ship_id` (string, required): Ship to predict for
- `maneuver` (object, required):
  ```typescript
  {
    "speed": number,  // 1-4 for most ships
    "joint": "straight" | "left_1" | "left_2" | "right_1" | "right_2"
  }
  ```

**Returns**:
```typescript
{
  "predicted_position": {"x": number, "y": number},
  "predicted_rotation": number,
  "valid": boolean,
  "warnings": [
    {
      "type": "collision" | "off_board" | "invalid_speed",
      "message": string,
      "object_id": string  // if collision
    }
  ],
  "collisions": [
    {
      "object_id": string,
      "object_type": "ship" | "squadron" | "obstacle",
      "collision_point": {"x": number, "y": number}
    }
  ],
  "final_speed": number  // may be reduced by collision
}
```

**Example Usage**:
```python
# LLM wants to move ISD forward at speed 2
result = await predict_ship_position(
    ship_id="isd-1",
    maneuver={"speed": 2, "joint": "straight"}
)

if result["valid"] and not result["collisions"]:
    # Safe to execute
    await execute_maneuver(ship_id="isd-1", maneuver={"speed": 2, "joint": "straight"})
```

---

### `execute_maneuver(ship_id: str, maneuver: object)`

**Purpose**: Execute ship maneuver

**Parameters**:
- `ship_id` (string, required): Ship to move
- `maneuver` (object, required):
  ```typescript
  {
    "speed": number,
    "joint": "straight" | "left_1" | "left_2" | "right_1" | "right_2"
  }
  ```

**Returns**:
```typescript
{
  "success": boolean,
  "final_position": {"x": number, "y": number},
  "final_rotation": number,
  "final_speed": number,
  "collisions": [
    {
      "object_id": string,
      "object_type": "ship" | "squadron" | "obstacle",
      "damage_to_self": number,
      "damage_to_other": number
    }
  ],
  "effects_triggered": [
    {
      "type": string,  // e.g., "asteroid_damage", "debris_damage"
      "description": string
    }
  ]
}
```

**Errors**:
- `SHIP_ALREADY_ACTIVATED`: Ship has already been activated this round
- `INVALID_SPEED`: Speed outside ship's allowed range
- `SHIP_NOT_ACTIVATED`: Ship hasn't been activated yet (must activate first)

---

### `move_squadron(squadron_id: str, position: object)`

**Purpose**: Move squadron to new position

**Parameters**:
- `squadron_id` (string, required): Squadron to move
- `position` (object, required):
  ```typescript
  {
    "x": number,
    "y": number
  }
  ```

**Returns**:
```typescript
{
  "success": boolean,
  "final_position": {"x": number, "y": number},
  "distance_moved": number,
  "engaged_status": boolean,
  "engaged_by": [string]  // squadron IDs
}
```

**Errors**:
- `SQUADRON_ALREADY_ACTIVATED`: Squadron already activated
- `SQUADRON_ENGAGED`: Squadron is engaged and cannot move (unless has Grit)
- `MOVE_TOO_FAR`: Distance exceeds squadron speed

---

## Combat Tools

### `execute_attack(attacker_id: str, defender_id: str, arc: str, options: object)`

**Purpose**: Execute attack from one piece to another

**Parameters**:
- `attacker_id` (string, required): ID of attacking piece
- `defender_id` (string, required): ID of defending piece
- `arc` (string, required): Firing arc ("front", "left", "right", "rear")
- `options` (object, optional):
  ```typescript
  {
    "concentrate_fire": boolean,
    "dice_modifications": [
      {
        "type": "reroll" | "add_die" | "change_die",
        "source": string,  // upgrade or effect name
        "details": object
      }
    ]
  }
  ```

**Returns**:
```typescript
{
  "success": boolean,
  "attack_type": "ship" | "squadron",
  "arc": string,
  "range": string,
  "dice_pool": {
    "red": number,
    "blue": number,
    "black": number
  },
  "dice_results": {
    "initial": {
      "hit": number,
      "crit": number,
      "accuracy": number,
      "blank": number
    },
    "after_modifications": {
      "hit": number,
      "crit": number,
      "accuracy": number,
      "blank": number
    },
    "modifications_used": [string]
  },
  "defense": {
    "tokens_spent": [string],
    "evade_count": number,
    "scatter_used": boolean,
    "brace_used": boolean,
    "redirect_used": boolean
  },
  "damage": {
    "total": number,
    "shields_lost": number,
    "hull_damage": number,
    "critical_effects": [
      {
        "card_id": string,
        "name": string,
        "face_up": boolean,
        "effect": string
      }
    ]
  },
  "defender_destroyed": boolean
}
```

**Errors**:
- `OUT_OF_RANGE`: Target not in range
- `NOT_IN_ARC`: Target not in specified arc
- `NO_LINE_OF_SIGHT`: Target blocked by terrain
- `ALREADY_ATTACKED`: Attacker already attacked this activation

---

### `spend_defense_token(ship_id: str, token_type: str, context: object)`

**Purpose**: Spend a defense token (used during attack resolution)

**Parameters**:
- `ship_id` (string, required): Ship spending token
- `token_type` (string, required): "evade", "brace", "redirect", "scatter", "contain"
- `context` (object, required):
  ```typescript
  {
    "attack_id": string,  // Reference to ongoing attack
    "redirect_to": "left" | "right" | "front" | "rear"  // if redirect token
  }
  ```

**Returns**:
```typescript
{
  "success": boolean,
  "token_spent": string,
  "new_status": "spent" | "exhausted",
  "effect_applied": string
}
```

---

## List Building Tools

### `search_cards(query: str, filters: object)`

**Purpose**: Search card database

**Parameters**:
- `query` (string, optional): Text search in card name or text
- `filters` (object, optional):
  ```typescript
  {
    "type": "ship" | "squadron" | "upgrade_commander" | "upgrade_officer" | etc.,
    "faction": "empire" | "rebel" | "republic" | "separatist",
    "min_cost": number,
    "max_cost": number,
    "unique": boolean,
    "keywords": [string]
  }
  ```

**Returns**:
```typescript
{
  "results": [
    {
      "id": string,
      "name": string,
      "type": string,
      "faction": string,
      "points": number,
      "unique": boolean,
      "short_description": string
    }
  ],
  "total_count": number,
  "query_time_ms": number
}
```

---

### `get_card_details(card_id: str)`

**Purpose**: Get full details for a card

**Parameters**:
- `card_id` (string, required): Card identifier

**Returns** (example for ship):
```typescript
{
  "id": string,
  "name": string,
  "type": "ship",
  "faction": "empire",
  "points": 110,
  "unique": false,

  // Ship stats
  "hull": 11,
  "command": 3,
  "squadron": 4,
  "engineering": 5,
  "shields": {"front": 4, "left": 3, "right": 3, "rear": 2},
  "armament": {
    "front": {"red": 3, "blue": 1, "black": 0},
    "left": {"red": 2, "blue": 1, "black": 0},
    "right": {"red": 2, "blue": 1, "black": 0},
    "rear": {"red": 2, "blue": 0, "black": 0}
  },
  "defense_tokens": ["evade", "brace", "redirect", "redirect"],
  "speed_chart": {
    "1": ["straight"],
    "2": ["straight", "left_1", "right_1"],
    "3": ["straight", "left_1", "right_1"]
  },
  "upgrade_slots": [
    "commander", "officer", "weapons_team", "offensive_retrofit",
    "defensive_retrofit", "turbolasers", "ion_cannons", "ordnance"
  ],

  "ability": string,
  "restrictions": [string],
  "errata": [string]
}
```

---

### `create_fleet(faction: str, point_limit: int, name: str)`

**Purpose**: Start building a new fleet

**Parameters**:
- `faction` (string, required): "empire", "rebel", "republic", "separatist"
- `point_limit` (number, required): Point limit (typically 400)
- `name` (string, optional): Fleet name

**Returns**:
```typescript
{
  "fleet_id": string,
  "faction": string,
  "point_limit": number,
  "current_points": 0,
  "name": string,
  "ships": [],
  "squadrons": [],
  "objectives": []
}
```

---

### `add_ship_to_fleet(fleet_id: str, ship_card_id: str)`

**Purpose**: Add a ship to fleet

**Parameters**:
- `fleet_id` (string, required): Fleet being built
- `ship_card_id` (string, required): Ship card to add

**Returns**:
```typescript
{
  "success": boolean,
  "fleet": {...},  // updated fleet
  "ship_instance_id": string,
  "warnings": [string],
  "errors": [string]
}
```

**Errors**:
- `POINTS_EXCEEDED`: Adding ship would exceed point limit
- `DUPLICATE_UNIQUE`: Unique ship already in fleet
- `FACTION_MISMATCH`: Ship not available to this faction

---

### `add_upgrade_to_ship(fleet_id: str, ship_instance_id: str, upgrade_card_id: str)`

**Purpose**: Add upgrade card to ship in fleet

**Parameters**:
- `fleet_id` (string, required): Fleet being built
- `ship_instance_id` (string, required): Specific ship instance in fleet
- `upgrade_card_id` (string, required): Upgrade card to add

**Returns**:
```typescript
{
  "success": boolean,
  "fleet": {...},
  "warnings": [string],
  "errors": [string]
}
```

**Errors**:
- `NO_SLOT_AVAILABLE`: Ship doesn't have a slot for this upgrade type
- `SLOT_OCCUPIED`: Slot already filled
- `RESTRICTION_VIOLATION`: Upgrade has restriction not met
- `POINTS_EXCEEDED`: Would exceed point limit

---

### `validate_fleet(fleet_id: str)`

**Purpose**: Validate complete fleet for legality

**Parameters**:
- `fleet_id` (string, required): Fleet to validate

**Returns**:
```typescript
{
  "valid": boolean,
  "points": {
    "ships": number,
    "squadrons": number,
    "total": number,
    "limit": number
  },
  "errors": [
    {
      "severity": "error" | "warning",
      "message": string,
      "location": string  // e.g., "ship-2, upgrade-3"
    }
  ],
  "suggestions": [string]
}
```

---

### `export_fleet_to_vassal(fleet_id: str)`

**Purpose**: Export fleet to format loadable in Vassal

**Parameters**:
- `fleet_id` (string, required): Fleet to export

**Returns**:
```typescript
{
  "success": boolean,
  "vassal_format": string,  // Format depends on Shrimpbot/module
  "loaded": boolean,  // If true, already loaded into current Vassal game
  "fleet_summary": {
    "name": string,
    "faction": string,
    "points": number,
    "ship_count": number,
    "squadron_count": number
  }
}
```

---

## Analysis & Helper Tools

### `calculate_dice_probabilities(pool: object, modifications: array)`

**Purpose**: Calculate attack outcome probabilities

**Parameters**:
- `pool` (object, required):
  ```typescript
  {
    "red": number,
    "blue": number,
    "black": number
  }
  ```
- `modifications` (array, optional): Available modifications like rerolls, adds

**Returns**:
```typescript
{
  "expected_damage": number,
  "probability_distribution": {
    "0": 0.05,
    "1": 0.15,
    "2": 0.25,
    // ...
  },
  "expected_accuracies": number,
  "crit_probability": number,
  "recommendations": [string]  // e.g., "Reroll blue dice for best expected value"
}
```

---

### `analyze_board_position()`

**Purpose**: Get tactical analysis of current board state

**Parameters**: None

**Returns**:
```typescript
{
  "board_control": {
    "player1": number,  // 0-100 score
    "player2": number
  },
  "threats": [
    {
      "attacker_id": string,
      "defender_id": string,
      "threat_level": "low" | "medium" | "high" | "critical",
      "expected_damage": number,
      "can_attack_this_round": boolean
    }
  ],
  "objectives": {
    "player1_scoring": boolean,
    "player2_scoring": boolean,
    "current_advantage": "player1" | "player2" | "tied"
  },
  "tactical_suggestions": [
    {
      "priority": number,
      "suggestion": string,
      "reasoning": string
    }
  ]
}
```

**Note**: This is a more advanced tool that could be disabled for harder benchmarks

---

### `get_game_history(limit: int)`

**Purpose**: Get history of actions taken in current game

**Parameters**:
- `limit` (number, optional): Number of recent actions to return (default: 20)

**Returns**:
```typescript
{
  "actions": [
    {
      "round": number,
      "phase": string,
      "player": "player1" | "player2",
      "timestamp": string,
      "action_type": "activate" | "move" | "attack" | "spend_token",
      "details": object,
      "result": object
    }
  ],
  "total_actions": number
}
```

---

## Utility Tools

### `screenshot_board(options: object)`

**Purpose**: Capture visual state of board

**Parameters**:
- `options` (object, optional):
  ```typescript
  {
    "perspective": "overhead" | "player1" | "player2",
    "annotate": boolean,  // Add labels and overlays
    "highlight_ships": [string],  // Ship IDs to highlight
    "show_ranges": boolean,
    "show_arcs": boolean,
    "show_movement_options": string  // Ship ID to show movement for
  }
  ```

**Returns**:
```typescript
{
  "image_url": string,  // data: URL with base64 encoded image
  "timestamp": string,
  "board_state_snapshot": {...},  // Matching board state
  "annotations": [
    {
      "type": "label" | "arc" | "range" | "highlight",
      "position": {"x": number, "y": number},
      "content": string
    }
  ]
}
```

---

### `reset_game()`

**Purpose**: Reset Vassal to start a new game

**Parameters**: None

**Returns**:
```typescript
{
  "success": boolean,
  "message": string
}
```

---

### `load_scenario(scenario_id: str)`

**Purpose**: Load a predefined test scenario

**Parameters**:
- `scenario_id` (string, required): ID of scenario to load

**Returns**:
```typescript
{
  "success": boolean,
  "scenario": {
    "id": string,
    "name": string,
    "description": string,
    "objectives": [string]
  },
  "board_state": {...}
}
```

---

## MCP Resources

### `card_database`

**URI**: `armadabench://cards`

**Description**: Complete database of all Star Wars Armada cards

**Schema**:
```typescript
{
  "ships": [...],
  "squadrons": [...],
  "upgrades": {
    "commander": [...],
    "officer": [...],
    "weapons_team": [...],
    // ... all upgrade types
  },
  "objectives": [...],
  "metadata": {
    "version": string,
    "last_updated": string,
    "total_cards": number
  }
}
```

---

### `rules_reference`

**URI**: `armadabench://rules`

**Description**: Star Wars Armada rules reference

**Schema**:
```typescript
{
  "sections": [
    {
      "title": string,
      "content": string,
      "subsections": [...]
    }
  ],
  "faq": [...],
  "errata": [...],
  "timing_chart": {...}
}
```

---

## Tool Call Sequences

### Example 1: Execute Ship Activation

```python
# 1. Get available activations
activations = await get_available_activations()

# 2. Choose ship to activate
ship_id = "isd-1"

# 3. Get ship details
ship = await get_ship_details(ship_id)

# 4. Predict movement
prediction = await predict_ship_position(
    ship_id=ship_id,
    maneuver={"speed": 2, "joint": "straight"}
)

# 5. Execute movement if safe
if prediction["valid"]:
    move_result = await execute_maneuver(
        ship_id=ship_id,
        maneuver={"speed": 2, "joint": "straight"}
    )

# 6. Check attack options
board_state = await get_board_state()
for target in board_state["ships"]:
    if target["owner"] == "player2":
        range_arc = await get_range_and_arc(ship_id, target["id"])
        if range_arc["can_attack"]:
            # Attack!
            attack_result = await execute_attack(
                attacker_id=ship_id,
                defender_id=target["id"],
                arc=range_arc["in_arc"]["front"] and "front" or "left"
            )
```

### Example 2: Build Fleet

```python
# 1. Create new fleet
fleet = await create_fleet(
    faction="empire",
    point_limit=400,
    name="My Imperial Fleet"
)

# 2. Search for flagship
ships = await search_cards(
    query="Star Destroyer",
    filters={"type": "ship", "faction": "empire"}
)

# 3. Add flagship
await add_ship_to_fleet(
    fleet_id=fleet["fleet_id"],
    ship_card_id="isd-ii"
)

# 4. Search for commander
commanders = await search_cards(
    filters={"type": "upgrade_commander", "faction": "empire"}
)

# 5. Add upgrades
await add_upgrade_to_ship(
    fleet_id=fleet["fleet_id"],
    ship_instance_id="ship-1",
    upgrade_card_id="vader-commander"
)

# 6. Validate
validation = await validate_fleet(fleet_id=fleet["fleet_id"])

# 7. Export to Vassal
await export_fleet_to_vassal(fleet_id=fleet["fleet_id"])
```

---

## Error Handling

All tools should return errors in consistent format:

```typescript
{
  "error": {
    "code": string,
    "message": string,
    "details": object,
    "suggestion": string  // What the LLM should try instead
  }
}
```

Common error codes:
- `VASSAL_NOT_CONNECTED`
- `INVALID_PARAMETER`
- `SHIP_NOT_FOUND`
- `ILLEGAL_ACTION`
- `POINTS_EXCEEDED`
- `GAME_STATE_ERROR`

---

## Tool Testing

Each tool should have:
1. **Unit tests** - Test tool logic
2. **Integration tests** - Test with mock Vassal
3. **E2E tests** - Test with real Vassal
4. **LLM tests** - Test with actual LLM calling tools

Example test:
```python
async def test_get_ship_details():
    # Setup mock game state
    await load_scenario("basic_test")

    # Call tool
    ship = await get_ship_details("isd-1")

    # Assertions
    assert ship["name"] == "Imperial I-class Star Destroyer"
    assert ship["hull"]["maximum"] == 11
    assert "commander" in ship["upgrade_slots"]
```
