import arcade
import math


class MovingWall():
    """ moving wall class """

    def __init__(self, wall_sprites: arcade.SpriteList, move_speed: int, move_distance: int, move_direction='vertical', move_with_player=False, player_sprite=None, disappears=False, visible=True):
        """
        initializer
        move direction default is left and down.
        move_direction = 'vertical' or 'horizontal'
        """
        self.wall_list = wall_sprites
        self.original_positions = [(wall.center_x, wall.center_y) for wall in wall_sprites]
        self.org_move_speed = move_speed
        self.move_speed = move_speed
        self.move_distance = move_distance
        self.move_direction = move_direction  # 'vertical' or 'horizontal'
        self.moved_distance = 0
        self.triggered = False
        self.is_moving = False
        self.move_with_player = move_with_player
        self.player_sprite = player_sprite
        self.disappears = disappears
        self.visible = visible
        self.wall_list.visible = self.visible
        self.player_on_platform = False

    def _check_player_collision(self):
        """Check if player sprite is colliding with any wall sprite using bounding boxes."""
        if self.player_sprite is None:
            return False
        
        player_left = self.player_sprite.left
        player_right = self.player_sprite.right
        player_bottom = self.player_sprite.bottom
        player_top = self.player_sprite.top
        
        for wall_sprite in self.wall_list:
            wall_left = wall_sprite.left
            wall_right = wall_sprite.right
            wall_bottom = wall_sprite.bottom
            wall_top = wall_sprite.top
            
            # Check if bounding boxes overlap
            if (player_right > wall_left and player_left < wall_right and
                player_top > wall_bottom and player_bottom < wall_top + 2):
                return True
        
        return False

    def update(self):
        """Move wall sprites at a constant speed until moved target distance.
        
        If player_sprite is provided and colliding with the wall, the player
        will move with the wall.
        """
        if not self.is_moving or not self.wall_list:
            return

        # remaining distance to move
        remaining = self.move_distance - self.moved_distance
        if remaining <= 0:
            self.finish_moving()
            return

        # move by the smaller of the speed or remaining distance to avoid overshoot
        delta = min(self.move_speed, remaining)

        # Check for player collision before moving the wall using manual bounding box check
        player_colliding = self._check_player_collision() if self.move_with_player and self.is_moving else False

        for sprite in self.wall_list:
            if self.move_direction == 'vertical':
                sprite.center_y -= delta
            else:
                sprite.center_x -= delta

        # Move the player with the wall if colliding
        self.player_on_platform = False
        if player_colliding and self.player_sprite is not None:
            self.player_on_platform = True
            # if self.move_direction == 'vertical':
            #     # Move player vertically with the wall
            #     self.player_sprite.center_y -= delta
            # else:
            #     # Move player horizontally with the wall
            #     self.player_sprite.center_x -= delta

        self.moved_distance += abs(delta)

        # stop when we've moved the target distance
        if self.moved_distance >= self.move_distance:
            self.finish_moving()
            

    def start_moving(self):
        """Start wall movement."""
        self.is_moving = True
        self.triggered = True
        self.wall_list.visible = True
    
    def finish_moving(self):
        self.is_moving = False
        self.player_on_platform = False
        if self.disappears:
            self.wall_list.visible = False
            for sprite in self.wall_list:
                # move it far far away so it "disappears"
                sprite.center_x = 100000
                sprite.center_y = 100000

    def reset(self):
        """Reset wall positions to original locations."""
        self.wall_list.visible = self.visible
        self.player_on_platform = False
        self.triggered = False
        self.moved_distance = 0
        self.is_moving = False
        self.move_speed = self.org_move_speed
        for i, wall in enumerate(self.wall_list):
            wall.center_x, wall.center_y = self.original_positions[i]


class Door():
    """ door class """
    def __init__(self, x, y):
        """ initializer """
        self.init_x = x
        self.init_y = y
        self.pos_x = x
        self.pos_y = y
        self.height = 45
        self.width = 30
        self.opacity = 255
        self.can_be_touched = True

        self.move_speed = 1
        self.move_distance = 60
        self.moved = 0
        self.is_moving = False
        self.move_over = True
        self.move_direction = None  # 'down' or 'right' to track which direction
    
    def draw(self):
        """ draws the door """
        arcade.draw_rectangle_filled(self.pos_x, self.pos_y, self.width + 10, self.height + 10, (64, 22, 0, self.opacity))
        arcade.draw_rectangle_filled(self.pos_x, self.pos_y, self.width, self.height, (255, 255, 255, self.opacity))
    
    def check_collision(self, left, right, bottom):
        """ check the collision of the door w/ an object """
        if not self.can_be_touched:
            return False
        if abs(right - (self.pos_x - self.width / 2)) < 3 and bottom < self.pos_y + self.height / 2:
            return True
        if abs(left - (self.pos_x + self.width / 2)) < 3 and bottom < self.pos_y + self.height / 2:
            return True
        if right > self.pos_x - self.width / 2 and left < self.pos_x + self.width / 2 and bottom < self.pos_y + self.height / 2:
            return True
        return False
    
    def reset(self):
        """ resets the position """
        self.pos_x = self.init_x
        self.pos_y = self.init_y
        self.opacity = 255
        self.is_moving = False
        self.move_direction = None
        self.can_be_touched = True
    
    def start_moving_down(self):
        """ should be called when game ends """
        self.is_moving = True
        self.move_over = False
        self.move_direction = 'down'
        self.moved = 0
        self.move_speed = 1
        self.move_distance = 60

        
    def start_moving_right(self, move_speed, move_distance):
        """ start right movement and fade out """
        self.is_moving = True
        self.move_direction = 'right'
        self.moved = 0
        self.move_speed = move_speed
        self.move_distance = move_distance
        self.can_be_touched = False


    def update(self):
        """Unified update method. Call each frame from the game loop.

        Handles movement and fading depending on `move_direction`.
        """
        if not self.is_moving or self.move_direction is None:
            return

        remaining = self.move_distance - self.moved
        if remaining <= 0:
            # move is over
            if self.move_direction == 'down':
                # tell level is complete
                self.move_over = True

            elif self.move_direction == 'right':
                # appear back at spawn
                self.pos_x = 200
                self.pos_y = 180
                self.opacity = 255
                self.can_be_touched = True

            self.is_moving = False
            self.move_direction = None
            return

        delta = min(self.move_speed, remaining)

        if self.move_direction == 'down':
            self.pos_y -= delta
            self.moved += delta

        elif self.move_direction == 'right':
            self.pos_x += delta
            self.moved += delta
            # fade out as the door moves
            self.opacity = max(0, 255 * (1.0 - self.moved / self.move_distance))
    

class Button():
    def __init__(self, pos_x, pos_y, flipped_diagonally = True, flipped_vertically = False):
        """ initializer """
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.triggered = False
        self.sprite_list = arcade.SpriteList()
        self.sprite1 = arcade.Sprite("data/sprites/button1.png", scale=0.25, center_x=pos_x, center_y=pos_y,
         flipped_diagonally=flipped_diagonally, flipped_vertically=flipped_vertically)
        self.sprite2 = arcade.Sprite("data/sprites/button2.png", scale=0.25, center_x=pos_x, center_y=pos_y,
         flipped_diagonally=flipped_diagonally, flipped_vertically=flipped_vertically)
        self.sprite2.visible = False
        self.sprite_list.append(self.sprite1)
        self.sprite_list.append(self.sprite2)
    
    def draw(self):
        self.sprite_list.draw()
    
    def touched(self):
        self.triggered = True
        self.sprite1.visible = False
        self.sprite2.visible = True
    
    def reset(self):
        self.triggered = False
        self.sprite1.visible = True
        self.sprite2.visible = False
    

class FireBall():
    def __init__(self, pos_x, pos_y, boundary):
        """ initializer """
        self.init_x = pos_x
        self.init_y = pos_y
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.v_x = 0
        self.v_y = 0
        self.boundary = boundary
        self.sprite = arcade.Sprite("data/sprites/fireball.png", scale=1, center_x=pos_x, center_y=pos_y)
        # self.sprite.set_hit_box([(-28, -28), (0, -42), (28, -28), (42, 0), (28, 28), (0, 42), (-28, 28), (-42, 0)])
    
    def draw(self):
        self.sprite.draw()
        # self.sprite.draw_hit_box()

    def update(self, gravity):
        if self.pos_y + self.v_y <= self.boundary:
            self.v_y *= -1
        else:
            self.v_y -= (gravity * 0.6)
        self.pos_x += self.v_x
        self.pos_y += self.v_y
        self.sprite.center_x = self.pos_x
        self.sprite.center_y = self.pos_y
    
    def bounce(self):
        self.v_x *= -1
        self.v_y *= -1
    
    def reset(self):
        self.pos_x = self.init_x
        self.pos_y = self.init_y
        self.v_x = 0
        self.v_y = 0


class Missile():
    def __init__(self, pos_x: int, pos_y: int, player_sprite: arcade.AnimatedTimeBasedSprite):
        """ a missile class initializer"""
        self.sprite = arcade.Sprite("data/sprites/missile.png", 2)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.player_sprite = player_sprite
        self.speed = 3.0  # constant speed magnitude
        self.turn_rate = 0.3  # steering acceleration factor (how quickly it can turn)
        self.sprite.center_x = pos_x
        self.sprite.center_y = pos_y
        
        # Initialize velocity pointing right (positive x direction)
        self.v_x = self.speed
        self.v_y = 0
        
        # Update sprite rotation to match initial velocity
        self._update_rotation()
    
    def _update_rotation(self):
        """Update sprite rotation to match velocity direction"""
        angle = math.degrees(math.atan2(self.v_y, self.v_x))
        self.sprite.angle = angle - 90
    
    def draw(self):
        """Draw the missile sprite"""
        self.sprite.draw()
    
    def update(self):
        """Update missile position with realistic physics - gradual steering"""
        if self.player_sprite is None:
            # If no target, just move in current direction
            self.pos_x += self.v_x
            self.pos_y += self.v_y
            self.sprite.center_x = self.pos_x
            self.sprite.center_y = self.pos_y
            return
        
        # Calculate desired direction (toward player)
        dx = self.player_sprite.center_x - self.pos_x
        dy = self.player_sprite.center_y - self.pos_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        if distance > 0:
            # Normalize desired direction
            desired_dir_x = dx / distance
            desired_dir_y = dy / distance
            
            # Get current velocity direction (normalized)
            current_speed = (self.v_x ** 2 + self.v_y ** 2) ** 0.5
            if current_speed > 0:
                current_dir_x = self.v_x / current_speed
                current_dir_y = self.v_y / current_speed
            else:
                # If velocity is zero, use desired direction
                current_dir_x = desired_dir_x
                current_dir_y = desired_dir_y
            
            # Calculate steering direction (perpendicular to current velocity)
            # The steering force is the component of desired direction perpendicular to current velocity
            # Dot product to find parallel component
            dot_product = desired_dir_x * current_dir_x + desired_dir_y * current_dir_y
            
            # Perpendicular component = desired - parallel
            # parallel = current_dir * dot_product
            parallel_x = current_dir_x * dot_product
            parallel_y = current_dir_y * dot_product
            
            # Steering direction (perpendicular to velocity)
            steer_x = desired_dir_x - parallel_x
            steer_y = desired_dir_y - parallel_y
            
            # Normalize steering vector
            steer_length = (steer_x ** 2 + steer_y ** 2) ** 0.5
            if steer_length > 0:
                steer_x /= steer_length
                steer_y /= steer_length
            
            # Apply steering acceleration (limited by turn_rate)
            self.v_x += steer_x * self.turn_rate
            self.v_y += steer_y * self.turn_rate
            
            # Maintain constant speed by normalizing velocity
            current_speed_after = (self.v_x ** 2 + self.v_y ** 2) ** 0.5
            if current_speed_after > 0:
                self.v_x = (self.v_x / current_speed_after) * self.speed
                self.v_y = (self.v_y / current_speed_after) * self.speed
        
        # Update position based on velocity
        self.pos_x += self.v_x
        self.pos_y += self.v_y
        self.sprite.center_x = self.pos_x
        self.sprite.center_y = self.pos_y
        
        # Update rotation to match velocity direction
        self._update_rotation()