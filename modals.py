import arcade


class MovingWall():
    """ moving wall class """

    def __init__(self, wall_sprites, move_speed, move_distance, move_direction='vertical'):
        """ initializer """
        self.wall_list = wall_sprites
        self.original_positions = [(wall.center_x, wall.center_y) for wall in wall_sprites]
        self.org_move_speed = move_speed
        self.move_speed = move_speed
        self.move_distance = move_distance
        self.move_direction = move_direction  # 'vertical' or 'horizontal'
        self.moved_distance = 0
        self.triggered = False
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
        self.can_be_touched = True
    
    def start_moving_down(self):
        """ should be called when game ends """
        self.is_moving = True
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
                self.pos_x = 250
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
    
