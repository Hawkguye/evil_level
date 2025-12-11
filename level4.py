import arcade
from arcade.experimental import Shadertoy
import random
import math
import time
from pyglet.math import Vec2

from modals import MovingWall, Door, FireBall


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# constants
SPRITE_SCALING_PLAYER = 0.25
TILE_SCALING = 0.25
MOVE_SPEED = 2
JUMP_SPEED = 3
JETPACK_SPEED = 0.4
GRAVITY = 0.2

VIEWPORT_MARGIN = 400
CAMERA_SPEED = 0.5
CAMERA_OFFSET_Y = 0

START_POS = (240, 250)

SPRITE_PATH = "data/sprites/sprite.png"


class Level4(arcade.View):
    """ windows class """

    def __init__(self, window):
        """ initializer """
        super().__init__(window)

        # self.set_mouse_visible(False)

        self.game_on = False

        # sprite lists
        self.player_list = None
        self.platform_list = None
        self.background = None
        self.spike_list = None
        self.door = None
        self.vis_sprites_list = None
        self.moving_wall_list = None

        # specific to the levels
        self.fireball1 = None
        self.fireball2 = None
        self.fireball3 = None
        self.fireball4 = None
        self.fireball5 = None
        self.fireball6 = None
        self.fireball_list = None
        
        # player info
        self.death = 0
        self.player_sprite = None

        # simple physics engine
        self.jetpack_fuel = 100
        self.jump_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.physics_engine = None
        self.tile_map = None
        # coyote time
        self.frames_since_land = 0
        
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
        
        # jetpack particle shader
        self.jetpack_particle_run = False
        self.jetpack_time_offset = 0.0
        jetpack_file_name = "jetpack_particles.glsl"
        self.jetpack_shadertoy = Shadertoy(size=(SCREEN_WIDTH, SCREEN_HEIGHT),
                                           main_source=open(jetpack_file_name).read())
        
        # arcade.enable_timings()


    def on_show_view(self):
        """ set up the game and initialize the variables """
        print("level 4 starting...")
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
        map_name = "data/maps/level4.json"
        self.tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING, hit_box_algorithm="Detailed")

        # sprite_list is from Tiled map layers
        self.door = Door(2100, 180)
        self.background = self.tile_map.sprite_lists["background"]
        self.platform_list = self.tile_map.sprite_lists["platforms"]

        self.fireball1 = FireBall(270, 480, 160)
        self.fireball2 = FireBall(462, 480, 224)
        self.fireball3 = FireBall(734, 480, 320)
        self.fireball4 = FireBall(976, 480, 128)
        self.fireball5 = FireBall(1168, 480, 192)
        self.fireball6 = FireBall(1392, 480, 256)
        self.fireball_list = [self.fireball1, self.fireball2, self.fireball3, self.fireball4, self.fireball5, self.fireball6]

        self.vis_sprites_list = [self.platform_list]

        # Set the background color to what is specified in the map
        # if self.tile_map.background_color:
        #     arcade.set_background_color(self.tile_map.background_color)

        # setup physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, 
            self.vis_sprites_list, 
            GRAVITY)
        
        self.game_on = True
        print("level 4 started")


    def on_draw(self):
        arcade.start_render()

        # select the camera to use before drawing sprites
        self.camera_sprites.use()

        self.background.draw()
        self.door.draw()
        self.player_list.draw()
        # self.player_list.draw_hit_boxes()
        # draw the sprite lists
        for sprite_list in self.vis_sprites_list:
            sprite_list.draw()
        for fireball in self.fireball_list:
            fireball.draw()

        # Run the GLSL code
        if self.particle_run:
            self.shadertoy.render(time=self.time)
            # stop particle rendering after the configured burst time
            if self.time > self.time_particle_start + self.PARTICLE_BURST_TIME:
                self.particle_run = False
        
        # Run jetpack particle shader when jetpack is active
        if self.jetpack_particle_run:
            self.jetpack_shadertoy.render(time=self.time)

        # draw the gui
        self.camera_gui.use()
        arcade.draw_text(f"jetpack fuel: {self.jetpack_fuel}; jump vel: {round(self.player_sprite.change_y)}", 50, 450, font_size=16, color=(0, 0, 0))
        arcade.draw_text(f"fps: {round(arcade.get_fps(), 2)}", 50, 500, font_size=16)
        arcade.draw_text(f"Deaths: {self.death}", 50, 550, font_size=16)
        arcade.draw_text(f"x: {round(self.player_sprite.center_x)}; y: {round(self.player_sprite.center_y)}", 50, 50, font_size=16)
        self.draw_fuel_bar()
        
    
    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.window.menu_view)
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


    def update(self, delta_time):
        """ Movement and game logic """
        self.time += delta_time
        self.frame_cnt += 1

        # If we're currently running the reset particle burst, wait until it finishes
        if self.is_resetting:
            # Disable jetpack particles during reset
            self.jetpack_particle_run = False
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
            self.jetpack_particle_run = False
            if self.door.move_over:
                self.level_complete()
        
        # Call update on all sprites
        self.door.update()
        self.player_list.update()
        self.player_list.update_animation()
        if self.game_on:
            self.physics_engine.update()
            for fireball in self.fireball_list:
                fireball.update(GRAVITY)
        
        # Calculate speed based on the keys pressed, if in air, does not stop immedietly
        self.player_sprite.change_x *= 0.92
        # self.player_sprite.change_x = 0

        if self.physics_engine.can_jump():
            self.player_sprite.change_x = 0
            if self.jetpack_fuel < 100:
                self.jetpack_fuel += 1
            if self.jump_pressed:
                self.player_sprite.change_y = JUMP_SPEED
            # Disable jetpack particles when on ground
            self.jetpack_particle_run = False
        else:
            if self.jump_pressed and self.jetpack_fuel > 0:
                if self.player_sprite.change_y < 0:
                    self.player_sprite.change_y = 0
                self.player_sprite.change_y += JETPACK_SPEED
                self.jetpack_fuel -= 1
                # Enable jetpack particles
                if not self.jetpack_particle_run:
                    self.jetpack_particle_run = True
                    self.jetpack_time_offset = self.time
                # Update particle position (below player sprite) continuously
                screen_x = self.player_sprite.center_x - self.view_left
                screen_y = self.player_sprite.center_y - CAMERA_OFFSET_Y - 20  # Offset below player
                try:
                    self.jetpack_shadertoy.program['pos'] = (screen_x, screen_y)
                    self.jetpack_shadertoy.program['timeOffset'] = self.jetpack_time_offset
                except Exception:
                    pass
            else:
                # Disable jetpack particles when not active
                self.jetpack_particle_run = False
        if self.player_sprite.change_y > 3:
            self.player_sprite.change_y = 3

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

        # out of limit, death
        if self.player_sprite.center_y < 0:
            self.reset()

        if not self.game_on:
            return
        
        # check if touched the door
        collided_w_door = self.door.check_collision(self.player_sprite.left, self.player_sprite.right, self.player_sprite.bottom)
        if collided_w_door:
            print(collided_w_door)
            self.game_on = False
            self.game_over()
        
        for fireball in self.fireball_list:
            # bounced = arcade.check_for_collision_with_list(fireball.sprite, self.platform_list)
            # if bounced:
            #     fireball.bounce()
                
            collided_w_player = arcade.check_for_collision(self.player_sprite, fireball.sprite)
            if collided_w_player:
                self.reset()
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
        # disable jetpack particles during reset
        self.jetpack_particle_run = False
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
        arcade.print_timings()

    def finish_reset(self):
        """Complete the reset after the particle burst has finished."""
        # stop rendering particles
        self.particle_run = False
        self.is_resetting = False
        self.death += 1

        # reset moving parts
        self.door.reset()
        self.jetpack_fuel = 100
        for fireball in self.fireball_list:
            fireball.reset()
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
        print("level complete")
        # self.window.show_view(self.window.menu_view)


    def draw_fuel_bar(self):
        arcade.draw_xywh_rectangle_filled(910, 200, 20, self.jetpack_fuel * 2, (255, 98, 0))
        arcade.draw_rectangle_outline(920, 300, 20, 200, (0, 0, 0), 5)
        

def main():
    """ main method """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "level 4", vsync=True)
    arcade.enable_timings()
    window.show_view(Level4(window))
    arcade.run()

if __name__ == "__main__":
    main()