''' (Windows) Sends key presses '''
import ctypes
import time

VK_RETURN = 0x0D
VK_CONTROL = 0x11 # CTRL key
VK_MENU = 0x12  # ALT key
VK_S = 0x53 # S Key

KEYEVENTF_KEYUP = 0x0002

def press_key(hex_key_code):
    ''' press a key '''
    ctypes.windll.user32.keybd_event(hex_key_code, 0, 0, 0)

def release_key(hex_key_code):
    ''' release a key '''
    ctypes.windll.user32.keybd_event(hex_key_code, 0, KEYEVENTF_KEYUP, 0)

def send_ctrl_alt_s():
    ''' Sends CTRL+ALT+S '''
    press_key(VK_CONTROL)
    press_key(VK_MENU)
    press_key(VK_S)
    time.sleep(0.1)
    release_key(VK_CONTROL)
    release_key(VK_MENU)
    release_key(VK_S)

def send_alt_enter():
    ''' Sends ALT+ENTER '''
    press_key(VK_MENU)
    press_key(VK_RETURN)
    time.sleep(0.1)
    release_key(VK_MENU)
    release_key(VK_RETURN)
