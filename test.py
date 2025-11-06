"""
Level Devil Style Game Framework with Tiled Integration + JSON Config
Supports: Walls, Spikes, Moving Walls, and Trigger Lines
Uses JSON files for easy level-specific mechanics configuration
"""

import arcade
import json
import os

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Level Devil Framework"
PLAYER_MOVEMENT_SPEED = 5
PLAYER_JUMP_SPEED = 15
GRAVITY = 0.8
TILE_SCALING = 1.0


class MovingWall:
    """Handles moving wall behavior triggered by player"""
    def __init__(self, sprite, start_x, start_y, end_x, end_y, speed, trigger_id, reverse=False):
        self.sprite = sprite
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.speed = speed
        self.trigger_id = trigger_id
        self.reverse = reverse  # Move back to start after reaching end
        self.active = False
        self.progress = 0.0  # 0 to 1
        self.going_forward = True
        
    def activate(self):
        """Start moving the wall"""
        self.active = True
    
    def update(self):
        """Update wall position"""
        if not self.active:
            return
        
        # Update progress
        if self.going_forward:
            self.progress += self.speed
            if self.progress >= 1.0:
                self.progress = 1.0
                if self.reverse:
                    self.going_forward = False
        else:
            self.progress -= self.speed
            if self.progress <= 0.0:
                self.progress = 0.0
                self.going_forward = True
        
        # Linear interpolation
        self.sprite.center_x = self.start_x + (self.end_x - self.start_x) * self.progress
        self.sprite.center_y = self.start_y + (self.end_y - self.start_y) * self.progress


class Trigger:
    """Trigger line that activates when player crosses it"""
    def __init__(self, x, y, width, height, trigger_id, one_time=True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.trigger_id = trigger_id
        self.one_time = one_time
        self.triggered = False
        
    def check_collision(self, player_sprite):
        """Check if player is touching this trigger"""
        if self.triggered and self.one_time:
            return False
            
        player_left = player_sprite.center_x - player_sprite.width / 2
        player_right = player_sprite.center_x + player_sprite.width / 2
        player_bottom = player_sprite.center_y - player_sprite.height / 2
        player_top = player_sprite.center_y + player_sprite.height / 2
        
        trigger_left = self.x
        trigger_right = self.x + self.width
        trigger_bottom = self.y
        trigger_top = self.y + self.height
        
        if (player_right > trigger_left and player_left < trigger_right and
            player_top > trigger_bottom and player_bottom < trigger_top):
            self.triggered = True
            return True
        return False


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        
        # Sprite lists
        self.wall_list = None
        self.spike_list = None
        self.moving_wall_list = None
        self.player_list = None
        self.goal_list = None
        
        # Player
        self.player_sprite = None
        
        # Physics engine
        self.physics_engine = None
        
        # Moving walls and triggers
        self.moving_walls = []
        self.triggers = []
        
        # Camera
        self.camera = None
        self.gui_camera = None
        
        # Level
        self.level = 1
        self.level_config = None
        
        arcade.set_background_color(arcade.color.SKY_BLUE)
        
    def setup(self):
        """Set up the game"""
        # Initialize sprite lists
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.spike_list = arcade.SpriteList(use_spatial_hash=True)
        self.moving_wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.player_list = arcade.SpriteList()
        self.goal_list = arcade.SpriteList()
        
        # Reset moving walls and triggers
        self.moving_walls = []
        self.triggers = []
        
        # Set up cameras
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Load the level
        self.load_level(self.level)
        
    def load_level_config(self, level_number):
        """Load level configuration from JSON file"""
        config_file = f"level_{level_number}_config.json"
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return None
    
    def load_level(self, level_number):
        """Load a level from Tiled TMX file and JSON config"""
        map_name = f"level_{level_number}.tmx"
        
        # Load config first
        self.level_config = self.load_level_config(level_number)
        
        try:
            # Load the Tiled map
            my_map = arcade.load_tilemap(map_name, TILE_SCALING)
            
            # Load sprite lists from map layers
            self.wall_list = my_map.sprite_lists.get("Walls", arcade.SpriteList())
            self.spike_list = my_map.sprite_lists.get("Spikes", arcade.SpriteList())
            self.moving_wall_list = my_map.sprite_lists.get("Moving_Wall", arcade.SpriteList())
            
            # If config exists, use it for player/goal/mechanics
            if self.level_config:
                self.load_from_config()
            else:
                # Fallback to Tiled objects
                self.load_from_tiled_objects(my_map)
            
            # Set up physics engine
            self.physics_engine = arcade.PhysicsEnginePlatformer(
                self.player_sprite,
                walls=self.wall_list,
                gravity_constant=GRAVITY
            )
            
        except FileNotFoundError:
            print(f"Level file {map_name} not found!")
            if self.level == 1:
                print("Creating placeholder level...")
                self.create_placeholder_level()
            else:
                print("No more levels! Restarting from level 1...")
                self.level = 1
                self.setup()
    
    def load_from_config(self):
        """Load level mechanics from JSON config"""
        config = self.level_config
        
        # Setup player
        player_spawn = config.get("player_spawn", [100, 200])
        self.setup_player(player_spawn[0], player_spawn[1])
        
        # Setup goal
        if "goal" in config:
            goal_pos = config["goal"]
            goal = arcade.Sprite(":resources:images/items/star.png", 0.5)
            goal.center_x = goal_pos[0]
            goal.center_y = goal_pos[1]
            self.goal_list.append(goal)
        
        # Setup moving walls
        if "moving_walls" in config:
            for mw_config in config["moving_walls"]:
                # Create sprite for moving wall
                sprite = arcade.Sprite(
                    mw_config.get("sprite", ":resources:images/tiles/boxCrate_double.png"),
                    mw_config.get("scale", 1.0)
                )
                start_pos = mw_config["start"]
                sprite.center_x = start_pos[0]
                sprite.center_y = start_pos[1]
                self.moving_wall_list.append(sprite)
                
                # Create moving wall controller
                end_pos = mw_config["end"]
                moving_wall = MovingWall(
                    sprite,
                    start_pos[0], start_pos[1],
                    end_pos[0], end_pos[1],
                    mw_config.get("speed", 0.01),
                    mw_config.get("trigger_id", 0),
                    mw_config.get("reverse", False)
                )
                self.moving_walls.append(moving_wall)
        
        # Setup triggers
        if "triggers" in config:
            for t_config in config["triggers"]:
                trigger = Trigger(
                    t_config["x"], t_config["y"],
                    t_config["width"], t_config["height"],
                    t_config["trigger_id"],
                    t_config.get("one_time", True)
                )
                self.triggers.append(trigger)
        
        # Setup additional spikes from config (optional)
        if "spikes" in config:
            for spike_pos in config["spikes"]:
                spike = arcade.Sprite(":resources:images/tiles/spikes.png", TILE_SCALING)
                spike.center_x = spike_pos[0]
                spike.center_y = spike_pos[1]
                self.spike_list.append(spike)
    
    def load_from_tiled_objects(self, my_map):
        """Fallback: Load from Tiled object layers"""
        # Load player spawn point from object layer
        if "Objects" in my_map.object_lists:
            for obj in my_map.object_lists["Objects"]:
                if obj.name == "Player":
                    self.setup_player(obj.shape[0], obj.shape[1])
                elif obj.name == "Goal":
                    goal = arcade.Sprite(":resources:images/items/star.png", 0.5)
                    goal.center_x = obj.shape[0]
                    goal.center_y = obj.shape[1]
                    self.goal_list.append(goal)
        
        # Load triggers from Tiled
        if "Triggers" in my_map.object_lists:
            for obj in my_map.object_lists["Triggers"]:
                if obj.name.startswith("Trigger"):
                    trigger_id = int(obj.name.split("_")[1])
                    trigger = Trigger(
                        obj.shape[0], obj.shape[1],
                        obj.shape[2], obj.shape[3],
                        trigger_id
                    )
                    self.triggers.append(trigger)
        
        # Set up moving walls from Tiled properties
        for sprite in self.moving_wall_list:
            if hasattr(sprite, 'properties'):
                props = sprite.properties
                if 'trigger_id' in props:
                    moving_wall = MovingWall(
                        sprite,
                        sprite.center_x, sprite.center_y,
                        props.get('end_x', sprite.center_x),
                        props.get('end_y', sprite.center_y),
                        props.get('speed', 0.01),
                        props.get('trigger_id', 0),
                        props.get('reverse', False)
                    )
                    self.moving_walls.append(moving_wall)
    
    def create_placeholder_level(self):
        """Create a simple placeholder level for testing without files"""
        # Create player
        self.setup_player(100, 200)
        
        # Create ground
        for x in range(0, 1500, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)
        
        # Create some platforms
        for x in range(300, 500, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
            wall.center_x = x
            wall.center_y = 200
            self.wall_list.append(wall)
        
        # Create spikes
        for x in range(600, 800, 64):
            spike = arcade.Sprite(":resources:images/tiles/spikes.png", TILE_SCALING)
            spike.center_x = x
            spike.center_y = 96
            self.spike_list.append(spike)
        
        # Create a moving wall
        moving_sprite = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", TILE_SCALING)
        moving_sprite.center_x = 900
        moving_sprite.center_y = 100
        self.moving_wall_list.append(moving_sprite)
        
        moving_wall = MovingWall(
            moving_sprite,
            900, 100,  # start position
            900, 400,  # end position
            0.01,      # speed
            1,         # trigger_id
            False      # reverse
        )
        self.moving_walls.append(moving_wall)
        
        # Create a trigger line
        trigger = Trigger(500, 0, 10, 400, 1)
        self.triggers.append(trigger)
        
        # Create goal
        goal = arcade.Sprite(":resources:images/items/star.png", 0.5)
        goal.center_x = 1200
        goal.center_y = 100
        self.goal_list.append(goal)
        
        # Set up physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            walls=self.wall_list,
            gravity_constant=GRAVITY
        )
        
        # Save example config
        self.save_example_config()
    
    def save_example_config(self):
        """Save an example config file for reference"""
        example_config = {
            "player_spawn": [100, 200],
            "goal": [1200, 100],
            "moving_walls": [
                {
                    "start": [900, 100],
                    "end": [900, 400],
                    "speed": 0.01,
                    "trigger_id": 1,
                    "reverse": False,
                    "sprite": ":resources:images/tiles/boxCrate_double.png",
                    "scale": 1.0
                }
            ],
            "triggers": [
                {
                    "x": 500,
                    "y": 0,
                    "width": 10,
                    "height": 400,
                    "trigger_id": 1,
                    "one_time": True
                }
            ],
            "spikes": [
                [650, 96],
                [714, 96],
                [778, 96]
            ]
        }
        
        try:
            with open("level_1_config.json", 'w') as f:
                json.dump(example_config, f, indent=2)
            print("✅ Created example config: level_1_config.json")
        except Exception as e:
            print(f"Could not save example config: {e}")
    
    def setup_player(self, x, y):
        """Create the player sprite"""
        self.player_sprite = arcade.Sprite(
            ":resources:images/animated_characters/female_person/femalePerson_idle.png",
            0.5
        )
        self.player_sprite.center_x = x
        self.player_sprite.center_y = y
        self.player_list.append(self.player_sprite)
    
    def on_draw(self):
        """Render the screen"""
        self.clear()
        
        # Activate game camera
        self.camera.use()
        
        # Draw sprites
        self.wall_list.draw()
        self.spike_list.draw()
        self.moving_wall_list.draw()
        self.player_list.draw()
        self.goal_list.draw()
        
        # Draw triggers (for debugging)
        for trigger in self.triggers:
            color = arcade.color.GREEN if not trigger.triggered else arcade.color.RED
            arcade.draw_rectangle_filled(
                trigger.x + trigger.width / 2,
                trigger.y + trigger.height / 2,
                trigger.width, trigger.height,
                (*color, 50)  # Semi-transparent
            )
        
        # Activate GUI camera
        self.gui_camera.use()
        
        # Draw GUI
        arcade.draw_text(
            f"Level {self.level}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.BLACK, 18
        )
        
        config_status = "✅ JSON Config" if self.level_config else "📋 Tiled Only"
        arcade.draw_text(
            config_status,
            10, SCREEN_HEIGHT - 55,
            arcade.color.DARK_GREEN if self.level_config else arcade.color.DARK_BLUE,
            14
        )
        
        arcade.draw_text(
            "Arrow Keys: Move | Space: Jump | R: Restart | N: Next Level",
            10, 10,
            arcade.color.BLACK, 14
        )
    
    def on_update(self, delta_time):
        """Movement and game logic"""
        # Update physics
        self.physics_engine.update()
        
        # Update moving walls
        for moving_wall in self.moving_walls:
            moving_wall.update()
        
        # Check triggers
        for trigger in self.triggers:
            if trigger.check_collision(self.player_sprite):
                # Activate all moving walls with this trigger_id
                for moving_wall in self.moving_walls:
                    if moving_wall.trigger_id == trigger.trigger_id:
                        moving_wall.activate()
        
        # Check collision with spikes
        spike_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.spike_list
        )
        if spike_hit:
            self.setup()  # Restart level
        
        # Check collision with moving walls (death)
        moving_wall_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.moving_wall_list
        )
        if moving_wall_hit:
            self.setup()  # Restart level
        
        # Check if reached goal
        goal_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.goal_list
        )
        if goal_hit:
            self.level += 1
            self.setup()
        
        # Center camera on player
        self.center_camera_on_player()
    
    def center_camera_on_player(self):
        """Center the camera on the player"""
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)
        
        # Don't let camera go below 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        
        player_centered = screen_center_x, screen_center_y
        self.camera.move_to(player_centered, 0.1)
    
    def on_key_press(self, key, modifiers):
        """Handle key presses"""
        if key == arcade.key.UP or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.R:
            self.setup()  # Restart level
        elif key == arcade.key.N:
            self.level += 1  # Next level
            self.setup()
    
    def on_key_release(self, key, modifiers):
        """Handle key releases"""
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0


def main():
    """Main function"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game = GameView()
    game.setup()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()