# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
'''
Mukkuru module for manual game imports and game properties\n
This module does not import other Mukkuru modules (besides core)\n
'''
#import os
import uuid
import json
from functools import lru_cache
from pathlib import Path
#from typing import Any
from utils.core import mukkuru_env, backend_log

@lru_cache(maxsize=1)
def _get_game_config():
    ''' Reads game configuration '''
    config_path = mukkuru_env["LibraryConfig"]
    if not Path(config_path).exists():
        return {}
    with open(config_path, encoding='utf-8') as f:
        game_config = json.load(f)
    return game_config

def _update_game_config(game_config: dict) -> None:
    ''' update user configuration '''
    current_game_config = _get_game_config()
    if game_config.get("Stamp", None) != current_game_config.get("Stamp", None):
        backend_log("stamp mismatch, refusing game config update", parent=True)
        return
    backend_log("updating game config....", parent=True)
    _get_game_config.cache_clear()
    game_config["Stamp"] = str(uuid.uuid4())
    with open(mukkuru_env['LibraryConfig'] , 'w', encoding='utf-8') as f:
        json.dump(game_config, f)

def get_title_config(appid: str) -> dict:
    ''' returns the configuration of a particular game '''
    game_config = _get_game_config()
    if appid not in game_config:
        return {}
    return game_config[appid]

def set_title_config(appid: str, config:dict):
    ''' updates the configuration for a particular game '''
    game_config = _get_game_config()
    game_config[appid] = config
    _update_game_config(game_config)
