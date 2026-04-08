# Quick Start Guide - Learn to Fly 4

## Running the Game

1. **From command line:**
   ```bash
   python main.py
   ```

2. **From PyCharm IDE:**
   - Right-click `main.py` → "Run 'main.py'"
   - Or press `Shift + F10`

## First Time Setup

The game will automatically:
- Create a `data/` folder for saves
- Initialize `save.json` with starting data
- Set you up with the base flight gear

## Game Loop (First Playthrough)

1. **Main Menu** → Click "Start Flight"
2. **Mission Select** → Choose "First Flight" mission (500 units)
3. **Flight** → 
   - Hold SPACE to fly upward
   - Use LEFT/RIGHT arrows to steer
   - Try to reach 500 units of distance
   - Avoid red spikes!
4. **Results** → See coins earned
5. **Upgrade Shop** → Click "Back" for now or explore later

## Tips for New Players

- **Fuel Management**: Each gear type has different fuel capacity
  - Don't waste fuel flying straight up; use gliding to conserve energy
  - The jetpack burns fuel faster but goes higher/faster
  
- **Understanding Wind**:
  - Wind icon shows direction (→ right, ← left)
  - Wind helps you fly further in that direction
  - Wind opposes your flight if you go against it

- **Gear Progression**:
  - Start with "First Flight" (500 units) → 100 coins
  - Do missions in order to build up coins
  - Jetpack MK1 (500 coins) is the first purchase

- **Mission Tips**:
  - "First Flight" - Easy, just reach 500
  - "Getting Distance" - 1000 units, need better control
  - "Long Haul" - 2500 units, try upgrading gear first
  - "Marathon Flight" - 5000 units, need good gear and strategy
  - "Elite Flyer" - 10000 units, late-game challenge

## Controls Reference

| Key | Action |
|-----|--------|
| SPACE / UP / W | Thrust upward (uses fuel) |
| LEFT / A | Bank left (rotate) |
| RIGHT / D | Bank right (rotate) |
| ESC | Return to menu (during flight) |
| Mouse | Click buttons on menus |

## Troubleshooting

**Game won't start:**
- Ensure you're in the LearnToFly4 directory
- Try: `python -m src.game`
- Check Python version is 3.8+

**Game is slow:**
- Close other applications
- The game runs at 60 FPS - if your system is slow, try closing browser/Discord

**Save file issues:**
- Delete `data/save.json` to reset progress
- Game will auto-create a new save

## Advanced Play

- Each gear has trade-offs. Experiment to find your favorite!
- Higher glide value = you can coast farther without fuel
- Higher speed = you reach distance targets faster
- Lower fuel capacity = you need to manage flight carefully

## Next Steps (Phase 2)

Future updates will include:
- New environments (volcano, city, space)
- Trick/stunt system with multipliers
- More gear options
- Global leaderboards
- Sound effects and music

---

**Happy flying! Remember: It's all about that balance between thrust, glide, and fuel.** ✈️

