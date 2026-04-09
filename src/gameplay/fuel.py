from src.constants import BOOSTER_TIERS, FUEL_CAPACITY_TIERS


def apply_fuel_capacity_upgrade(player, game_data, refill=True):
    """Scale booster fuel by fuel upgrade level and optionally refill."""
    if player is None or player.booster not in BOOSTER_TIERS:
        return

    fuel_level = max(0, min(int(game_data.get("fuel_level", 0)), len(FUEL_CAPACITY_TIERS) - 1))
    fuel_mult = float(FUEL_CAPACITY_TIERS[fuel_level]["fuel_mult"])
    base_fuel = float(BOOSTER_TIERS[player.booster]["fuel"])
    player.max_fuel = base_fuel * fuel_mult

    if refill:
        player.fuel = player.max_fuel
    else:
        player.fuel = min(player.fuel, player.max_fuel)

