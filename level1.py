import arcade
from arcade.experimental import Shadertoy
import random
import math
import time
from pyglet.math import Vec2

from modals import MovingWall, Door, EndScreen


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# constants
SPRITE_SCALING_PLAYER = 0.25
TILE_SCALING = 0.25
MOVE_SPEED = 3
JUMP_SPEED = 8
GRAVITY = 0.6

VIEWPORT_MARGIN = 400
CAMERA_SPEED = 0.5
CAMERA_OFFSET_Y = 50

START_POS = (250, 300)

SPRITE_PATH = "data/sprites/sprite.png"


class Level1(arcade.View):
    """ windows class """

    def __init__(self, window):
        """ initializer """
        super().__init__(window)

        # self.set_mouse_visible(False)

        self.game_on = False
        self.paused = False

        # sprite lists
        self.player_list = None
        self.bkg_list = None
        self.background = None
        self.spike_list = None
        self.door = None
        self.vis_sprites_list = None
        self.moving_wall_list = None

        # specific to the levels
        self.ceiling_list = None
        self.trig1_list = None
        self.gap1_list = None
        self.trig2_list = None
        self.spike2_list = None
        self.trig3_list = None
        self.gap3_list = None
        self.trig4_list = None
        self.trig5_list = None
        self.gap5_list = None
        self.arrow_sprite = None
        
        # player info
        self.death = 0
        self.player_sprite = None
        self.level_start_time = 0.0

        # simple physics engine
        self.jump_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.physics_engine = None
        self.tile_map = None
        # coyote time
        self.frames_since_land = 0
        self.was_on_ground = False
        self.jump_sound_ready = True
        self.jump_sound = arcade.load_sound("data/sounds/jump.wav")
        
        # CAMERAS
        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_sprites.move_to(Vec2(0, CAMERA_OFFSET_Y))
        # Used in scrolling
        # self.view_bottom = 0
        self.view_left = 0

        # reset/freeze state for particle burst
        self.is_resetting = False
        self.reset_start_time = 0.0
        self.PARTICLE_BURST_TIME = 0.5
        # particle shader
        self.particle_run = False
        self.frame_cnt = 0
        self.time = 0.0
        self.time_particle_start = 0.0
        file_name = "particles.glsl"
        self.shadertoy = Shadertoy(size=(SCREEN_WIDTH, SCREEN_HEIGHT),
                                   main_source=open(file_name).read())
        
        # arcade.enable_timings()


    def on_show_view(self):
        """ set up the game and initialize the variables """
        print("level 1 starting...")
        arcade.set_background_color((122, 9, 2))
        # sprite lists
        self.player_list = arcade.SpriteList()
        self.bkg_list = arcade.SpriteList()
        self.player_sprite = arcade.AnimatedTimeBasedSprite()

        # set up player animation sprites
        texture = arcade.load_texture(SPRITE_PATH, 0, 0, 128, 128)
        anim = arcade.AnimationKeyframe(1, 10, texture)
        self.player_sprite.frames.append(anim)
        self.player_sprite.scale = SPRITE_SCALING_PLAYER
        self.player_sprite.set_hit_box([(-32, -48), (32, -48), (32, 48), (-32, 48)])

        # set up the player sprite
        self.player_sprite.center_x, self.player_sprite.center_y = START_POS
        self.player_list.append(self.player_sprite)

        # set up the map from Tiled
        map_name = "data/maps/level1.json"
        self.tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING, hit_box_algorithm="Detailed")

        # sprite_list is from Tiled map layers
        self.door = Door(2100, 180)
        self.background = self.tile_map.sprite_lists["background"]
        self.bkg_list = self.tile_map.sprite_lists["bkg"]
        self.spike_list = self.tile_map.sprite_lists["spikes"]
        self.arrow_sprite = arcade.Sprite("data/sprites/arrow_left.png", scale=0.25, center_x=2200, center_y=400)
        self.arrow_sprite.visible = False

        self.ceiling_list = MovingWall(self.tile_map.sprite_lists["ceiling"], 0.15, 400, 'vertical')

        # Set up triggers and traps
        self.trig1_list = self.tile_map.sprite_lists["trig1"]
        self.gap1_list = MovingWall(self.tile_map.sprite_lists["gap1"], 10, 400, 'vertical')

        self.trig2_list = self.tile_map.sprite_lists["trig2"]
        self.triggered2 = False
        self.spike2_list = self.tile_map.sprite_lists["spike2"]

        self.trig3_list = self.tile_map.sprite_lists["trig3"]
        self.gap3_list = MovingWall(self.tile_map.sprite_lists["gap3"], 0.2, 200, 'horizontal')

        self.trig4_list = self.tile_map.sprite_lists["trig4"]
        self.triggered4 = False

        self.trig5_list = self.tile_map.sprite_lists["trig5"]
        self.gap5_list = MovingWall(self.tile_map.sprite_lists["gap5"], 10, 400, 'vertical')

        self.moving_wall_list = [self.gap1_list, self.gap3_list, self.gap5_list]
        self.vis_sprites_list = [self.bkg_list, self.gap1_list.wall_list, self.gap3_list.wall_list, self.gap5_list.wall_list]

        # Set the background color to what is specified in the map
        # if self.tile_map.background_color:
        #     arcade.set_background_color(self.tile_map.background_color)

        # setup physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, 
            self.vis_sprites_list, 
            GRAVITY)
        
        self.game_on = True
        print("level 1 started")
        self.level_start_time = time.time()


    def on_draw(self):
        arcade.start_render()

        # select the camera to use before drawing sprites
        self.camera_sprites.use()

        self.background.draw()
        self.door.draw()
        self.player_list.draw()
        # self.player_list.draw_hit_boxes()
        self.ceiling_list.wall_list.draw()
        # draw the sprite lists
        for sprite_list in self.vis_sprites_list:
            sprite_list.draw()
        self.spike_list.draw()
        self.spike2_list.draw()
        self.arrow_sprite.draw()

        # Run the GLSL code
        if self.particle_run:
            self.shadertoy.render(time=self.time)
            # stop particle rendering after the configured burst time
            if self.time > self.time_particle_start + self.PARTICLE_BURST_TIME:
                self.particle_run = False

        # draw the gui
        self.camera_gui.use()
        elapsed = max(0.0, time.time() - self.level_start_time)
        elapsed_minutes = int(elapsed) // 60
        elapsed_seconds = int(elapsed) % 60
        if elapsed_minutes > 0:
            elapsed_text = f"Time: {elapsed_minutes}m {elapsed_seconds:02d}s"
        else:
            elapsed_text = f"Time: {elapsed_seconds}s"
        arcade.draw_text(f"fps: {round(arcade.get_fps(), 2)}", 50, 500, font_size=16)
        arcade.draw_text(f"Deaths: {self.death}", 50, 550, font_size=16)
        arcade.draw_text(elapsed_text, 50, 525, font_size=16)
        arcade.draw_text(f"x: {round(self.player_sprite.center_x)}; y: {round(self.player_sprite.center_y)}", 50, 50, font_size=16)
        if self.paused:
            self.draw_pause_overlay()

    def draw_pause_overlay(self):
        """Draw pause overlay and controls."""
        w = self.window.width
        h = self.window.height
        arcade.draw_rectangle_filled(w / 2, h / 2, w, h, (0, 0, 0, 180))
        arcade.draw_text("Paused", w / 2, h / 2 + 80, (255, 255, 255), 32, anchor_x="center")
        arcade.draw_text("ESC: Back to Game", w / 2, h / 2 + 20, (230, 230, 230), 18, anchor_x="center")
        arcade.draw_text("R: Restart", w / 2, h / 2 - 10, (230, 230, 230), 18, anchor_x="center")
        arcade.draw_text("Q: Main Menu", w / 2, h / 2 - 40, (230, 230, 230), 18, anchor_x="center")
        
    
    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """
        if key == arcade.key.ESCAPE:
            self.paused = not self.paused
            return
        if self.paused:
            if key == arcade.key.R:
                self.paused = False
                self.window.show_view(self.__class__(self.window))
            elif key == arcade.key.Q:
                self.paused = False
                self.window.show_view(self.window.menu_view)
            return
        if not self.game_on:
            return
        if key == arcade.key.UP or key == arcade.key.SPACE or key == arcade.key.W:
            self.jump_pressed = True
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True


    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP or key == arcade.key.SPACE or key == arcade.key.W:
            self.jump_pressed = False
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False


    def on_mouse_press(self, x, y, button, modifiers):
        """ called whenver mouse is clicked """
        if button == arcade.MOUSE_BUTTON_LEFT:
            print("left mouse button pressed at ", x, y)
        if button == arcade.MOUSE_BUTTON_RIGHT:
            print("right mouse button pressed at ", x, y)

    def _play_jump_sound(self):
        if self.jump_sound_ready:
            arcade.play_sound(self.jump_sound)
            self.jump_sound_ready = False


    def update(self, delta_time):
        """ Movement and game logic """
        if self.paused:
            return
        self.time += delta_time
        self.frame_cnt += 1

        # If we're currently running the reset particle burst, wait until it finishes
        if self.is_resetting:
            # If the burst duration is over, finalize the reset
            if self.time - self.reset_start_time >= self.PARTICLE_BURST_TIME:
                self.finish_reset()
            # While the burst is active, do not advance game logic
            return
        
        if not self.game_on:
            self.player_sprite.center_x = self.door.pos_x
            self.player_sprite.center_y = self.door.pos_y
            self.left_pressed = False
            self.right_pressed = False
            self.jump_pressed = False
            if self.door.move_over:
                self.level_complete()
        
        if not self.ceiling_list.is_moving:
            self.ceiling_list.start_moving()

        # earthquake
        # print(self.time % 1)
        if self.game_on and self.frame_cnt % 20 == 0 and self.time > 0.5:
            if not self.triggered4:
                self.earthquake_camera(1.5, 0.4)
            else:
                self.earthquake_camera(2.0, 0.9)

        # Call update on all sprites
        self.door.update()
        self.player_list.update()
        self.player_list.update_animation()
        for wall_list in self.moving_wall_list:
            wall_list.update()
        if self.game_on:
            self.physics_engine.update()
            self.ceiling_list.update()
        
        # Calculate speed based on the keys pressed, if in air, does not stop immedietly
        self.player_sprite.change_x *= 0.92
        # self.player_sprite.change_x = 0

        on_ground = self.physics_engine.can_jump()
        if on_ground and not self.was_on_ground:
            self.jump_sound_ready = True
        if on_ground:
            self.frames_since_land = 0
            self.player_sprite.change_x = 0
            if self.jump_pressed:
                self.player_sprite.change_y = JUMP_SPEED
                self._play_jump_sound()
        else:
            # coyote time.
            self.frames_since_land += 1
            if self.jump_pressed and self.frames_since_land <= 2 and self.player_sprite.change_y < 2:
                self.player_sprite.change_y = JUMP_SPEED
                self._play_jump_sound()
        self.was_on_ground = on_ground

        if self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -MOVE_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = MOVE_SPEED

        if self.player_sprite.change_x > 0.02:
            # moving right
            self.set_anim(384)
        elif self.player_sprite.change_x < -0.02:
            # moving left
            self.set_anim(256)
        else:
            self.clear_anim(0, 0)

        spike_hit = arcade.check_for_collision_with_lists(self.player_sprite, [self.spike_list, self.spike2_list, self.ceiling_list.wall_list])
        if spike_hit:
            self.reset()

        # out of limit, death
        if self.player_sprite.center_y < -20:
            self.reset()

        if not self.game_on:
            return
        
        # trigger traps
        if not self.gap1_list.triggered:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trig1_list)
            if trigger_hit:
                self.gap1_list.start_moving()

        if not self.triggered2:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trig2_list)
            if trigger_hit:
                self.triggered2 = True
                self.spike2_list.visible = True

        if not self.gap3_list.triggered:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trig3_list)
            if trigger_hit:
                self.gap3_list.start_moving()
        
        if not self.triggered4:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trig4_list)
            if trigger_hit:
                self.triggered4 = True
                print("trig4 touched")
                # door moves, ceiling comes down faster
                self.door.start_moving_right(5, 300)
                self.ceiling_list.move_speed = 0.4
                self.arrow_sprite.visible = True

        if self.triggered4 and not self.gap5_list.triggered:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, self.trig5_list)
            if trigger_hit:
                self.gap5_list.start_moving()

        # check if touched the door
        collided_w_door = self.door.check_collision(self.player_sprite.left, self.player_sprite.right, self.player_sprite.bottom)
        if collided_w_door:
            print(collided_w_door)
            self.game_on = False
            self.game_over()

        # Scroll the screen to the player
        self.scroll_to_player()

    def reset(self):
        """
        resets the scene after death
        """
        # Start the particle burst and freeze the game; the actual reset will occur in finish_reset() after the burst duration elapses.
        # Set uniform data to send to the GLSL shader
        # Convert world position to screen (camera) coordinates so shader lines up with what the player sees.
        screen_x = self.player_sprite.center_x - self.view_left
        screen_y = self.player_sprite.center_y - CAMERA_OFFSET_Y
        try:
            self.shadertoy.program['pos'] = (screen_x, screen_y)
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
        self.was_on_ground = False
        self.jump_sound_ready = True
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.player_list.visible = False
        arcade.print_timings()

    def finish_reset(self):
        """Complete the reset after the particle burst has finished."""
        # stop rendering particles
        self.particle_run = False
        self.is_resetting = False
        self.death += 1

        # reset moving parts
        self.door.reset()
        self.ceiling_list.reset()
        for wall_list in self.moving_wall_list:
            if wall_list.triggered:
                wall_list.reset()
        self.triggered2 = False
        self.triggered4 = False
        self.spike2_list.visible = False
        self.arrow_sprite.visible = False

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
        self.door.start_moving_down()
        self.shake_camera()

    
    def earthquake_camera(self, magnitude, shake_damping):
        """ Shake the camera constantly """
        
        shake_direction = random.random() * 2 * math.pi
        shake_vector = Vec2(
            math.cos(shake_direction) * magnitude,
            math.sin(shake_direction) * magnitude
        )
        # shake_vector = Vec2(magnitude, magnitude * 0.6)
        shake_speed = 1.0
        self.camera_sprites.shake(shake_vector,
                                    speed=shake_speed,
                                    damping=shake_damping)

    
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
        # Scroll left
        left_boundary = self.view_left + VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary

        # # Scroll up
        # top_boundary = self.view_bottom + self.height - VIEWPORT_MARGIN
        # if self.player_sprite.top > top_boundary:
        #     self.view_bottom += self.player_sprite.top - top_boundary

        # # Scroll down
        # bottom_boundary = self.view_bottom + VIEWPORT_MARGIN
        # if self.player_sprite.bottom < bottom_boundary:
        #     self.view_bottom -= bottom_boundary - self.player_sprite.bottom

        # Scroll to the proper location
        self.camera_sprites.move_to(Vec2(self.view_left, CAMERA_OFFSET_Y), CAMERA_SPEED)


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
        elapsed = time.time() - self.level_start_time
        attempts = self.death + 1
        from level2 import Level2
        end_view = EndScreen(self.window, "Level 1 Complete", elapsed, attempts, self.__class__, Level2)
        self.window.show_view(end_view)
        


def main():
    """ main method """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "level 1", vsync=True)
    arcade.enable_timings()
    window.show_view(Level1(window))
    arcade.run()

if __name__ == "__main__":
    main()
