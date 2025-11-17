# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
'''
Mukkuru module with essential functions and constants.\n
This module should NOT import other Mukkuru modules (with the exception of database).\n
'''
import os
import traceback
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any
import sys
import time
import json
import platform
import inspect
import unicodedata
import re

import utils.database as db
from utils.model import Config

# Constants
mukkuru_env = {}
COMPILER_FLAG = getattr(sys, 'frozen', False) or "__compiled__" in globals()
APP_VERSION = "0.4.0"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PORT: int = 49347
SERVER_PORT: int = 49351
PASSTHROUGH_PORT: int = 49453# 49454, 49455 will also be used when opening more games
AVAILABLE_P_PORTS: int = 4
FRONTEND_MODE: str = "PYWEBVIEW"
DEBUG = True

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
def backend_log(message: str, parent = False) -> None:
    ''' print message and save to file
    :param str message: Message to print\n
    :param bool parent: logs caller filename/line\n'''
    stack = inspect.stack()
    frame = stack[1]
    if parent:
        frame = stack[2]
    lineno = frame.lineno
    filename = os.path.basename(frame.filename)
    if "[frontend]" not in message:
        message = f"[{filename}:{lineno}] {message}"
    if not COMPILER_FLAG:
        print(message.encode("utf-8", errors="replace").decode("utf-8"))
    if "log" in mukkuru_env:
        os.makedirs(os.path.dirname(mukkuru_env["log"]), exist_ok=True)
        with open(mukkuru_env["log"], 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")

def log_uncaught_exceptions(exc_type, exc_value, exc_tb):
    ''' handler for traceback hook '''
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    backend_log(tb_str, True)

def thread_exception_handler(args):
    ''' Handler for thread traceback hook '''
    tb_str = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    backend_log(f"Thread {args.thread.name}:\n" + tb_str, parent=True)

# Config
@lru_cache(maxsize=1)
def get_config() -> dict:
    ''' get user configuration'''
    user_config = {
            "loop" : False,
            "skipNoArt" : False,
            "skipDuplicated" : True,
            "displayBatteryPercent" : False,
            "displayCursor" : True,
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
            "theme" : "JoyView 2",
            "cores" : 6,
            "alwaysShowBottomBar" : True,
            "uiSounds" : "original",
            "gameProperties" : {},
            "boxartBlacklist" : [],
            "logoBlacklist" : [],
            "heroBlacklist" : [],
            "losslessScaling" : [],
            "configVersion" : APP_VERSION,
            "adultContent" : False,
            "addedToStartup" : False,
            "repos" : [ "https://repo.panyolsoft.com/" ],
            "patches" : [ ],
            "sgdb_key" : "",
        }
    session = db.get_session()
    cfg: Config = session.query(Config).first()

    if not cfg:
        cfg = Config(config=user_config)
        session.add(cfg)
        session.commit()
    configuration = cfg.config
    for key, value in user_config.items():
        if key not in configuration:
            backend_log(f"creating configuration key {key}")
            configuration[key] = value
        user_config = configuration
    session.close()
    return user_config

def update_config(user_config: dict) -> None:
    ''' update user configuration '''
    session = db.get_session()
    backend_log("updating config....", parent=True)
    cfg: Config = session.query(Config).first()
    cfg.config = user_config
    session.commit()
    session.close()
    # clear cached config as the value was updated
    get_config.cache_clear()

def set_alive_status(value) -> None:
    ''' set alive status, this will be periodically read from frontend '''
    mukkuru_env["alive"] = value

#def add_alive_command(value):
#    ''' adds a command to alive status '''
#    mukkuru_env["alive"]["commands"]

def format_executable(executable: str) -> str:
    ''' appends .exe if Windows, otherwise return parameter as-is '''
    if platform.system() == "Windows":
        executable = f"{executable}.exe"
    return executable

def sanitized_env() -> dict:
    '''
    Returns a sanitized copy of os.environ\n
    This is necessary when using PyInstaller, since default environment
    can cause external executable calls to look for system libs inside
    this app directory\n
    :returns: a os.environ copy without LD_LIBRARY_PATH, PYTHONHOME and PYTHONPATH
    '''
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env

def get_paths_from_extensions(path: str, extensions: list) -> list:
    ''' returns a list of paths from given extensions '''
    paths: list  = []
    for extension in extensions:
        paths.append(f'{path}.{extension}')
    return paths

def normalize_text(text: str, remove_symbols: bool = False) -> str:
    ''' removes all special characters
    :param str text: text to normalize\n
    :param bool remove_symbols: keep only letters, numbers, underscores, and spaces.\n'''
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    if remove_symbols:
        text = re.sub(r"[^\w\s]", "", text)
    text = text.rstrip()
    return text

def is_bsd() -> bool:
    ''' returns whether os is a FreeBSD fork '''
    return "BSD" in platform.system() or platform.system() == "DragonFly"

def ternary(condition: bool, var1: Any, var2: Any) -> Any:
    ''' returns var1 if condition evaluates True, else return var2'''
    return var1 if condition else var2

sys.excepthook = log_uncaught_exceptions
threading.excepthook = thread_exception_handler
