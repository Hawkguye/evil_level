"""
Level devel-ish platformer demo
Victor Qin
"""

import arcade
from arcade.experimental import Shadertoy
import random
import math
import time
from pyglet.math import Vec2

# constants
SPRITE_SCALING_PLAYER = 0.25
TILE_SCALING = 0.25
MOVE_SPEED = 3
JUMP_SPEED = 10
GRAVITY = 0.8

SCREEN_WIDTH = 1050
SCREEN_HEIGHT = 800

CAMERA_SPEED = 0.5

# new wall movement constants
WALL_1_MOVE_SPEED = 10      # pixels per update
WALL_1_MOVE_DISTANCE = 400     # total pixels to move
WALL_2_MOVE_SPEED = 8
WALL_2_MOVE_DISTANCE = 96

START_POS = (160, 300)

SPRITE_PATH = "data/sprites/sprite.png"

class MovingWall():
    """ moving wall class """

    def __init__(self, wall_sprites, move_speed, move_distance, move_direction='vertical'):
        """ initializer """
        self.wall_list = wall_sprites
        self.original_positions = [(wall.center_x, wall.center_y) for wall in wall_sprites]
        self.move_speed = move_speed
        self.move_distance = move_distance
        self.move_direction = move_direction  # 'vertical' or 'horizontal'
        self.moved_distance = 0
        self.is_moving = False

    def update(self):
        """Move wall sprites at a constant speed until moved target distance."""
        if not self.is_moving or not self.wall_list:
            return

        # remaining distance to move
        remaining = self.move_distance - self.moved_distance
        if remaining <= 0:
            self.is_moving = False
            return

        # move by the smaller of the speed or remaining distance to avoid overshoot
        delta = min(self.move_speed, remaining)

        for sprite in self.wall_list:
            if self.move_direction == 'vertical':
                sprite.center_y -= delta
            else:
                sprite.center_x -= delta

        self.moved_distance += delta

        # stop when we've moved the target distance
        if self.moved_distance >= self.move_distance:
            self.is_moving = False

    def start_moving(self):
        """Start wall movement."""
        self.is_moving = True

    def reset(self):
        """Reset wall positions to original locations."""
        self.moved_distance = 0
        self.is_moving = False
        for i, wall in enumerate(self.wall_list):
            wall.center_x, wall.center_y = self.original_positions[i]


class Door():
    """ door class """
    def __init__(self, x, y):
        """ initializer """
        self.pos_x = x
        self.pos_y = y
        self.height = 45
        self.width = 30

        self.move_speed = 1
        self.move_distance = 60
        self.moved = 0
        self.is_moving = False
        self.move_over = True
    
    def draw(self):
        """ draws the door """
        arcade.draw_rectangle_filled(self.pos_x, self.pos_y, self.width + 10, self.height + 10, (64, 22, 0))
        arcade.draw_rectangle_filled(self.pos_x, self.pos_y, self.width, self.height, arcade.color.WHITE)
    
    def check_collision(self, left, right, bottom):
        """ check the collision of the door w/ an object """
        if abs(right - (self.pos_x - self.width / 2)) < 3 and bottom < self.pos_y + self.height / 2:
            return True
        if abs(left - (self.pos_x + self.width / 2)) < 3 and bottom < self.pos_y + self.height / 2:
            return True
        if right > self.pos_x - self.width / 2 and left < self.pos_x + self.width / 2 and bottom < self.pos_y + self.height / 2:
            return True
        return False
    
    def move_down(self):
        """ moves the door down when the game is over """
        if not self.is_moving:
            return
        
        remaining = self.move_distance - self.moved
        if remaining <= 0:
            self.is_moving = False
            self.move_over = True
            return

        delta = min(self.move_speed, remaining)
        self.pos_y -= delta
        self.moved += delta

        if self.moved >= self.move_distance:
            self.is_moving = False
            self.move_over = True


class MyGame(arcade.Window):
    """ windows class """

    def __init__(self):
        """ initializer """
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Evil Level", resizable=True)

        # set location of the window
        self.set_location(100, 100)

        self.game_on = True

        # sprite lists
        self.player_list = None
        self.wall_list = None
        self.star_list = None
        self.spike_list = None

        # specific to the levels
        self.wall_1 = None
        self.wall_2 = None
        self.wall_3 = None
        self.trigger_1_list = None
        self.trigger_2_list = None
        self.trigger_3_list = None
        self.door = None

        # player info
        self.death = 0
        self.lvl = 0
        self.player_sprite = None
        self.score = 0

        # simple physics engine
        self.jump_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.physics_engine = None
        self.tile_map = None
        # reset/freeze state for particle burst
        self.is_resetting = False
        self.reset_start_time = 0.0
        # Keep this in sync with the shader BURST_TIME (seconds)
        self.PARTICLE_BURST_TIME = 0.5

        # self.set_mouse_visible(False)
        arcade.set_background_color((255, 195, 99))

        # CAMERAS
        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # shader
        self.particle_run = False
        self.time = 0.0
        self.time_particle_start = 0.0
        # Load a file and create a shader from it
        file_name = "particles.glsl"
        self.shadertoy = Shadertoy(size=self.get_size(),
                                   main_source=open(file_name).read())


    def setup(self):
        """ set up the game and initialize the variables """
        # sprite lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.star_list = arcade.SpriteList()
        self.player_sprite = arcade.AnimatedTimeBasedSprite()

        # set up player animation sprites
        texture = arcade.load_texture(SPRITE_PATH, 0, 0, 128, 128)
        anim = arcade.AnimationKeyframe(1, 10, texture)
        self.player_sprite.frames.append(anim)
        self.player_sprite.scale = SPRITE_SCALING_PLAYER
        self.player_sprite.set_hit_box([(-32, -48), (32, -48), (32, 48), (-32, 48)])

        # set up the player sprite
        self.player_sprite.center_x = START_POS[0]
        self.player_sprite.center_y = START_POS[1]
        self.player_list.append(self.player_sprite)

        # set up the map from Tiled
        map_name = "data/maps/map.json"
        self.tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING)

        # sprite_list is from Tiled map layers
        self.door = Door(920, 210)
        self.wall_list = self.tile_map.sprite_lists["Walls"]
        self.star_list = self.tile_map.sprite_lists["Stars"]
        self.spike_list = self.tile_map.sprite_lists["Spike"]

        # Create moving walls
        self.wall_1 = MovingWall(self.tile_map.sprite_lists["Walls_1"], WALL_1_MOVE_SPEED, WALL_1_MOVE_DISTANCE, 'vertical')
        self.wall_2 = MovingWall(self.tile_map.sprite_lists["Walls_2"], WALL_2_MOVE_SPEED, WALL_2_MOVE_DISTANCE, 'horizontal')
        self.wall_3 = MovingWall(self.tile_map.sprite_lists["Walls_3"], WALL_1_MOVE_SPEED, WALL_1_MOVE_DISTANCE, 'vertical')

        # Set up triggers
        self.trigger_1_list = self.tile_map.sprite_lists["Trigger_1"]
        self.trigger_2_list = self.tile_map.sprite_lists["Trigger_2"]
        self.trigger_3_list = self.tile_map.sprite_lists["Trigger_3"]

        # Set the background color to what is specified in the map
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # setup physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, 
            [self.wall_list, self.wall_1.wall_list, self.wall_2.wall_list, self.wall_3.wall_list], 
            GRAVITY)


    def on_draw(self):
        arcade.start_render()

        # select the camera to use before drawing sprites
        self.camera_sprites.use()

        # draw the sprite lists
        self.door.draw()
        self.player_list.draw()
        self.wall_list.draw()
        self.wall_1.wall_list.draw()
        self.wall_2.wall_list.draw()
        self.wall_3.wall_list.draw()
        self.star_list.draw()
        self.spike_list.draw()

        # Run the GLSL code
        if self.particle_run:
            self.shadertoy.render(time=self.time)
            # stop particle rendering after the configured burst time
            if self.time > self.time_particle_start + self.PARTICLE_BURST_TIME:
                self.particle_run = False

        # draw the gui
        self.camera_gui.use()
        arcade.draw_text(f"Score: {self.score}", 50, 550, font_size=16)
        arcade.draw_text(f"Deaths: {self.death}", 50, 600, font_size=16)
        arcade.draw_text(f"x: {round(self.player_sprite.center_x)}; y: {round(self.player_sprite.center_y)}", 50, 50, font_size=16)
        
    
    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """
        if not self.game_on:
            return
        if key == arcade.key.UP or key == arcade.key.SPACE:
            self.jump_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True


    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP or key == arcade.key.SPACE:
            self.jump_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False


    def on_mouse_press(self, x, y, button, modifiers):
        """ called whenver mouse is clicked """
        if button == arcade.MOUSE_BUTTON_LEFT:
            print("left mouse button pressed at ", x, y)
        if button == arcade.MOUSE_BUTTON_RIGHT:
            print("right mouse button pressed at ", x, y)


    def update(self, delta_time):
        """ Movement and game logic """
        self.time += delta_time

        # If we're currently running the reset particle burst, wait until it finishes
        if self.is_resetting:
            # If the burst duration is over, finalize the reset
            if self.time - self.reset_start_time >= self.PARTICLE_BURST_TIME:
                self.finish_reset()
            # While the burst is active, do not advance game logic
            return
        
        if self.door.is_moving:
            self.door.move_down()

        if not self.game_on:
            self.player_sprite.center_x = self.door.pos_x
            self.player_sprite.center_y = self.door.pos_y
            self.left_pressed = False
            self.right_pressed = False
            self.jump_pressed = False
            if self.door.move_over:
                self.level_complete()

        # Call update on all sprites
        self.player_list.update()
        self.star_list.update()
        self.player_list.update_animation()
        self.wall_1.update()
        self.wall_2.update()
        self.wall_3.update()
        if self.game_on:
            self.physics_engine.update()
        
        # Calculate speed based on the keys pressed
        self.player_sprite.change_x = 0
        # self.player_sprite.change_y = 0
        if self.jump_pressed and self.physics_engine.can_jump(1):
            self.player_sprite.change_y = JUMP_SPEED
        if self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -MOVE_SPEED
            self.set_anim(256)
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = MOVE_SPEED
            self.set_anim(384)
        else:
            self.clear_anim(0, 0)

        spike_hit = arcade.check_for_collision_with_list(self.player_sprite, self.spike_list)
        if spike_hit:
            self.reset()

        # out of limit, death
        if self.player_sprite.center_y < -20:
            self.reset()

        if not self.game_on:
            return

        # a list of all star sprites that collided with the player sprite
        star_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.star_list)

        # kill all the stars that are hit
        for star in star_hit_list:
            star.kill()
            self.score += 1
        
        # trigger traps
        trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trigger_1_list)
        if trigger_hit:
            # print("trigger hit")
            self.wall_1.start_moving()
            if self.lvl < 1:
                self.lvl = 1

        if (self.lvl >= 1 and self.death > 0) or True:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trigger_2_list)
            if trigger_hit:
                self.wall_2.start_moving()
                if self.lvl < 2:
                    self.lvl = 2
        
        if self.death > 0:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trigger_3_list)
            if trigger_hit:
                self.wall_3.start_moving()

        # check if touched the door
        collided_w_door = self.door.check_collision(self.player_sprite.left, self.player_sprite.right, self.player_sprite.bottom)
        if collided_w_door:
            print(collided_w_door)
            self.game_on = False
            self.game_over()
        # Scroll the screen to the player
        # self.scroll_to_player()

    def reset(self):
        """
        resets the scene after death
        """
        # Start the particle burst and freeze the game; the actual reset will occur
        # in finish_reset() after the burst duration elapses.
        # Set uniform data to send to the GLSL shader
        self.shadertoy.program['pos'] = (self.player_sprite.center_x, self.player_sprite.center_y)
        # Tell the shader when this burst started so it can start from time 0
        try:
            self.shadertoy.program['burstStart'] = self.time
        except Exception:
            # If the shader/program doesn't accept the uniform for some reason,
            # ignore and continue — the shader will fallback to using global time.
            pass
        self.shake_camera()
        self.particle_run = True
        # record when the particle burst started
        self.time_particle_start = self.time
        self.reset_start_time = self.time
        self.is_resetting = True
        # disable inputs and stop motion while resetting
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.player_list.visible = False

    def finish_reset(self):
        """Complete the reset after the particle burst has finished."""
        # stop rendering particles
        self.particle_run = False
        self.is_resetting = False
        # apply the actual reset actions
        self.death += 1
        self.wall_1.reset()
        self.wall_2.reset()
        self.wall_3.reset()
        self.player_sprite.center_x = START_POS[0]
        self.player_sprite.center_y = START_POS[1]
        self.player_list.visible = True

    
    def game_over(self):
        """ game over animation, door and player moves down """
        self.player_sprite.center_x = self.door.pos_x
        self.player_sprite.center_y = self.door.pos_y
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.door.is_moving = True
        self.shake_camera()

    
    def shake_camera(self):
        """ Shake the camera """
        # Pick a random direction
        shake_direction = random.random() * 2 * math.pi
        # How 'far' to shake
        shake_amplitude = 10
        # Calculate a vector based on that
        shake_vector = Vec2(
            math.cos(shake_direction) * shake_amplitude,
            math.sin(shake_direction) * shake_amplitude
        )
        # Frequency of the shake
        shake_speed = 3.0
        # How fast to damp the shake
        shake_damping = 0.9
        # Do the shake
        self.camera_sprites.shake(shake_vector,
                                    speed=shake_speed,
                                    damping=shake_damping)


    def scroll_to_player(self):
        """ 
        scroll the window to the player

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan
        """

        position = Vec2(self.player_sprite.center_x - self.width / 2,
                        self.player_sprite.center_y - self.height / 2)
        self.camera_sprites.move_to(position, CAMERA_SPEED)


    def on_resize(self, width, height):
        """
        Resize window
        Handle the user grabbing the edge and resizing the window.
        """
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))


    def set_anim(self, y):
        """ set up walking animation, input y in the sprite sheet """
        self.player_sprite.frames.clear()
        for i in range(4):
            texture = arcade.load_texture(SPRITE_PATH, i * 128, y, 128, 128)
            # frame i, speed 50ms per frame
            anim = arcade.AnimationKeyframe(i, 50, texture)
            self.player_sprite.frames.append(anim)


    def clear_anim(self, x, y):
        """ clear animation to a static texture, input x,y in the sprite sheet """
        self.player_sprite.frames.clear()
        for i in range(4):
            texture = arcade.load_texture(SPRITE_PATH, x, y, 128, 128)
            # frame i, speed 10ms per frame
            anim = arcade.AnimationKeyframe(i, 10, texture)
            self.player_sprite.frames.append(anim)
    
    def level_complete(self):
        self.door.move_over = False
        self.shake_camera()
        print("level complete")


def main():
    """ main method """
    window = MyGame()
    window.setup()
    arcade.run()

main()