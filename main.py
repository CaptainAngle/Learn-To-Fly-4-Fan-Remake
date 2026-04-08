#!/usr/bin/env python3
"""
Learn to Fly 4: Skyward Evolution
A physics-based flight simulator inspired by classic Flash games.
"""

from src.game import Game


def main():
    """Entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

