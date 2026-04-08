#!/usr/bin/env python3
"""
Launch script for Learn to Fly 4
Ensures dependencies are installed and starts the game
"""

import sys
import subprocess
import importlib.util

def check_pygame():
    """Check if pygame is installed, install if not."""
    spec = importlib.util.find_spec("pygame")
    if spec is None:
        print("Pygame not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame==2.6.1"])
    else:
        print("✓ Pygame is installed")

def main():
    """Main launcher function."""
    print("=" * 50)
    print("Learn to Fly 4: Skyward Evolution")
    print("=" * 50)
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    check_pygame()
    print()
    
    # Launch game
    print("Launching game...")
    print("-" * 50)
    
    try:
        from src.game import Game
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error launching game: {e}")
        print("\nTroubleshooting:")
        print("1. Check Python version (3.8+)")
        print("2. Try: pip install pygame --only-binary :all:")
        print("3. Run from the LearnToFly4 directory")
        sys.exit(1)

if __name__ == "__main__":
    main()

