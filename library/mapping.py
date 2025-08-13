# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' This library will fetch more info for different game sources '''
import os
from pathlib import Path
from typing import Optional, Any
import sqlite3
from utils.core import backend_log

LUTRIS_PREFIX = "lutris:rungameid/"

def is_lutris(launch_options: str) -> bool:
    ''' returns whether launch_options are lutris '''
    return LUTRIS_PREFIX in launch_options

def get_id_from_lutris_command(lutris_cmd: str) -> str:
    ''' returns lutris id from a lutris command'''
    if "lutris:rungameid" not in lutris_cmd:
        return ""
    args: list = lutris_cmd.split(" ")
    arg: str
    for arg in args:
        if LUTRIS_PREFIX in arg:
            return arg.replace(LUTRIS_PREFIX, "")
    print("a code that should never be reached somehow ended being reached")
    return ""

def find_lutris_db() -> Optional[str]:
    ''' iterate over possible lutris database paths, and returns the existing one '''
    lutris_database_paths = ["~/.local/share/lutris/pga.db",
                         "~/.var/app/net.lutris.Lutris/data/lutris/pga.db"]
    for lutris_db in lutris_database_paths:
        lutris_db = os.path.expanduser(lutris_db)
        if Path(lutris_db).exists():
            return lutris_db
    return None

def get_property_from_lutris(lutris_id, property_key: str) -> Any:
    ''' gets a property from lutris db '''
    lutris_db = find_lutris_db()
    if lutris_db is None:
        return None
    conn = sqlite3.connect(lutris_db)
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
        SELECT {property_key}
        FROM games
        WHERE id=?
        """, (lutris_id,))
    except sqlite3.ProgrammingError as e:
        backend_log(f"exception executing SQL: {e}")
        return None
    game = cursor.fetchone()
    if game:
        return game[0]
    return None
