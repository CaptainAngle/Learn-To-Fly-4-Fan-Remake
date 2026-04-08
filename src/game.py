import pygame
from src.constants import *
from src.player import Player
from src.environment import Environment
from src.mission import MissionManager
from src.save_system import SaveSystem
from src.ui import UIManager, Button


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Learn to Fly 4: Skyward Evolution")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.state = STATE_MENU
        self.previous_state = None
        
        # Systems
        self.save_system = SaveSystem()
        self.ui_manager = UIManager()
        self.mission_manager = MissionManager()
        
        # Game objects
        self.player = None
        self.environment = None
        self.game_data = None
        
        # Camera system for scrolling
        self.camera_x = 0  # Camera position for horizontal scrolling
        
        # Load or create save
        self.load_or_create_save()
        
        # UI buttons
        self.buttons = {}
        self.create_menu_buttons()
        
        # Flight state tracking
        self.flight_distance = 0
        self.flight_coins_earned = 0
        self.mission_completed_this_flight = False
    
    def load_or_create_save(self):
        """Load existing save or create new one."""
        save_data = self.save_system.load_game()
        if save_data is None:
            save_data = self.save_system.create_new_save()
        self.game_data = save_data
        
        # Create a dummy player for menus
        self.player = Player(100, 200)
        self.player.coins = self.game_data.get("total_coins", 0)
        if "equipped_gear" in self.game_data:
            self.player.equip_gear(self.game_data["equipped_gear"])
    
    def save_game(self):
        """Save current game state."""
        self.save_system.save_game(self.game_data)
    
    def create_menu_buttons(self):
        """Create buttons for different menus."""
        # Main menu buttons
        self.buttons["menu"] = [
            Button(SCREEN_WIDTH // 2 - 75, 250, 150, 60, "Start Flight", (100, 150, 100)),
            Button(SCREEN_WIDTH // 2 - 75, 350, 150, 60, "Gear Shop", (100, 100, 150)),
            Button(SCREEN_WIDTH // 2 - 75, 450, 150, 60, "Settings", (150, 100, 100)),
            Button(SCREEN_WIDTH // 2 - 75, 550, 150, 60, "Quit", (150, 50, 50)),
        ]
        
        # Mission select buttons
        self.buttons["mission_select"] = [
            Button(50, SCREEN_HEIGHT - 80, 120, 60, "Back", (100, 100, 100)),
        ]
        
        # For each mission
        for i in range(len(self.mission_manager.missions)):
            btn = Button(SCREEN_WIDTH - 200, 130 + (i * 50), 150, 40, "Select", (100, 150, 100))
            if "mission_buttons" not in self.buttons:
                self.buttons["mission_buttons"] = []
            self.buttons["mission_buttons"].append(btn)
        
        # Upgrade screen buttons
        self.buttons["upgrade"] = [
            Button(50, SCREEN_HEIGHT - 80, 120, 60, "Back", (100, 100, 100)),
        ]
        
        # For each gear
        for i, (gear_name, stats) in enumerate(GEAR_TYPES.items()):
            if gear_name == "base":
                continue
            btn = Button(SCREEN_WIDTH - 150, 150 + (i * 35), 120, 30, "Equip/Buy", (100, 150, 100))
            if "gear_buttons" not in self.buttons:
                self.buttons["gear_buttons"] = []
            self.buttons["gear_buttons"].append((gear_name, btn))
        
        # Results screen buttons
        self.buttons["results"] = [
            Button(SCREEN_WIDTH // 2 - 75, 450, 150, 60, "Continue", (100, 150, 100)),
        ]
    
    def start_flight(self):
        """Initialize a new flight."""
        self.player = Player(100, 200)
        self.player.coins = self.game_data.get("total_coins", 0)
        self.environment = Environment()
        self.flight_distance = 0
        self.flight_coins_earned = 0
        self.mission_completed_this_flight = False
        
        # Equip the current gear
        if "equipped_gear" in self.game_data:
            self.player.equip_gear(self.game_data["equipped_gear"])
        
        self.state = STATE_PLAYING
    
    def handle_input(self):
        """Handle player input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                    self.save_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.handle_click(mouse_pos)
        
        # Continuous input for flight
        if self.state == STATE_PLAYING:
            keys = pygame.key.get_pressed()
            controls = {
                "up": keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w],
                "left": keys[pygame.K_LEFT] or keys[pygame.K_a],
                "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            }
            return controls
        return {}
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on buttons."""
        if self.state == STATE_MENU:
            for i, button in enumerate(self.buttons["menu"]):
                if button.is_clicked(mouse_pos, True):
                    if i == 0:  # Start Flight
                        self.state = STATE_MISSION_SELECT
                    elif i == 1:  # Gear Shop
                        self.state = STATE_UPGRADE
                    elif i == 2:  # Settings
                        pass  # TODO: Settings
                    elif i == 3:  # Quit
                        self.running = False
        
        elif self.state == STATE_MISSION_SELECT:
            if self.buttons["mission_select"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
            
            for i, button in enumerate(self.buttons.get("mission_buttons", [])):
                if button.is_clicked(mouse_pos, True):
                    mission = self.mission_manager.select_mission(i + 1)
                    if mission:
                        self.start_flight()
        
        elif self.state == STATE_UPGRADE:
            if self.buttons["upgrade"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
            
            for gear_name, button in self.buttons.get("gear_buttons", []):
                if button.is_clicked(mouse_pos, True):
                    self.try_purchase_gear(gear_name)
        
        elif self.state == STATE_RESULTS:
            if self.buttons["results"][0].is_clicked(mouse_pos, True):
                self.state = STATE_MENU
    
    def try_purchase_gear(self, gear_name):
        """Try to purchase or equip gear."""
        gear_info = GEAR_TYPES.get(gear_name)
        if not gear_info:
            return
        
        if gear_name in self.game_data["unlocked_gear"]:
            # Already owned, equip it
            self.player.equip_gear(gear_name)
            self.game_data["equipped_gear"] = gear_name
        else:
            # Not owned, try to purchase
            if self.player.coins >= gear_info["cost"]:
                self.player.coins -= gear_info["cost"]
                self.game_data["unlocked_gear"].append(gear_name)
                self.player.equip_gear(gear_name)
                self.game_data["equipped_gear"] = gear_name
    
    def update(self, controls):
        """Update game state."""
        if self.state == STATE_PLAYING:
            self.player.update(controls, self.environment.terrain.wind_speed)
            self.environment.update()
            
            # Apply ramp boost when player is on a slope
            terrain_y = self.environment.terrain.get_ground_y_at(self.player.x)
            self.environment.terrain.apply_ramp_boost(self.player, terrain_y)
            
            # Update camera to follow player (keep penguin mostly centered)
            self.camera_x = max(0, min(self.player.x - SCREEN_WIDTH // 3, 
                                       self.environment.terrain.width - SCREEN_WIDTH))
            
            # Check landing
            if self.player.check_landing(terrain_y):
                # Flight ended
                self.flight_distance = self.player.distance_traveled
                
                # Check if mission completed
                if self.mission_manager.current_mission:
                    if self.mission_manager.current_mission.check_completion(self.flight_distance):
                        self.flight_coins_earned = self.mission_manager.current_mission.reward_coins
                        self.mission_completed_this_flight = True
                
                # Award coins
                base_coins = int(self.flight_distance / 100)
                self.flight_coins_earned += base_coins
                self.player.coins += self.flight_coins_earned
                self.game_data["total_coins"] += self.flight_coins_earned
                self.game_data["total_distance"] += self.flight_distance
                
                # Save and show results
                self.save_game()
                self.state = STATE_RESULTS
            
            # Check hazard collision
            if self.environment.check_hazard_collision(self.player):
                # Crash - end flight
                self.flight_distance = self.player.distance_traveled
                self.flight_coins_earned = max(0, int(self.flight_distance / 200))  # Reduced coins on crash
                self.player.coins += self.flight_coins_earned
                self.game_data["total_coins"] += self.flight_coins_earned
                self.save_game()
                self.state = STATE_RESULTS
            
            # Check screen bounds
            if self.player.x < 0:
                self.player.x = 0
            elif self.player.x > SCREEN_WIDTH:
                # Went off screen - success!
                self.flight_distance = self.player.distance_traveled
                if self.mission_manager.current_mission:
                    if self.mission_manager.current_mission.check_completion(self.flight_distance):
                        self.flight_coins_earned = self.mission_manager.current_mission.reward_coins
                        self.mission_completed_this_flight = True
                
                base_coins = int(self.flight_distance / 100)
                self.flight_coins_earned += base_coins
                self.player.coins += self.flight_coins_earned
                self.game_data["total_coins"] += self.flight_coins_earned
                self.game_data["total_distance"] += self.flight_distance
                self.save_game()
                self.state = STATE_RESULTS
    
    def draw(self):
        """Render game."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button states
        if self.state == STATE_MENU:
            for button in self.buttons["menu"]:
                button.update(mouse_pos)
            self.ui_manager.draw_menu(self.screen, self.buttons["menu"])
        
        elif self.state == STATE_MISSION_SELECT:
            for button in self.buttons["mission_select"]:
                button.update(mouse_pos)
            for button in self.buttons.get("mission_buttons", []):
                button.update(mouse_pos)
            self.ui_manager.draw_mission_select(self.screen, self.mission_manager.missions, 
                                               self.buttons["mission_select"] + self.buttons.get("mission_buttons", []))
        
        elif self.state == STATE_UPGRADE:
            for button in self.buttons["upgrade"]:
                button.update(mouse_pos)
            for _, button in self.buttons.get("gear_buttons", []):
                button.update(mouse_pos)
            self.ui_manager.draw_upgrade_screen(self.screen, self.player, self.game_data, 
                                               self.buttons["upgrade"] + [b for _, b in self.buttons.get("gear_buttons", [])])
        
        elif self.state == STATE_PLAYING:
            # Draw game with camera offset
            # Draw background (not affected by camera)
            self.screen.fill((135, 206, 235))
            
            # Draw clouds
            for i in range(5):
                cloud_y = 50 + (i * 100)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(100 + i * 200 - self.camera_x * 0.3), cloud_y), 30)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(130 + i * 200 - self.camera_x * 0.3), cloud_y), 35)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(70 + i * 200 - self.camera_x * 0.3), cloud_y), 25)
            
            # Draw game elements with camera offset applied
            self.draw_terrain_with_camera(self.screen)
            self.draw_player_with_camera(self.screen)
            
            self.ui_manager.draw_stats(self.screen, self.player, self.environment)
            
            # Draw mission progress bar
            if self.mission_manager.current_mission:
                self.ui_manager.draw_mission_progress(self.screen, self.player, self.mission_manager.current_mission)
        
        elif self.state == STATE_RESULTS:
            for button in self.buttons["results"]:
                button.update(mouse_pos)
            self.ui_manager.draw_results_screen(self.screen, self.flight_distance, 
                                               self.flight_coins_earned, self.mission_completed_this_flight,
                                               self.buttons["results"])
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        while self.running:
            controls = self.handle_input()
            self.update(controls)
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()

