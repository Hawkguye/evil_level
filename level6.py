import arcade
from arcade.experimental import Shadertoy
import random
import math
import time
from pyglet.math import Vec2

from modals import EndScreen


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# constants
SPRITE_SCALING_PLAYER = 0.25
TILE_SCALING = 0.25
MOVE_SPEED = 2
JUMP_SPEED = 3
JETPACK_SPEED = 0.4
GRAVITY = 0.15

VIEWPORT_MARGIN = 400
CAMERA_SPEED = 0.5
CAMERA_OFFSET_Y = 0

START_POS = (200, 900)

SPRITE_PATH = "data/sprites/sprite_jetpack.png"

class Stone(arcade.Sprite):
    """Stone class for throwable objects"""
    def __init__(self, center_x: float, center_y: float, scale: float = 0.25):
        super().__init__("data/sprites/stone.png", scale=scale)
        self.center_x = center_x
        self.center_y = center_y
        self.v_x = 0.0
        self.v_y = 0.0
        self.thrown = False  # Whether this stone has been thrown

class ThrownStone(arcade.Sprite):
    """Thrown stone with physics"""
    def __init__(self, center_x: float, center_y: float, v_x: float, v_y: float):
        super().__init__("data/sprites/stone.png", scale=0.25)
        self.center_x = center_x
        self.center_y = center_y
        self.v_x = v_x
        self.v_y = v_y

class BOSS(arcade.AnimatedTimeBasedSprite):
    def __init__(self, center_x: float = 0, center_y: float = 0, scale: float = 1.0):
        super().__init__()
        self.boss_sprite_path = "data/sprites/stickman.png"
        for i in range(4):
            texture = arcade.load_texture(self.boss_sprite_path, i * 256, 0, 256, 256)
            anim = arcade.AnimationKeyframe(i, 150, texture)  # 250ms per frame
            self.frames.append(anim)
        self.scale = scale
        self.center_x = center_x
        self.center_y = center_y
        self.max_health = 90
        self.health = 90
        self.is_hurt = False
        self.hurt_end_time = 0.0
        self.is_dead = False
    
    def hurt(self, current_time: float):
        """Apply damage and swap to hurt textures"""
        self.health -= 15
        if self.health <= 0:
            self.health = 0
            print("BOSS defeated")
        self.is_hurt = True
        self.hurt_end_time = current_time + 0.3
        self.frames.clear()
        for i in range(4):
            # Use the red-tinted row of the sprite sheet
            texture = arcade.load_texture(self.boss_sprite_path, i * 256, 256, 256, 256)
            anim = arcade.AnimationKeyframe(i, 150, texture)
            self.frames.append(anim)
    
    def reset_anim(self):
        """Restore normal textures"""
        self.frames.clear()
        for i in range(4):
            texture = arcade.load_texture(self.boss_sprite_path, i * 256, 0, 256, 256)
            anim = arcade.AnimationKeyframe(i, 150, texture)
            self.frames.append(anim)
        self.is_hurt = False
        self.hurt_end_time = 0.0
        self.is_dead = False
    
    def set_death_anim(self):
        """Swap to death animation row."""
        self.frames.clear()
        for i in range(4):
            texture = arcade.load_texture(self.boss_sprite_path, i * 256, 512, 256, 256)
            anim = arcade.AnimationKeyframe(i, 250, texture)
            self.frames.append(anim)
        # Reset animation to the first frame
        self.texture = self.frames[0].texture
        if hasattr(self, "cur_frame_idx"):
            self.cur_frame_idx = 0
        if hasattr(self, "time_since_last_frame"):
            self.time_since_last_frame = 0.0
        self.is_dead = True

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
        self.vis_sprites_list = None
        self.moving_wall_list = None
        self.boss_list = None
        self.obstacle_list = None
        self.stone_list = None
        self.thrown_stone_list = None

        # specific to the levels
        self.button_list = None
        
        # stone inventory
        self.stone_inventory = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.stone_icon_texture = None
        
        # camera scrolling
        self.camera_target_x = 0
        self.scroll_speed = 2.0
        self.scroll_deceleration = 0.02
        self.camera_max_x = 200
        
        # obstacle spawning
        self.obstacle_spawn_timer = 0.0
        self.obstacle_spawn_interval = 0.5
        self.obstacle_speed = 3.0
        self.ground_spike_list = None
        self.ground_spike_spawn_timer = 0.0
        self.ground_spike_spawn_interval = 0.5
        
        # stone spawning
        self.stone_spawn_timer = 0.0
        self.stone_spawn_interval = 2.0
        
        # player info
        self.death = 0
        self.player_sprite = None
        self.boss_sprite = None
        self.boss_defeated = False
        self.boss_fade_started = False
        self.player_anim_stopped = False
        self.fade_active = False
        self.fade_alpha = 0
        self.post_boss_cleared = False
        self.boss_death_active = False
        self.boss_death_start_time = 0.0
        self.boss_death_active = False
        self.boss_death_start_time = 0.0
        self.fade_speed = 2
        self.boss_death_duration = 1.0
        self.level_start_time = 0.0

        # simple physics engine
        self.jetpack_fuel = 100
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
        self.jetpack_sound = arcade.load_sound("data/sounds/jetpack.mp3", streaming=True)
        self.jetpack_sound_player = None
        
        # CAMERAS
        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_sprites.move_to(Vec2(0, CAMERA_OFFSET_Y))

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
        self.boss_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.ground_spike_list = arcade.SpriteList()
        self.stone_list = arcade.SpriteList()
        self.thrown_stone_list = arcade.SpriteList()
        self.player_sprite = arcade.AnimatedTimeBasedSprite()
        self.stone_icon_texture = arcade.load_texture("data/sprites/stone.png")

        # set up player animation sprites
        texture = arcade.load_texture(SPRITE_PATH, 0, 0, 128, 128)
        anim = arcade.AnimationKeyframe(1, 10, texture)
        self.player_sprite.frames.append(anim)
        self.player_sprite.scale = SPRITE_SCALING_PLAYER
        self.player_sprite.set_hit_box([(-32, -48), (32, -48), (32, 48), (-32, 48)])

        # set up the player sprite
        self.player_sprite.center_x, self.player_sprite.center_y = START_POS
        self.player_list.append(self.player_sprite)

        # set up boss sprite
        self.boss_sprite = BOSS(center_x=100, center_y=205, scale=1.0)
        self.boss_sprite.max_health = 100
        self.boss_sprite.health = 100
        self.boss_list.append(self.boss_sprite)
        
        # reset camera scrolling
        self.camera_target_x = 0
        self.scroll_speed = 2.0
        self.obstacle_spawn_timer = 0.0
        self.ground_spike_spawn_timer = 0.0
        self.stone_spawn_timer = 0.0
        self.stone_inventory = 0
        self.boss_defeated = False
        self.boss_fade_started = False
        self.player_anim_stopped = False
        self.fade_active = False
        self.fade_alpha = 0

        # set up the map from Tiled
        map_name = "data/maps/level6.json"
        self.tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING, hit_box_algorithm="Detailed")

        # sprite_list is from Tiled map layers
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

        self.cannon = Cannon(170, 445, self.player_sprite, True)
        self.cannon2 = Cannon(1550, 480, self.player_sprite, False) # another one at (1550, 445)

        self.vis_sprites_list = [self.platform_list]

        # setup physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, 
            self.vis_sprites_list, 
            GRAVITY)
        
        self.game_on = True
        print("level 6 started")
        self.level_start_time = time.time()


    def on_draw(self):
        arcade.start_render()

        # select the camera to use before drawing sprites
        self.camera_sprites.use()

        self.background.draw()
        self.obstacle_list.draw()
        # self.obstacle_list.draw_hit_boxes()
        self.ground_spike_list.draw()
        # self.ground_spike_list.draw_hit_boxes()
        self.player_list.draw()
        # self.player_list.draw_hit_boxes()
        # draw the sprite lists
        for sprite_list in self.vis_sprites_list:
            sprite_list.draw()
        if not self.is_resetting and self.game_on:
            self.draw_fuel_bar()
        self.stone_list.draw()
        self.thrown_stone_list.draw()
        self.boss_list.draw()
        if self.game_on and not self.boss_death_active:
            self.draw_boss_health_bar()
            self.draw_trajectory_arrow()

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
        # arcade.draw_text(f"jetpack fuel: {self.jetpack_fuel}; jump vel: {round(self.player_sprite.change_y)}", 50, 450, font_size=16, color=(0, 0, 0))
        arcade.draw_text(f"fps: {round(arcade.get_fps(), 2)}", 50, 500, font_size=16)
        arcade.draw_text(f"Deaths: {self.death}", 50, 550, font_size=16)
        # arcade.draw_text(f"Stones: {self.stone_inventory}", 50, 400, font_size=16, color=(0, 0, 0))
        # arcade.draw_text(f"x: {round(self.player_sprite.center_x)}; y: {round(self.player_sprite.center_y)}", 50, 50, font_size=16)
        self.draw_stone_ui()
        if self.paused:
            self.draw_pause_overlay()
        if self.fade_active:
            arcade.draw_rectangle_filled(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                (0, 0, 0, self.fade_alpha),
            )

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
            if self.paused:
                self._stop_jetpack_sound()
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


    def on_mouse_motion(self, x, y, dx, dy):
        """Called when the mouse moves"""
        self.mouse_x = x
        self.mouse_y = y
    
    def on_mouse_press(self, x, y, button, modifiers):
        """ called whenver mouse is clicked """
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Throw stone if player has stones in inventory
            if self.game_on and self.stone_inventory > 0:
                self.throw_stone(x, y)
            else:
                print("left mouse button pressed at ", round(x + self.camera_target_x), round(y + CAMERA_OFFSET_Y))

    def _play_jump_sound(self):
        if self.jump_sound_ready:
            arcade.play_sound(self.jump_sound)
            self.jump_sound_ready = False

    def _start_jetpack_sound(self):
        if self.jetpack_sound_player is None:
            self.jetpack_sound_player = arcade.play_sound(self.jetpack_sound, looping=True)

    def _stop_jetpack_sound(self):
        if self.jetpack_sound_player is not None:
            arcade.stop_sound(self.jetpack_sound_player)
            self.jetpack_sound_player = None


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
        
        if self.fade_active:
            self.update_end_fade()
            return
        
        # Camera scrolling (slow down after boss defeat)
        if self.boss_defeated and self.scroll_speed > 0:
            self.scroll_speed = max(0, self.scroll_speed - self.scroll_deceleration * delta_time * 60)
        if self.camera_target_x < self.camera_max_x and self.scroll_speed > 0:
            move_amount = self.scroll_speed * delta_time * 60
            self.camera_target_x += move_amount
            if self.camera_target_x > self.camera_max_x:
                self.camera_target_x = self.camera_max_x
            
            # Move BOSS and player right at same pace as camera (only while camera is scrolling)
            if self.game_on and not self.boss_defeated:
                self.boss_sprite.center_x += move_amount
                self.player_sprite.center_x += move_amount
        if self.boss_defeated:
            self.handle_boss_fade_and_idle()
        
        # Update obstacles
        for obstacle in self.obstacle_list:
            obstacle.center_x -= self.obstacle_speed * delta_time * 60
            if obstacle.center_x < -100:
                obstacle.remove_from_sprite_lists()
        
        # Update ground spikes
        for spike in self.ground_spike_list:
            spike.center_x -= self.obstacle_speed * delta_time * 60
            if spike.center_x < -100:
                spike.remove_from_sprite_lists()
        
        # Update stones on ground
        for stone in self.stone_list:
            stone.center_x -= self.obstacle_speed * delta_time * 60
            if stone.center_x < -100:
                stone.remove_from_sprite_lists()
        
        # Update thrown stones
        for thrown_stone in self.thrown_stone_list:
            thrown_stone.v_y -= GRAVITY * delta_time * 60
            thrown_stone.center_x += thrown_stone.v_x * delta_time * 60
            thrown_stone.center_y += thrown_stone.v_y * delta_time * 60
            # Remove if off screen
            if thrown_stone.center_x < -100 or thrown_stone.center_x > self.player_sprite.center_x + SCREEN_WIDTH + 200:
                thrown_stone.remove_from_sprite_lists()
            if thrown_stone.center_y < -100:
                thrown_stone.remove_from_sprite_lists()
        
        # Spawn obstacles
        if self.game_on and not self.boss_defeated:
            self.obstacle_spawn_timer += delta_time
            if self.obstacle_spawn_timer >= self.obstacle_spawn_interval:
                self.spawn_obstacle()
                self.obstacle_spawn_timer = 0.0
                self.obstacle_spawn_interval = random.uniform(0.3, 1.0)
            
            # Spawn ground spikes
            self.ground_spike_spawn_timer += delta_time
            if self.ground_spike_spawn_timer >= self.ground_spike_spawn_interval:
                self.spawn_ground_spike()
                self.ground_spike_spawn_timer = 0.0
                self.ground_spike_spawn_interval = random.uniform(1.5, 2.5)
            
            # Spawn stones
            self.stone_spawn_timer += delta_time
            if self.stone_spawn_timer >= self.stone_spawn_interval:
                self.spawn_stone()
                self.stone_spawn_timer = 0.0
                self.stone_spawn_interval = random.uniform(1.5, 3.0)
        
        # Check stone pickup
        if self.game_on:
            stone_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.stone_list)
            for stone in stone_hit_list:
                stone.remove_from_sprite_lists()
                self.stone_inventory += 1
        
        # Check thrown stone collisions with BOSS
        if self.game_on:
            boss_hit_list = arcade.check_for_collision_with_list(self.boss_sprite, self.thrown_stone_list)
            for thrown_stone in boss_hit_list:
                thrown_stone.remove_from_sprite_lists()
                self.boss_sprite.hurt(self.time)
            # Reset boss animation after hurt duration
            if self.boss_sprite.is_hurt and self.time >= self.boss_sprite.hurt_end_time and not self.boss_death_active:
                self.boss_sprite.reset_anim()
            if self.boss_sprite.health <= 0 and not self.boss_defeated:
                self.start_boss_defeat_sequence()
        
        # Call update on all sprites
        self.boss_list.update()
        if self.boss_death_active or not self.boss_fade_started:
            self.boss_list.update_animation()
        self.obstacle_list.update()
        self.ground_spike_list.update()
        self.stone_list.update()
        self.thrown_stone_list.update()
        self.player_list.update()
        if not self.player_anim_stopped:
            self.player_list.update_animation()
        if self.game_on:
            self.physics_engine.update()
        else:
            return
        
        # Horizontal movement disabled until boss is defeated
        if self.boss_defeated:
            if self.left_pressed and not self.right_pressed:
                self.player_sprite.change_x = -MOVE_SPEED
            elif self.right_pressed and not self.left_pressed:
                self.player_sprite.change_x = MOVE_SPEED
            else:
                self.player_sprite.change_x = 0
        else:
            self.player_sprite.change_x = 0

        on_ground = self.physics_engine.can_jump()
        if on_ground and not self.was_on_ground:
            self.jump_sound_ready = True
        if on_ground:
            if self.jetpack_fuel < 100:
                self.jetpack_fuel += 2
            if self.jump_pressed:
                self.player_sprite.change_y = JUMP_SPEED
                self._play_jump_sound()
            # Disable jetpack particles when on ground
            self.jetpack_particle_run = False
        else:
            if self.jump_pressed and self.jetpack_fuel > 0:
                if self.player_sprite.change_y < 0:
                    self.player_sprite.change_y = 0
                self.player_sprite.change_y += JETPACK_SPEED
                self.jetpack_fuel -= 0.5
                # Enable jetpack particles
                if not self.jetpack_particle_run:
                    self.jetpack_particle_run = True
                    self.jetpack_time_offset = self.time
                # Update particle position (below player sprite) continuously
                screen_x = self.player_sprite.center_x - self.camera_target_x
                screen_y = self.player_sprite.center_y - CAMERA_OFFSET_Y - 10  # Offset below player
                try:
                    self.jetpack_shadertoy.program['pos'] = (screen_x, screen_y)
                    self.jetpack_shadertoy.program['timeOffset'] = self.jetpack_time_offset
                    self.jetpack_shadertoy.program['direction'] = self.player_sprite.change_x * -0.3
                except Exception:
                    pass
            else:
                # Disable jetpack particles when not active
                self.jetpack_particle_run = False
        if self.player_sprite.change_y > 3:
            self.player_sprite.change_y = 3
        self.was_on_ground = on_ground

        if self.jetpack_particle_run:
            self._start_jetpack_sound()
        else:
            self._stop_jetpack_sound()

        # Keep player animation running to the right
        if not self.player_anim_stopped:
            self.set_anim(384)

        # out of limit, death
        if self.player_sprite.center_y < 0:
            self.reset()

        if not self.game_on:
            return
        
        # check obstacle collisions
        obstacle_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.obstacle_list)
        if obstacle_hit_list:
            self.reset()
        
        # check ground spike collisions
        ground_spike_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.ground_spike_list)
        if ground_spike_hit_list:
            self.reset()
        
        # Scroll the screen to the player
        self.scroll_to_player()

    def trigger_particle_explosion(self, world_x: float, world_y: float):
        """
        Trigger particle explosion at the given world coordinates
        """
        # Convert world position to screen (camera) coordinates so shader lines up with what the player sees.
        screen_x = world_x - self.camera_target_x
        screen_y = world_y - CAMERA_OFFSET_Y
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
        self.was_on_ground = False
        self.jump_sound_ready = True
        self._stop_jetpack_sound()
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
        self.jetpack_fuel = 100
        self.player_sprite.center_x = START_POS[0]
        self.player_sprite.center_y = START_POS[1]
        self.boss_sprite.center_x = 100
        self.boss_sprite.center_y = 210
        self.camera_target_x = 0
        self.scroll_speed = 2.0
        self.obstacle_spawn_timer = 0.0
        self.ground_spike_spawn_timer = 0.0
        self.obstacle_list.clear()
        self.ground_spike_list.clear()
        self.stone_list.clear()
        self.thrown_stone_list.clear()
        self.boss_sprite.health = 100
        self.boss_sprite.reset_anim()
        self.boss_sprite.alpha = 255
        self.stone_inventory = 0
        self.player_list.visible = True
        self.boss_defeated = False
        self.boss_fade_started = False
        self.player_anim_stopped = False
        self.fade_active = False
        self.fade_alpha = 0
        self.post_boss_cleared = False

    
    def game_over(self):
        """ game over animation"""
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self._stop_jetpack_sound()
        self.shake_camera()
    
    def start_boss_defeat_sequence(self):
        """Stop spawns, play death animation, then fade to end screen."""
        self.boss_defeated = True
        self.boss_death_active = True
        self.boss_death_start_time = self.time
        self.boss_sprite.set_death_anim()
        self.boss_sprite.is_hurt = False
        self.boss_sprite.hurt_end_time = 0.0
        if not self.post_boss_cleared:
            self.obstacle_list.clear()
            self.ground_spike_list.clear()
            self.stone_list.clear()
            self.thrown_stone_list.clear()
            self.post_boss_cleared = True
    
    def handle_boss_fade_and_idle(self):
        """Freeze player animation and advance boss death sequence."""
        if not self.player_anim_stopped:
            self.player_anim_stopped = True
            self.clear_anim(0, 384)
        if self.boss_death_active and self.time - self.boss_death_start_time >= self.boss_death_duration:
            self.boss_death_active = False
            self.boss_fade_started = True
            self.fade_active = True
    
    def update_end_fade(self):
        """Fade to black, then show end screen."""
        self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
        if self.fade_alpha >= 255:
            self.level_complete()


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
        """
        self.camera_sprites.move_to(Vec2(self.camera_target_x, 0), 0.2)


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
        self.shake_camera()
        elapsed = time.time() - self.level_start_time
        attempts = self.death + 1
        end_view = EndScreen(self.window, "Level 6 Complete", elapsed, attempts, self.__class__, None)
        self.window.show_view(end_view)


    def spawn_obstacle(self):
        """Spawn an obstacle at random position and angle"""
        obstacle_types = [
            ("data/sprites/bombline.png", 1.0),
            ("data/sprites/lightning_32x32.png", 1.0),
            ("data/sprites/lightning_32x64.png", 1.0),
            ("data/sprites/spike.png", 0.5)
        ]
        
        sprite_path, scale = random.choice(obstacle_types)
        obstacle = arcade.Sprite(sprite_path, scale=scale, hit_box_algorithm="Detailed")
        
        spawn_x = self.player_sprite.center_x + SCREEN_WIDTH + random.uniform(0, 200)
        spawn_y = random.uniform(100, SCREEN_HEIGHT - 100)
        
        obstacle.center_x = spawn_x
        obstacle.center_y = spawn_y
        obstacle.angle = random.uniform(0, 360)
        
        self.obstacle_list.append(obstacle)
    
    def spawn_ground_spike(self):
        """spawn 1-4 ground spikes in a row"""
        num_spikes = random.randint(1, 4)
        base_spawn_x = self.player_sprite.center_x + SCREEN_WIDTH + 100
        
        for i in range(num_spikes):
            spawn_x = base_spawn_x + (i * 38)
            ground_spike = arcade.Sprite("data/sprites/ground_spike.png", scale=0.5, hit_box_algorithm="Detailed")
            ground_spike.center_x = spawn_x
            ground_spike.center_y = 108
            self.ground_spike_list.append(ground_spike)
    
    def draw_fuel_bar(self):
        x = int(self.player_sprite.center_x - 18)
        y = int(self.player_sprite.center_y)
        arcade.draw_xywh_rectangle_filled(x-3, y-25, 6, self.jetpack_fuel / 2, (255, 98, 0))
        arcade.draw_rectangle_outline(x, y, 6, 50, (0, 0, 0))
    
    def draw_boss_health_bar(self):
        """Draw health bar above BOSS"""
        bar_width = 120
        bar_height = 12
        bar_x = self.boss_sprite.center_x
        bar_y = self.boss_sprite.center_y + 140
        alpha = self.boss_sprite.alpha
        
        # Draw background (red)
        arcade.draw_rectangle_filled(bar_x, bar_y, bar_width, bar_height, (200, 0, 0, alpha))
        
        # Draw health (green)
        health_ratio = self.boss_sprite.health / self.boss_sprite.max_health
        health_width = bar_width * health_ratio
        if health_width > 0:
            arcade.draw_rectangle_filled(bar_x - (bar_width - health_width) / 2, bar_y, health_width, bar_height, (0, 200, 0, alpha))
        
        # Draw border
        arcade.draw_rectangle_outline(bar_x, bar_y, bar_width, bar_height, (0, 0, 0, alpha), 2)
    
    def draw_trajectory_arrow(self):
        """Draw trajectory arrow when player has stones"""
        COLOR = (120, 13, 13)
        if self.stone_inventory > 0:
            # Get world coordinates of mouse
            world_mouse_x = self.mouse_x + self.camera_target_x
            world_mouse_y = self.mouse_y + CAMERA_OFFSET_Y
            
            # Player position
            player_x = self.player_sprite.center_x
            player_y = self.player_sprite.center_y
            
            # Calculate direction
            dx = world_mouse_x - player_x
            dy = world_mouse_y - player_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                # Normalize direction
                dir_x = dx / distance
                dir_y = dy / distance
                
                # Arrow length
                arrow_length = 50
                arrow_end_x = player_x + dir_x * arrow_length
                arrow_end_y = player_y + dir_y * arrow_length
                
                # Draw arrow line
                arcade.draw_line(player_x, player_y, arrow_end_x, arrow_end_y, COLOR, 3)
                
                # Draw arrowhead
                angle = math.atan2(dir_y, dir_x)
                arrowhead_size = 10
                arrowhead_x1 = arrow_end_x - arrowhead_size * math.cos(angle - 0.5)
                arrowhead_y1 = arrow_end_y - arrowhead_size * math.sin(angle - 0.5)
                arrowhead_x2 = arrow_end_x - arrowhead_size * math.cos(angle + 0.5)
                arrowhead_y2 = arrow_end_y - arrowhead_size * math.sin(angle + 0.5)
                arcade.draw_triangle_filled(arrow_end_x, arrow_end_y, arrowhead_x1, arrowhead_y1, arrowhead_x2, arrowhead_y2, COLOR)

    def draw_stone_ui(self):
        """Draw stone count in the bottom-right corner."""
        if not self.stone_icon_texture:
            return

        padding = 40
        icon_scale = 0.25
        icon_width = self.stone_icon_texture.width * icon_scale
        icon_height = self.stone_icon_texture.height * icon_scale
        icon_center_x = padding + (icon_width / 2)
        icon_center_y = padding + (icon_height / 2)

        arcade.draw_texture_rectangle(
            icon_center_x,
            icon_center_y,
            icon_width,
            icon_height,
            self.stone_icon_texture,
        )
        arcade.draw_text(
            f"x {self.stone_inventory}",
            icon_center_x + (icon_width / 2) + 8,
            icon_center_y - 12,
            color=(0, 0, 0),
            font_size=22,
            anchor_x="left",
        )
    
    def spawn_stone(self):
        """Spawn a stone at random position"""
        stone = Stone(
            center_x=self.player_sprite.center_x + SCREEN_WIDTH + random.uniform(0, 200),
            center_y=random.uniform(120, SCREEN_HEIGHT - 100),
            scale=0.25
        )
        self.stone_list.append(stone)
    
    def throw_stone(self, mouse_x, mouse_y):
        """Throw a stone towards mouse position"""
        if self.stone_inventory <= 0:
            return
        
        # Convert screen mouse coordinates to world coordinates
        world_mouse_x = mouse_x + self.camera_target_x
        world_mouse_y = mouse_y + CAMERA_OFFSET_Y
        
        # Player position
        player_x = self.player_sprite.center_x
        player_y = self.player_sprite.center_y
        
        # Calculate direction and velocity
        dx = world_mouse_x - player_x
        dy = world_mouse_y - player_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Normalize direction
            dir_x = dx / distance
            dir_y = dy / distance
            
            # Throw velocity (adjust speed as needed)
            throw_speed = 8.0
            v_x = dir_x * throw_speed
            v_y = dir_y * throw_speed
            
            # Create thrown stone
            thrown_stone = ThrownStone(player_x, player_y, v_x, v_y)
            self.thrown_stone_list.append(thrown_stone)
            
            # Remove one stone from inventory
            self.stone_inventory -= 1

def main():
    """ main method """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "level 6", vsync=True)
    arcade.enable_timings()
    window.show_view(Level6(window))
    arcade.run()

if __name__ == "__main__":
    main()
