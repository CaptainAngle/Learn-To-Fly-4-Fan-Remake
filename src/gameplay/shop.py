from src.constants import (
    BOOSTER_TIERS,
    FUEL_CAPACITY_TIERS,
    GLIDER_TIERS,
    PAYLOAD_TIERS,
    RAMP_DROP_TIERS,
    RAMP_HEIGHT_TIERS,
    SLED_TIERS,
)


def get_catalog_entries(category):
    """Return ordered gear tuples for the selected shop catalog."""
    if category == "sled":
        return list(SLED_TIERS.items())
    if category == "glider":
        return list(GLIDER_TIERS.items())
    if category == "booster":
        return list(BOOSTER_TIERS.items())
    if category == "payload":
        return list(PAYLOAD_TIERS.items())
    return []


def try_purchase_gear(game, category, gear_name):
    """Try to purchase/equip categorized gear using game state and side-effects."""
    if category == "sled":
        gear_info = SLED_TIERS.get(gear_name)
        unlock_key = "unlocked_sleds"
        equip_key = "equipped_sled"
        equip_fn = game.player.equip_sled
    elif category == "glider":
        gear_info = GLIDER_TIERS.get(gear_name)
        unlock_key = "unlocked_gliders"
        equip_key = "equipped_glider"
        equip_fn = game.player.equip_glider
    elif category == "booster":
        gear_info = BOOSTER_TIERS.get(gear_name)
        unlock_key = "unlocked_boosters"
        equip_key = "equipped_booster"
        equip_fn = game.player.equip_booster
    elif category == "payload":
        gear_info = PAYLOAD_TIERS.get(gear_name)
        unlock_key = "unlocked_payloads"
        equip_key = "equipped_payload"
        equip_fn = game.player.equip_payload
    else:
        return

    if not gear_info:
        return

    if gear_name in game.game_data[unlock_key]:
        equip_fn(gear_name)
        if category == "booster":
            game._apply_fuel_capacity_upgrade()
        game.game_data[equip_key] = gear_name
        game.save_game()
        game.set_toast(f"Equipped {gear_info['name']}", (120, 210, 150), duration=1.8)
        return

    if game.player.coins >= gear_info["cost"]:
        game.player.coins -= gear_info["cost"]
        game.game_data[unlock_key].append(gear_name)
        equip_fn(gear_name)
        if category == "booster":
            game._apply_fuel_capacity_upgrade()
        game.game_data[equip_key] = gear_name
        game.save_game()
        game.set_toast(f"Purchased {gear_info['name']}", (120, 210, 150), duration=2.1)
    else:
        need = gear_info["cost"] - game.player.coins
        game.set_toast(f"Need {need}$ more", (235, 130, 120), duration=2.0)


def try_purchase_ramp_height(game):
    _try_purchase_level_upgrade(
        game,
        level_key="ramp_height_level",
        tiers=RAMP_HEIGHT_TIERS,
        toast_label="Ramp Height",
    )


def try_purchase_ramp_drop(game):
    _try_purchase_level_upgrade(
        game,
        level_key="ramp_drop_level",
        tiers=RAMP_DROP_TIERS,
        toast_label="Ramp Length",
    )


def try_purchase_fuel_capacity(game):
    _try_purchase_level_upgrade(
        game,
        level_key="fuel_level",
        tiers=FUEL_CAPACITY_TIERS,
        toast_label="Fuel",
        on_purchase=lambda g: g._apply_fuel_capacity_upgrade(),
    )


def _try_purchase_level_upgrade(game, level_key, tiers, toast_label, on_purchase=None):
    current_level = int(game.game_data.get(level_key, 0))
    next_level = current_level + 1
    if next_level >= len(tiers):
        return

    next_tier = tiers[next_level]
    if game.player.coins >= next_tier["cost"]:
        game.player.coins -= next_tier["cost"]
        game.game_data[level_key] = next_level
        if on_purchase is not None:
            on_purchase(game)
        game.save_game()
        game.set_toast(f"{toast_label} upgraded to Lv {next_level + 1}", (120, 210, 150), duration=2.0)
    else:
        need = next_tier["cost"] - game.player.coins
        game.set_toast(f"Need {need}$ more", (235, 130, 120), duration=2.0)

