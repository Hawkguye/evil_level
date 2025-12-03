import arcade
import arcade.gui

from level1 import Level1
from level2 import Level2

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600


class MenuView(arcade.View):
    """ Menu View """
    def __init__(self, window):
        super().__init__(window)
        arcade.set_background_color((255, 255, 255))
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.v_box = arcade.gui.UIBoxLayout()

        level1_button = arcade.gui.UIFlatButton(text="Level 1", width=200)
        self.v_box.add(level1_button.with_space_around(bottom=20))
        level1_button.on_click = self.start_level1

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def start_level1(self):
        level1_view = Level1()
        self.window.show_view(level1_view)

    def on_show_view(self):
        arcade.set_background_color((255, 255, 255))
    
    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
        arcade.draw_text("Evil Level", 500, 500, (0, 0, 0), 32, anchor_x="center")
        

class GameWindow(arcade.Window):
    """ Main Game Window """

    def __init__(self):
        """ initializer """
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Evil Level", vsync=True)
        self.set_location(50, 50)
        self.menu_view = MenuView(self)
        
    def setup(self):
        self.show_view(self.menu_view)

def main():
    """ main method """
    window = GameWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()