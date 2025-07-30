# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Mukkuru module with essential functions and constants '''
import os
from functools import lru_cache
from pathlib import Path
import sys
import time
import json
import platform

# Constants
mukkuru_env = {}
COMPILER_FLAG = getattr(sys, 'frozen', False) or "__compiled__" in globals()
APP_VERSION = "0.3.12"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PORT = 49347
SERVER_PORT = 49351
FRONTEND_MODE = "PYWEBVIEW"

if platform.system() == "Windows":
    pass
elif platform.system() == "Darwin":
    FRONTEND_MODE = "PYWEBVIEW"
else:
    FRONTEND_MODE = "FLASKUI"

@lru_cache(maxsize=1)
def app_version():
    ''' app name + version '''
    return f"Mukkuru v{APP_VERSION}"

# Logging
def backend_log(message) -> None:
    ''' print message and save to file '''
    print(message)
    if "log" in mukkuru_env:
        os.makedirs(os.path.dirname(mukkuru_env["log"]), exist_ok=True)
        with open(mukkuru_env["log"], 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
# Config
@lru_cache(maxsize=1)
def get_config() -> dict:
    ''' get user configuration'''
    user_config = {
            "loop" : False,
            "skipNoArt" : False,
            "displayBatteryPercent" : False,
            "maxGamesInHomeScreen" : 12,
            "enableServer" : False,
            "autoPlayMedia" : False,
            "videoSources" : [os.path.join(mukkuru_env["root"], "video")],
            "musicSources" : [os.path.join(mukkuru_env["root"], "music")],
            "pictureSources" : [os.path.join(mukkuru_env["root"], "pictures")],
            "saveScreenshot" : 0,
            "useAllVideoSources" : False,
            "protonConfig" : {},
            "useAlternativeImage" : { "1149550" : 1 },
            "librarySource" : 3,
            "darkMode" : False,
            "startupGameScan" : False,
            "safeMode" : False,
            "12H" : True,
            "fullScreen" : False,
            "language" : "EN",
            "blacklist" : [],
            "favorite" : [],
            "recentPlayed" : [],
            "showKeyGuide" : True,
            "theme" : "Switch 2",
            "cores" : 6,
            "alwaysShowBottomBar" : True,
            "uiSounds" : "original",
            "gameProperties" : {},
            "boxartBlacklist" : [],
            "logoBlacklist" : [],
            "heroBlacklist" : [],
            "configVersion" : APP_VERSION,
            "adultContent" : False,
            "repos" : [ "https://repo.panyolsoft.com/" ],
            "patches" : [ ],
            "sgdb_key" : "",
        }

    while "config.json" not in mukkuru_env:
        time.sleep(0.1)

    if not Path(mukkuru_env["config.json"]).is_file():
        backend_log("No config.json")
        with open(mukkuru_env["config.json"], 'w', encoding='utf-8') as f:
            json.dump(user_config, f)
    with open(mukkuru_env["config.json"], encoding='utf-8') as f:
        configuration = json.load(f)
        for key, value in user_config.items():
            if key not in configuration:
                configuration[key] = value
            user_config = configuration
    return user_config

def update_config(user_config) -> None:
    ''' update user configuration '''
    # clear cached config as the value was updated
    get_config.cache_clear()
    with open(mukkuru_env['config.json'] , 'w', encoding='utf-8') as f:
        json.dump(user_config, f)

def set_alive_status(value) -> None:
    ''' set alive status, this will be periodically read from frontend '''
    mukkuru_env["alive"] = value

#def add_alive_command(value):
#    ''' adds a command to alive status '''
#    mukkuru_env["alive"]["commands"]

def format_executable(executable) -> str:
    ''' appends .exe if Windows, otherwise return parameter as-is '''
    if platform.system() == "Windows":
        executable = f"{executable}.exe"
    return executable

def sanitized_env() -> dict:
    ''' get a environment copy free of bundled libs references '''
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env

def is_bsd() -> bool:
    ''' returns whether os is a FreeBSD fork '''
    return "BSD" in platform.system() or platform.system() == "DragonFly"
