# Learn to Fly 4: Skyward Evolution

A physics-based flight simulator game inspired by classic Flash browser games. Guide your character to break flight records, unlock advanced flight gear, and complete challenging missions!

## Features

- **Dynamic Flight Physics** — Gravity, wind, momentum, and gliding mechanics create a challenging flight experience
- **Multiple Flight Gear** — Unlock and equip different flight equipment with unique stat trade-offs:
  - Base Flight (balanced starter)
  - Jetpack MK1 (high speed, low glide)
  - Wingsuit (excellent glide, lower acceleration)
  - Rocket Boots (maximum speed, minimal fuel)
  - Propeller Hat (balanced advanced gear)

- **Mission System** — Complete distance challenges to earn coins and rewards
- **Upgrade Shop** — Purchase new flight gear with earned coins
- **Procedurally Generated Terrain** — Each flight features unique rolling hills and obstacles
- **Persistent Save System** — Your progress is automatically saved

## How to Play

### Controls
- **SPACE / UP ARROW / W** — Thrust/Fly upward
- **LEFT ARROW / A** — Bank left (rotate)
- **RIGHT ARROW / D** — Bank right (rotate)
- **ESC** — Return to menu during flight

### Game Flow
1. **Main Menu** → Select "Start Flight"
2. **Mission Select** → Choose a distance challenge
3. **Flying** → Use physics to reach the target distance
4. **Results** → Earn coins based on distance traveled
5. **Upgrade Shop** → Purchase new gear or return to menu

### Tips for Success
- **Manage Fuel** — Each gear has different fuel capacity. Higher-speed gear burns fuel faster.
- **Use Thermals** — Wind currents help or hinder flight depending on direction.
- **Avoid Hazards** — Red spikes and gray walls will crash your flight.
- **Glide Strategically** — Gear with high glide values let you coast farther with less fuel.
- **Progressive Upgrades** — Start with early missions to build a coin reserve, then unlock powerful gear.

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the game:
   ```bash
   python main.py
   ```

## Project Structure

```
LearnToFly4/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── src/
│   ├── constants.py        # Game constants and gear definitions
│   ├── player.py           # Player class (flight physics)
│   ├── environment.py      # Terrain, hazards, and world
│   ├── mission.py          # Mission system
│   ├── save_system.py      # Game state persistence
│   ├── ui.py               # UI rendering and buttons
│   └── game.py             # Main game loop and state management
└── data/
    └── save.json           # Player save file (auto-generated)
```

## Game States

- **MENU** — Main menu with options
- **MISSION_SELECT** — Choose a mission to attempt
- **PLAYING** — Active flight
- **UPGRADE** — Gear shop to purchase/equip equipment
- **RESULTS** — Flight results and coin earnings

## Future Enhancements (Phase 2)

- Additional environments (volcanos, urban rooftops, futuristic cities)
- More flight gear with unique abilities
- Stunt/trick system with combo multipliers
- Global leaderboards (optional online features)
- Sound effects and ambient music
- Particle effects and improved animations
- Character customization

## Technical Details

- Built with **Python 3** and **Pygame 2.6.1**
- 2D physics simulation with gravity, velocity, and drag
- JSON-based save system for cross-session persistence
- State machine architecture for game flow
- Procedural terrain generation

## License

This project is a fan-inspired recreation. "Learn to Fly" is a trademark of their original creators. This project is for educational and entertainment purposes.

---

**Enjoy the skies, pilot!** ✈️

