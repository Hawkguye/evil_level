import arcade
from arcade.experimental import Shadertoy
import random
import math
import time
from pyglet.math import Vec2

from modals import MovingWall, Door, FireBall, Missile, Button, EndScreen


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# constants
SPRITE_SCALING_PLAYER = 0.25
TILE_SCALING = 0.25
MOVE_SPEED = 3
JUMP_SPEED = 4
JETPACK_SPEED = 1.0
GRAVITY = 0.2
PYMUNK_GRAVITY = 0
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600
PLAYER_DAMPING = 1.0
JETPACK_FUEL_MAX = 100
JETPACK_FUEL_REGEN = 2
JETPACK_FUEL_BURN = 1

FIREBALL_MIN_SPEED = 500
FIREBALL_MAX_SPEED = 700
FIREBALL_FRICTION = 0.0
FIREBALL_ELASTICITY = 1.0

VIEWPORT_MARGIN = 500
CAMERA_SPEED = 0.5
CAMERA_OFFSET_Y = 0

START_POS = (500, 900)

SPRITE_PATH = "data/sprites/sprite_jetpack.png"


class Cannon:
    """Cannon class that spawns missiles periodically"""
    
    def __init__(self, pos_x: int, pos_y: int, player_sprite, flipped = False):
        """Initialize cannon at given position"""
        self.sprite = arcade.Sprite()
        self.sprite.scale = 0.5
        self.sprite.center_x = pos_x
        self.sprite.center_y = pos_y
        self.flipped = flipped
        self.sprite.flipped_horizontally = self.flipped
        self.player_sprite = player_sprite
        self.missile_list = []
        self.last_spawn_time = 0.0
        self.spawn_interval = 3.0  # spawn every 3 seconds
        self.animation_duration = 0.5  # duration of firing animation in seconds
        self.firing_start_time = None
        
        # Load animation textures
        self.idle_texture = arcade.load_texture("data/sprites/cannon.png", flipped_horizontally=self.flipped)
        self.firing_textures = [
            arcade.load_texture("data/sprites/cannon2.png", flipped_horizontally=self.flipped),
            arcade.load_texture("data/sprites/cannon3.png", flipped_horizontally=self.flipped),
            arcade.load_texture("data/sprites/cannon4.png", flipped_horizontally=self.flipped),
            arcade.load_texture("data/sprites/cannon5.png", flipped_horizontally=self.flipped),
        ]
        
        # Set initial texture to idle
        self.sprite.texture = self.idle_texture
    
    def draw(self):
        """Draw the cannon and all active missiles"""
        self.sprite.draw()
        for missile in self.missile_list:
            missile.draw()
    
    def start_firing_animation(self, current_time: float):
        """Start the firing animation"""
        self.firing_start_time = current_time
        # Set to first frame of firing animation
        self.sprite.texture = self.firing_textures[0]
    
    def update(self, current_time: float):
        """Update cannon and missiles, spawn new missile if interval elapsed"""
        # Spawn new missile if enough time has passed
        if current_time - self.last_spawn_time >= self.spawn_interval:
            if (self.flipped and self.player_sprite.center_x < 735) or (not self.flipped and self.player_sprite.center_x > 735):
                missile = Missile(self.sprite.center_x + 30 if self.flipped else self.sprite.center_x - 30, self.sprite.center_y - 10, self.player_sprite, "right" if self.flipped else "left")
                self.missile_list.append(missile)
                self.start_firing_animation(current_time)
            self.last_spawn_time = current_time
            # Start firing animation
        
        # Update firing animation
        if self.firing_start_time is not None:
            elapsed = current_time - self.firing_start_time
            if elapsed >= self.animation_duration:
                # Animation complete, return to idle
                self.sprite.texture = self.idle_texture
                self.firing_start_time = None
            else:
                # Calculate which frame to show
                frame_index = int((elapsed / self.animation_duration) * len(self.firing_textures))
                frame_index = min(frame_index, len(self.firing_textures) - 1)  # Clamp to valid range
                self.sprite.texture = self.firing_textures[frame_index]
        
        # Update all missiles
        for missile in self.missile_list[:]:  # Use slice to safely iterate while modifying
            missile.update()
    
    def reset(self, current_time: float = 0.0):
        """Reset cannon state"""
        self.missile_list.clear()
        self.last_spawn_time = current_time
        self.sprite.texture = self.idle_texture
        self.firing_start_time = None


class Level6(arcade.View):
    """ windows class """

    def __init__(self, window):
        """ initializer """
        super().__init__(window)

        # self.set_mouse_visible(False)

        self.game_on = False
        self.paused = False

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
        self.cannon = None
        self.cannon2 = None
        self.button_list = None
        
        # player info
        self.death = 0
        self.player_sprite = None
        self.level_start_time = 0.0

        # simple physics engine
        self.jetpack_fuel = JETPACK_FUEL_MAX
        self.jump_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.physics_engine = None
        self.pymunk_engine = None
        self.tile_map = None
        # coyote time
        self.frames_since_land = 0
        
        # CAMERAS
        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_sprites.move_to(Vec2(0, CAMERA_OFFSET_Y))
        # Used in scrolling
        self.view_bottom = 0
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
        print("level 6 starting...")
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
        map_name = "data/maps/level6.json"
        self.tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING, hit_box_algorithm="Detailed")

        # sprite_list is from Tiled map layers
        self.door = Door(1470, 276)
        self.door.can_be_touched = False
        self.door.opacity = 0  # Hide door until all buttons are pressed
        self.background = self.tile_map.sprite_lists["background"]
        self.platform_list = self.tile_map.sprite_lists["platforms"]
        
        self.button1 = Button(130, 736, False, True)
        self.button2 = Button(656, 950)
        self.button3 = Button(1225, 1232, False, True)
        self.button_list = [self.button1, self.button2, self.button3]
        self.buttons_pressed_count = 0

        self.fireball1 = FireBall(290, 620, 673)
        self.fireball2 = FireBall(460, 620, 635)
        self.fireball3 = FireBall(734, 620, 633)
        self.fireball4 = FireBall(990, 620, 640)
        self.fireball5 = FireBall(1168, 620, 610)
        self.fireball6 = FireBall(1400, 620, 665)
        self.fireball_list = [self.fireball1, self.fireball2, self.fireball3, self.fireball4, self.fireball5, self.fireball6]

        self.cannon = Cannon(170, 608, self.player_sprite, True)
        self.cannon2 = Cannon(1550, 608, self.player_sprite, False) # another one at (1550, 445)

        self.vis_sprites_list = [self.platform_list]

        # Set the background color to what is specified in the map
        # if self.tile_map.background_color:
        #     arcade.set_background_color(self.tile_map.background_color)

        # setup physics engine
        self.setup_physics()
        
        self.game_on = True
        print("level 6 started")
        self.level_start_time = time.time()


    def on_draw(self):
        arcade.start_render()

        # select the camera to use before drawing sprites
        self.camera_sprites.use()

        self.background.draw()
        # Only draw door if it's active (can_be_touched)
        if self.door.can_be_touched:
            self.door.draw()
        self.player_list.draw()
        self.cannon.draw()
        self.cannon2.draw()
        # Draw buttons
        for button in self.button_list:
            button.draw()
        # self.player_list.draw_hit_boxes()
        # draw the sprite lists
        for sprite_list in self.vis_sprites_list:
            sprite_list.draw()
        for fireball in self.fireball_list:
            fireball.draw()
        if not self.is_resetting and self.game_on:
            self.draw_fuel_bar()

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
        arcade.draw_text(f"jetpack fuel: {self.jetpack_fuel}; jump vel: {round(self.player_sprite.change_y, 2)}", 50, 450, font_size=16, color=(0, 0, 0))
        arcade.draw_text(f"fps: {round(arcade.get_fps(), 2)}", 50, 500, font_size=16)
        arcade.draw_text(f"Deaths: {self.death}", 50, 550, font_size=16)
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
            print("left mouse button pressed at ", round(x + self.view_left), round(y + self.view_bottom))


    def update(self, delta_time):
        """ Movement and game logic """
        if self.paused:
            return
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
            self.pymunk_engine.step(delta_time)
            self.cannon.update(self.time)
            self.cannon2.update(self.time)

        # Calculate speed based on the keys pressed, if in air, does not stop immediately
        self.player_sprite.change_x *= 0.97

        if self.physics_engine.can_jump():
            self.player_sprite.change_x = 0
            if self.jetpack_fuel < JETPACK_FUEL_MAX:
                self.jetpack_fuel = min(JETPACK_FUEL_MAX, self.jetpack_fuel + JETPACK_FUEL_REGEN)
            if self.jump_pressed:
                self.player_sprite.change_y = JUMP_SPEED
            # Disable jetpack particles when on ground
            self.jetpack_particle_run = False
        else:
            if self.jump_pressed and self.jetpack_fuel > 0:
                # if self.player_sprite.change_y < 0:
                #     self.player_sprite.change_y = 0
                self.player_sprite.change_y += JETPACK_SPEED
                self.jetpack_fuel = max(0, self.jetpack_fuel - JETPACK_FUEL_BURN)
                # Enable jetpack particles
                if not self.jetpack_particle_run:
                    self.jetpack_particle_run = True
                    self.jetpack_time_offset = self.time
                # Update particle position (below player sprite) continuously
                screen_x = self.player_sprite.center_x - self.view_left
                screen_y = self.player_sprite.center_y - self.view_bottom - 10
                try:
                    self.jetpack_shadertoy.program['pos'] = (screen_x, screen_y)
                    self.jetpack_shadertoy.program['timeOffset'] = self.jetpack_time_offset
                    self.jetpack_shadertoy.program['direction'] = self.player_sprite.change_x * -0.3
                except Exception:
                    pass
            else:
                # Disable jetpack particles when not active
                self.jetpack_particle_run = False
        if self.player_sprite.change_y > JUMP_SPEED:
            self.player_sprite.change_y = JUMP_SPEED

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
        # if self.player_sprite.center_y < 500:
        #     self.reset()

        if not self.game_on:
            return
        
        # Check button collisions
        for button in self.button_list:
            trigger_hit = arcade.check_for_collision_with_list(self.player_sprite, button.sprite_list)
            if not button.triggered and trigger_hit:
                # Button just got triggered
                button.touched()
                self.buttons_pressed_count += 1
                self.shake_camera()
            elif button.triggered and not trigger_hit:
                # Player left the button after triggering it, hide it
                button.sprite_list.visible = False
        
        # Show door when all buttons are pressed
        if self.buttons_pressed_count >= 3 and not self.door.can_be_touched:
            self.door.can_be_touched = True
            self.door.opacity = 255
        
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
        
        # Check missile collisions
        for missile in self.cannon.missile_list[:]:  # Use slice to safely iterate while modifying
            # Check collision with player
            collided_w_player = arcade.check_for_collision(self.player_sprite, missile.sprite)
            if collided_w_player:
                self.reset()
                break  # Reset will handle clearing missiles, so break to avoid processing more
            
            # Check collision with platforms
            collided_w_platform = arcade.check_for_collision_with_list(missile.sprite, self.platform_list)
            if collided_w_platform:
                # Trigger particle explosion at missile location
                self.trigger_particle_explosion(missile.pos_x, missile.pos_y)
                # Remove the missile
                self.cannon.missile_list.remove(missile)

        for missile in self.cannon2.missile_list[:]:  # Use slice to safely iterate while modifying
            # Check collision with player
            collided_w_player = arcade.check_for_collision(self.player_sprite, missile.sprite)
            if collided_w_player:
                self.reset()
                break  # Reset will handle clearing missiles, so break to avoid processing more
            
            # Check collision with platforms
            collided_w_platform = arcade.check_for_collision_with_list(missile.sprite, self.platform_list)
            if collided_w_platform:
                # Trigger particle explosion at missile location
                self.trigger_particle_explosion(missile.pos_x, missile.pos_y)
                # Remove the missile
                self.cannon2.missile_list.remove(missile)
        # Scroll the screen to the player
        self.scroll_to_player()

    def trigger_particle_explosion(self, world_x: float, world_y: float):
        """
        Trigger particle explosion at the given world coordinates
        """
        # Convert world position to screen (camera) coordinates so shader lines up with what the player sees.
        screen_x = world_x - self.view_left
        screen_y = world_y - self.view_bottom
        try:
            self.shadertoy.program['pos'] = (screen_x, screen_y)
            self.shadertoy.program['burstStart'] = self.time
        except Exception:
            pass
        
        self.particle_run = True
        self.time_particle_start = self.time

    def reset(self):
        """
        resets the scene after death
        """
        self.trigger_particle_explosion(self.player_sprite.center_x, self.player_sprite.center_y)
        self.shake_camera()
        # disable jetpack particles during reset
        self.jetpack_particle_run = False
        # record when the particle burst started
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
        self.door.can_be_touched = False
        self.door.opacity = 0  # Hide door again
        self.jetpack_fuel = JETPACK_FUEL_MAX
        self.reset_fireballs()
        self.cannon.reset(self.time)
        self.cannon2.reset(self.time)
        # Reset buttons
        for button in self.button_list:
            button.reset()
            button.sprite_list.visible = True
        self.buttons_pressed_count = 0
        self.player_sprite.center_x = START_POS[0]
        self.player_sprite.center_y = START_POS[1]
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
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
        self.view_left = self.player_sprite.center_x - (SCREEN_WIDTH / 2)
        self.view_bottom = self.player_sprite.center_y - (SCREEN_HEIGHT / 2)

        # Scroll to the proper location
        self.camera_sprites.move_to(Vec2(self.view_left, self.view_bottom), CAMERA_SPEED)


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
        from level5 import Level5
        end_view = EndScreen(self.window, "Level 6 Complete", elapsed, attempts, self.__class__, Level5)
        self.window.show_view(end_view)


    def draw_fuel_bar(self):
        # arcade.draw_xywh_rectangle_filled(910, 200, 20, self.jetpack_fuel * 2, (255, 98, 0))
        # arcade.draw_rectangle_outline(920, 300, 20, 200, (0, 0, 0), 5)
        x = int(self.player_sprite.center_x - 18)
        y = int(self.player_sprite.center_y)
        arcade.draw_xywh_rectangle_filled(x-3, y-25, 6, self.jetpack_fuel / 2, (255, 98, 0))
        arcade.draw_rectangle_outline(x, y, 6, 50, (0, 0, 0))

    def setup_physics(self):
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            self.vis_sprites_list,
            GRAVITY,
        )

        self.pymunk_engine = arcade.PymunkPhysicsEngine(gravity=(0, PYMUNK_GRAVITY), damping=1.0)
        self.pymunk_engine.add_sprite_list(
            self.platform_list,
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            friction=1.0,
            elasticity=FIREBALL_ELASTICITY,
        )

        for fireball in self.fireball_list:
            self.pymunk_engine.add_sprite(
                fireball.sprite,
                mass=0.5,
                friction=FIREBALL_FRICTION,
                elasticity=FIREBALL_ELASTICITY,
                moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                damping=1.0,
                gravity=(0, 0),
                collision_type="fireball",
            )

        self.reset_fireballs()

    def reset_fireballs(self):
        for fireball in self.fireball_list:
            fireball.sprite.center_x = fireball.init_x
            fireball.sprite.center_y = fireball.init_y
            self.pymunk_engine.set_position(fireball.sprite, (fireball.init_x, fireball.init_y))
            self.pymunk_engine.set_velocity(fireball.sprite, (0, 0))
            self.launch_fireball(fireball)

    def launch_fireball(self, fireball):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(FIREBALL_MIN_SPEED, FIREBALL_MAX_SPEED)
        velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
        self.pymunk_engine.set_velocity(fireball.sprite, velocity)

def main():
    """ main method """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "level 6", vsync=True)
    arcade.enable_timings()
    window.show_view(Level6(window))
    arcade.run()

if __name__ == "__main__":
    main()
