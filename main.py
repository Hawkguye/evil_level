import arcade
import arcade.gui
import time

from level1 import Level1
from level2 import Level2
from level3 import Level3
from level4 import Level4
from level5 import Level5

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600


class MenuView(arcade.View):
    """ Menu View """
    def __init__(self, window):
        super().__init__(window)
        self.is_loading = False
        arcade.set_background_color((255, 255, 255))
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.v_box = arcade.gui.UIBoxLayout()

        level1_button = arcade.gui.UIFlatButton(text="Level 1", width=200)
        self.v_box.add(level1_button.with_space_around(bottom=20))
        level1_button.on_click = self.start_level1

        
        level2_button = arcade.gui.UIFlatButton(text="Level 2", width=200)
        self.v_box.add(level2_button.with_space_around(bottom=20))
        level2_button.on_click = self.start_level2

        level3_button = arcade.gui.UIFlatButton(text="Level 3", width=200)
        self.v_box.add(level3_button.with_space_around(bottom=20))
        level3_button.on_click = self.start_level3

        level4_button = arcade.gui.UIFlatButton(text="Level 4", width=200)
        self.v_box.add(level4_button.with_space_around(bottom=20))
        level4_button.on_click = self.start_level4

        level5_button = arcade.gui.UIFlatButton(text="Level 5", width=200)
        self.v_box.add(level5_button.with_space_around(bottom=20))
        level5_button.on_click = self.start_level5

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def start_level1(self, event):
        level1_view = Level1(self.window)
        self.window.show_view(level1_view)
    
    def start_level2(self, event):
        level2_view = Level2(self.window)
        self.window.show_view(level2_view)

    def start_level3(self, event):
        level3_view = Level3(self.window)
        self.window.show_view(level3_view)
    
    def start_level4(self, event):
        level4_view = Level4(self.window)
        self.window.show_view(level4_view)

    def start_level5(self, event):
        level5_view = Level5(self.window)
        self.window.show_view(level5_view)

    def on_show_view(self):
        arcade.set_background_color((255, 255, 255))
    
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
        arcade.draw_text("Evil Level", 500, 500, (0, 0, 0), 32, anchor_x="center")
        if self.is_loading:
            arcade.draw_text("loading level...", 500, 100, (0, 0, 0), 32, anchor_x="center")
        

class GameWindow(arcade.Window):
    """ Main Game Window """

    def __init__(self):
        """ initializer """
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Evil Level", vsync=True)
        self.set_location(50, 50)
        self.menu_view = MenuView(self)
        arcade.enable_timings()

    def setup(self):
        self.show_view(self.menu_view)

def main():
    """ main method """
    window = GameWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()