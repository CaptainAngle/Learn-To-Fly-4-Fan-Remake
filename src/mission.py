class Mission:
    def __init__(self, mission_id, name, description, mission_type, target_value, reward_coins):
        self.id = mission_id
        self.name = name
        self.description = description
        self.type = mission_type  # "distance", "target", "survival"
        self.target_value = target_value
        self.reward_coins = reward_coins
        self.completed = False
        self.best_result = 0
    
    def check_completion(self, result_value):
        """Check if mission is completed."""
        if result_value >= self.target_value:
            self.completed = True
            self.best_result = max(self.best_result, result_value)
            return True
        self.best_result = max(self.best_result, result_value)
        return False
    
    def get_reward(self):
        """Return coin reward if completed."""
        return self.reward_coins if self.completed else 0


class MissionManager:
    def __init__(self):
        self.missions = []
        self.create_default_missions()
        self.current_mission = None
    
    def create_default_missions(self):
        """Create default missions."""
        missions = [
            Mission(1, "First Flight", "Fly 25 m", "distance", 25, 100),
            Mission(2, "Getting Distance", "Fly 50 m", "distance", 50, 250),
            Mission(3, "Long Haul", "Fly 125 m", "distance", 125, 500),
            Mission(4, "Marathon Flight", "Fly 250 m", "distance", 250, 1000),
            Mission(5, "Elite Flyer", "Fly 500 m", "distance", 500, 2000),
        ]
        self.missions = missions
    
    def select_mission(self, mission_id):
        """Select a mission to attempt."""
        for mission in self.missions:
            if mission.id == mission_id:
                self.current_mission = mission
                return mission
        return None
    
    def get_all_missions(self):
        """Return all missions."""
        return self.missions
    
    def get_completed_count(self):
        """Return number of completed missions."""
        return sum(1 for m in self.missions if m.completed)
    
    def get_total_coins_earned(self):
        """Return total coins earned from completed missions."""
        return sum(m.reward_coins for m in self.missions if m.completed)

