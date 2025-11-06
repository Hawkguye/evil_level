from pynput import keyboard
from pynput.keyboard import Key, Controller

# Create a keyboard controller to send key events
kbd = Controller()

# Mapping: key to press -> key to simulate
KEY_MAP = {
    'a': Key.left,
    's': Key.down,
    'd': Key.up,
    'f': Key.right
}

# Track which keys are currently pressed to avoid repeats
pressed_keys = set()

def on_press(key):
    try:
        # Get the character of the key pressed
        key_char = key.char if hasattr(key, 'char') else None
        
        # Check if this key is in our mapping and not already pressed
        if key_char in KEY_MAP and key_char not in pressed_keys:
            pressed_keys.add(key_char)
            # Press the corresponding arrow key
            kbd.press(KEY_MAP[key_char])
    except AttributeError:
        pass

def on_release(key):
    try:
        # Get the character of the key released
        key_char = key.char if hasattr(key, 'char') else None
        
        # Check if this key is in our mapping
        if key_char in KEY_MAP and key_char in pressed_keys:
            pressed_keys.remove(key_char)
            # Release the corresponding arrow key
            kbd.release(KEY_MAP[key_char])
        
        # Stop listener on ESC key
        if key == Key.esc:
            print("\nStopping key remapper...")
            return False
    except AttributeError:
        pass

# Start listening to keyboard events
print("Key remapper started!")
print("Mappings:")
print("  A -> Left Arrow")
print("  S -> Down Arrow")
print("  D -> Up Arrow")
print("  F -> Right Arrow")
print("\nPress ESC to stop the remapper.")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()