import json
import os


class SaveSystem:
    def __init__(self, save_dir="data"):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.save_file = os.path.join(save_dir, "save.json")
    
    def save_game(self, game_data):
        """Save game data to JSON file."""
        with open(self.save_file, 'w') as f:
            json.dump(game_data, f, indent=2)
    
    def load_game(self):
        """Load game data from JSON file."""
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_default_save(self):
        """Return default save data."""
        return {
            "total_coins": 0,
            "total_distance": 0,
            "ramp_height_level": 0,
            "ramp_drop_level": 0,
            "fuel_level": 0,
            "unlocked_sleds": [],
            "unlocked_gliders": [],
            "unlocked_boosters": [],
            "unlocked_payloads": [],
            "equipped_sled": None,
            "equipped_glider": None,
            "equipped_booster": None,
            "equipped_payload": None,
            "best_flight_distance": 0,
        }
    
    def create_new_save(self):
        """Create a new save file."""
        default_save = self.get_default_save()
        self.save_game(default_save)
        return default_save
