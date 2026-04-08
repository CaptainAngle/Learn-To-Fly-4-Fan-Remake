# Learn to Fly 4 - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       MAIN GAME LOOP                        │
│                      (game.py - Game)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input Handler ──→ State Manager ──→ Update Logic ──→ Draw  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         ↓              ↓              ↓              ↓
    ┌────────┐    ┌──────────┐   ┌─────────┐   ┌──────────┐
    │ Player │    │Environment   │ Mission │   │   UI     │
    │ (phys) │    │ (terrain)    │ Manager │   │ (render) │
    └────────┘    └──────────┘   └─────────┘   └──────────┘
         ↓              ↓              ↓              ↓
    ┌────────────────────────────────────────────────────┐
    │         Save System (Persistence Layer)            │
    └────────────────────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────────────────────┐
    │              data/save.json (Disk)                 │
    └────────────────────────────────────────────────────┘
```

## Module Responsibilities

### `constants.py`
- **Purpose**: Define all game constants, gear statistics, and configurations
- **Key Constants**:
  - Screen dimensions (1200x800)
  - Physics parameters (gravity, wind, max velocity)
  - Game states (MENU, PLAYING, UPGRADE, etc.)
  - Gear definitions with stats
  - Color palette

### `player.py`
- **Class**: `Player`
- **Responsibilities**:
  - Manage player position and velocity
  - Apply physics (gravity, thrust, wind effects)
  - Track flight statistics (distance, fuel, coins)
  - Handle gear equipping
  - Render player sprite
  - Detect landing

### `environment.py`
- **Classes**: `Terrain`, `Hazard`, `Environment`
- **Responsibilities**:
  - Generate procedural terrain
  - Manage wind simulation
  - Spawn and track hazards
  - Handle collisions
  - Render all environmental elements
  - Provide height data at any X coordinate

### `mission.py`
- **Classes**: `Mission`, `MissionManager`
- **Responsibilities**:
  - Define individual missions with targets and rewards
  - Track mission completion status
  - Check completion criteria
  - Manage mission selection
  - Calculate rewards

### `save_system.py`
- **Class**: `SaveSystem`
- **Responsibilities**:
  - Load/save game state to JSON
  - Manage save file location
  - Provide default save structure
  - Handle file I/O errors

### `ui.py`
- **Classes**: `Button`, `UIManager`
- **Responsibilities**:
  - Render all UI elements (buttons, text, progress bars)
  - Handle button interaction (hover/click detection)
  - Draw different screens (menu, mission select, upgrade, results)
  - Display in-game HUD elements

### `game.py`
- **Class**: `Game`
- **Responsibilities**:
  - Main game loop (60 FPS)
  - State machine management
  - Input handling
  - Object initialization and lifecycle
  - Save/load coordination
  - Screen-to-screen navigation

---

## State Machine Flow

```
START
  ↓
[MENU] ← ESC
  ├─→ "Start Flight" → [MISSION_SELECT]
  │                          ├─→ "Select Mission" → [PLAYING]
  │                          │                         ├─→ Landed → [RESULTS]
  │                          │                         ├─→ Crashed → [RESULTS]
  │                          │                         └─→ ESC → [MENU]
  │                          └─→ "Back" → [MENU]
  │
  ├─→ "Gear Shop" → [UPGRADE]
  │                    ├─→ "Buy/Equip Gear" → [UPGRADE]
  │                    └─→ "Back" → [MENU]
  │
  ├─→ "Settings" → [SETTINGS] (TODO)
  │
  └─→ "Quit" → EXIT
```

---

## Data Flow Examples

### Flying Process
```
handle_input()
  ├─→ Get keyboard input (SPACE, LEFT, RIGHT)
  └─→ Return controls dict

update()
  ├─→ player.update(controls, wind)
  │    ├─→ Apply thrust if SPACE pressed
  │    ├─→ Apply rotation from LEFT/RIGHT
  │    ├─→ Apply gravity
  │    ├─→ Apply wind force
  │    ├─→ Update position
  │    └─→ Track distance traveled
  │
  ├─→ environment.update()
  │    └─→ Update wind simulation
  │
  └─→ Check end conditions:
       ├─→ Landing → calculate rewards
       ├─→ Hazard collision → crash
       └─→ Off-screen → success
```

### Mission Completion Flow
```
Flight Ends (landed/crashed)
  ├─→ Calculate distance
  ├─→ Check mission.check_completion(distance)
  │    └─→ If distance ≥ target: mission.completed = True
  ├─→ Calculate coins:
  │    ├─→ Base coins = floor(distance / 100)
  │    └─→ Bonus = mission.reward_coins (if completed)
  ├─→ Update player.coins
  ├─→ Update game_data
  ├─→ save_game() → JSON file
  └─→ Show RESULTS screen
```

### Gear Purchase Flow
```
User clicks "Buy Gear"
  ├─→ Check if owned
  │    ├─→ YES: equip gear
  │    └─→ NO: Check coins ≥ cost
  │            ├─→ YES: Deduct coins, add to unlocked
  │            └─→ NO: Show error (TODO)
  ├─→ Update game_data
  ├─→ Update player stats
  └─→ save_game() → JSON file
```

---

## Physics System

### Movement Calculation
```
1. Check input → get thrust vector
2. Apply thrust: vy -= thrust * acceleration_multiplier
3. Apply gravity: vy += GRAVITY / glide_multiplier
4. Apply wind: vx += wind_speed
5. Cap velocity: scale if > max_speed
6. Update position: x += vx, y += vy
7. Track distance: distance_traveled += vx (if positive)
```

### Collision Detection
```
For each hazard:
  distance = sqrt((player.x - hazard.x)² + (player.y - hazard.y)²)
  if distance < (player.size + hazard.size):
    return True (collision)
```

### Landing Detection
```
terrain_y = get_ground_y_at(player.x)
if player.y + player.size >= terrain_y:
  player.is_landed = True
  player.y = terrain_y - player.size
```

---

## Event Handling

### Keyboard Events
| Event | Handler | Effect |
|-------|---------|--------|
| SPACE/UP/W | `handle_input()` → `player.update()` | Thrust |
| LEFT/A | `handle_input()` → `player.update()` | Bank left |
| RIGHT/D | `handle_input()` → `player.update()` | Bank right |
| ESC | `handle_input()` → state change | Return to menu |
| QUIT | `handle_input()` | Exit game |

### Mouse Events
| Event | Handler | Effect |
|-------|---------|--------|
| Click on button | `handle_click()` → button.is_clicked() | Navigate/action |
| Hover on button | `button.update()` | Visual feedback |

---

## Performance Considerations

### Optimization Techniques
1. **Wind particles**: Limited to 50 particles max, cleared each frame
2. **Hazard checking**: Only active hazards checked for collision
3. **Terrain interpolation**: Linear interpolation instead of full recalculation
4. **Drawing**: Only visible elements drawn (clipping on screen bounds)

### Frame Budget (60 FPS = ~16.67ms per frame)
- **Input**: ~1ms
- **Update**: ~3-5ms (physics, hazard checks, state logic)
- **Draw**: ~8-10ms (terrain rendering, sprites, UI)
- **Buffer**: ~2-3ms headroom

---

## Extensibility Points

### Adding New Missions
```python
# In mission.py MissionManager.create_default_missions()
Mission(id, name, description, type, target_value, reward_coins)
```

### Adding New Gear
```python
# In constants.py GEAR_TYPES
"new_gear": {
    "speed": 1.5,
    "acceleration": 1.2,
    "glide": 1.0,
    "fuel": 100,
    "cost": 700
}
```

### Adding New Game States
```python
# In constants.py add STATE_NAME = "name"
# In game.py handle_click() add state branch
# In game.py draw() add render logic
```

### Adding New Hazard Types
```python
# In environment.py Hazard.__init__() add type
# In Hazard.draw() add rendering logic
# In Hazard.check_collision() update collision logic
```

---

## Testing Checklist

- [x] Game initializes without errors
- [x] Main menu displays and buttons respond
- [x] Mission select shows all 5 missions
- [x] Flight controls respond (thrust, steering)
- [x] Physics behave predictably
- [x] Hazards appear and collide properly
- [x] Landing detection works
- [x] Coins are earned correctly
- [x] Save file is created and persists
- [x] Gear can be purchased and equipped
- [x] Mission completion is tracked
- [x] UI renders correctly at all screen sizes

---

**Architecture Version**: 1.0  
**Last Updated**: April 7, 2026  
**Status**: Production Ready (MVP)

