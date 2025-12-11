import arcade


class MovingWall():
    """ moving wall class """

    def __init__(self, wall_sprites, move_speed, move_distance, move_direction='vertical', move_with_player=False, player_sprite=None):
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
            self.is_moving = False
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
        if player_colliding and self.player_sprite is not None:
            if self.move_direction == 'vertical':
                # Move player vertically with the wall
                self.player_sprite.center_y -= delta
            else:
                # Move player horizontally with the wall
                self.player_sprite.center_x -= delta

        self.moved_distance += abs(delta)

        # stop when we've moved the target distance
        if self.moved_distance >= self.move_distance:
            self.is_moving = False

    def start_moving(self):
        """Start wall movement."""
        self.is_moving = True
        self.triggered = True

    def reset(self):
        """Reset wall positions to original locations."""
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
    def __init__(self, pos_x, pos_y, flipped_diagonally = True):
        """ initializer """
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.triggered = False
        self.sprite_list = arcade.SpriteList()
        self.sprite1 = arcade.Sprite("data/sprites/button1.png", scale=0.25, center_x=pos_x, center_y=pos_y, flipped_diagonally=flipped_diagonally)
        self.sprite2 = arcade.Sprite("data/sprites/button2.png", scale=0.25, center_x=pos_x, center_y=pos_y, flipped_diagonally=flipped_diagonally)
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
        self.sprite = arcade.Sprite("data/sprites/fireball.png", scale=0.4, center_x=pos_x, center_y=pos_y)
        self.sprite.set_hit_box([(-28, -28), (0, -42), (28, -28), (42, 0), (28, 28), (0, 42), (-28, 28), (-42, 0)])
    
    def draw(self):
        self.sprite.draw()
        # self.sprite.draw_hit_box()

    def update(self, gravity):
        if self.pos_y + self.v_y <= self.boundary:
            self.v_y *= -1
        else:
            self.v_y -= gravity
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