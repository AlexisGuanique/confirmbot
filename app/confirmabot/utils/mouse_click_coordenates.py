import pyautogui
import keyboard
import time

def get_mouse_coordinate_on_keypress(key="c"):
    while True:
        if keyboard.is_pressed(key):
            x, y = pyautogui.position()
            return f"{x}x{y}"
        time.sleep(0.1)