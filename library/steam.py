# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Steam library module '''
import struct
import glob
import os
import sys
import re
import shutil
import platform
import traceback
from pathlib import Path
from functools import lru_cache
from typing import Optional
# third-party imports
import vdf

from utils.core import backend_log, get_config, update_config
from library import binary_vdf_parser, source
from library import wrapper, common, mapping

APP_BASE_NAME = os.path.basename(sys.argv[0])

hardcoded_exclusions = ["Proton Experimental",
                        "Steamworks Common Redistributables",
                        "Steam Linux Runtime 1.0 (scout)",
                        "Steam Linux Runtime 2.0 (soldier)",
                        "Steam Linux Runtime 3.0 (sniper)",
                        "Proton 10.0 (Beta)",
                        "Proton 9.0",
                        "Proton 8.0",
                        "Proton 7.0",
                        "Proton 5.0",
                        "Proton 4.2",
                        "Proton 3.7",
                        "Proton 3.16",
                        "Proton 3.0",
                        "Proton Hotfix",
                        "Proton EasyAntiCheat Runtime",
                        "Proton BattlEye Runtime",
                        APP_BASE_NAME]

def set_shortcut_exe(shortcuts: dict, game:dict, app_exe: str):
    ''' Sets shortcut executable '''
    shortcut_index = game["Index"]
    shortcut = shortcuts['shortcuts'][shortcut_index]
    if "originalExe" not in shortcut:
        shortcut["originalExe"] = shortcut["Exe"]
    else:
        backend_log("[debug]Skipping shortcut property backup")
    shortcut["Exe"] = app_exe

def set_shortcut_launch_options(steam_env: dict, game:dict, options:str, sht: dict = None) -> bool:
    ''' Set launch options for non-steam games '''
    if steam_env is None:
        steam_env = get_steam_env()
    shortcut_index = game["Index"]
    if sht is None:
        parser = binary_vdf_parser.BinaryVDFParser(None)
        shortcuts_file: str = steam_env["shortcuts"]
        shortcuts: dict = parser.parse_shortcut(shortcuts_file)
    else:
        shortcuts: dict = sht
    shortcuts['shortcuts'][shortcut_index]["LaunchOptions"] = options
    if sht is None:
        parser.save_shortcut(shortcuts_file, shortcuts)
    return True

def read_shortcuts(steam_env: dict) -> dict:
    ''' wrapper for reading shortcuts from disk '''
    shortcuts_file: str = steam_env["shortcuts"]
    parser = binary_vdf_parser.BinaryVDFParser(None)
    shortcuts: dict = parser.parse_shortcut(shortcuts_file)
    return shortcuts

def save_shortcuts(steam_env: dict, shortcuts: dict):
    ''' saves shortcuts to disk '''
    shortcuts_file = steam_env["shortcuts"]
    parser =  binary_vdf_parser.BinaryVDFParser(None)
    parser.save_shortcut(shortcuts_file, shortcuts)

@lru_cache(maxsize=1)
def read_local_config(vdf_path: str = None) -> Optional[dict]:
    ''' reads localconfig.vdf '''
    if vdf_path is None:
        vdf_path = get_steam_env()["localconfig.vdf"]
    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = vdf.load(f)
        return data
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Failed to read {vdf_path}: {e}")
        return None

def save_local_config(steam: dict, data: dict):
    ''' Writes local_config.vdf to disk '''
    vdf_path = steam["shortcuts"].replace("shortcuts.vdf", "localconfig.vdf")
    read_local_config.cache_clear()
    with open(vdf_path, "w", encoding="utf-8") as f:
        vdf.dump(data, f, pretty=True)

def get_launch_options(steam: dict, appid: str) -> str:
    ''' Returns LaunchOptions for a given appid '''
    if steam is None:
        steam = get_steam_env()
    data = read_local_config(steam["localconfig.vdf"])
    if data is None:
        return ""
    software_dict = data["UserLocalConfigStore"]["Software"]
    if "valve" in software_dict:
        valve_dict = software_dict["valve"]
    else:
        valve_dict = software_dict["Valve"]
    if appid not in valve_dict["Steam"]["apps"]:
        return ""
    game_dict = valve_dict["Steam"]["apps"][appid]
    if "LaunchOptions" in game_dict:
        return game_dict["LaunchOptions"]
    return ""

def set_launch_options(steam: dict, appid: str, options: str, localconfig: dict = None) -> bool:
    """Set the LaunchOptions for a given appid in localconfig.vdf"""
    if steam is None:
        steam = get_steam_env()
    if localconfig is None:
        data = read_local_config(steam["localconfig.vdf"])
    else:
        data = localconfig
    if data is None:
        return False
    try:
        software_dict:dict = data["UserLocalConfigStore"]["Software"]
        if "valve" in software_dict:
            valve_dict:dict = software_dict["valve"]
        else:
            valve_dict:dict = software_dict["Valve"]
        if appid not in valve_dict["Steam"]["apps"]:
            valve_dict["Steam"]["apps"][appid] = {}
        valve_dict["Steam"]["apps"][appid]["LaunchOptions"] = options
    except KeyError:
        backend_log("Unable to set launch options, key error")
        return False
    if localconfig is None:
        save_local_config(steam, data)
    return True

def parse_acf(acf_path: str) -> dict:
    """Parse an ACF file to get game info"""
    try:
        with open(acf_path, 'r', encoding='utf-8') as f:
            data = parse_text_vdf(f.read())
    except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
        backend_log(f"Error reading ACF file {acf_path}: {e}")
        return {}
    app_state = data.get("AppState", {})
    acf = {}
    acf["appid"] = app_state.get("appid", "")
    acf["name"] = app_state.get("name", "")
    acf["install_dir"] = app_state.get("installdir", "")
    return acf

def parse_text_vdf(vdf_text) -> dict:
    """Simple text VDF parser (simplified version)"""
    # This is a simplified version - for full parsing you might want to use a proper VDF parser
    lines = vdf_text.split('\n')
    stack = []
    current = {}
    result = current
    key = None# Prevent crash
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        if line == '{':
            new_dict = {}
            stack.append((current, key))
            current[key] = new_dict
            current = new_dict
        elif line == '}':
            if stack:
                current, key = stack.pop()
        else:
            parts = line.split('"')
            if len(parts) >= 3:
                key = parts[1]
                value = parts[3] if len(parts) >= 4 else ""
                current[key] = value
    return result

def get_non_steam_games(steam_env: dict) -> dict:
    """Get Non-Steam games from shortcuts.vdf files"""
    games = {}
    if steam_env is None:
        return games
    steam_launch_path = steam_env["launchPath"]

    shortcuts_pattern = steam_env["shortcuts"]
    shortcuts_files = glob.glob(shortcuts_pattern)
    for file in shortcuts_files:
        try:
            data = binary_vdf_parser.BinaryVDFParser(None).parse_shortcut(file)
            shortcuts = data.get("shortcuts", {})
            # Iterate over each shortcut, 'key' discarded with _
            for shorcut_index, shortcut in shortcuts.items():
                if not isinstance(shortcut, dict):
                    continue
                app_name: str = shortcut.get("AppName", "")
                app_dir = shortcut.get("StartDir", "")
                app_options = shortcut.get("LaunchOptions", "")

                app_id = int(shortcut.get("appid", 0)) if shortcut.get("appid") else 0
                app_id = str(get_rungameid(app_id))

                app_exe: str = shortcut.get("Exe", "")
                game_config = source.get_title_config(app_id)
                if "Exe" in game_config:
                    app_exe = game_config["Exe"]
                else:
                    game_config["Exe"] = app_exe
                    source.set_title_config(app_id, game_config)

                if "moondeckrun" in app_exe:
                    continue

                if app_name in hardcoded_exclusions:
                    if app_name == APP_BASE_NAME:
                        user_config = get_config()
                        user_config["mukkuru_steam_id"] = app_id
                        update_config(user_config)
                    backend_log(f"Skipping {app_name} ({app_id}) due to hardcoded exclusion")
                    continue
                icon = shortcut.get("icon", "")

                if app_name and app_id:
                    games[app_id] = {
                        "AppName": app_name,
                        "icon": icon,
                        "AppExe": app_exe,
                        "StartDir": app_dir,
                        "AppOptions": app_options,
                        "Exe": os.path.join(steam_launch_path),
                        "LaunchOptions" : f'steam://rungameid/{app_id}',
                        "Hero": os.path.join(steam_env["gridPath"], app_id+"_hero.jpg"),
                        "Logo": os.path.join(steam_env["gridPath"], app_id+"_logo.png"),
                        "Cover": os.path.join(steam_env["gridPath"], app_id+"p.jpg"),
                        "Source" : "non-steam",
                        "Index" : shorcut_index,
                        "Managed" : "mukkuru" in app_options,
                        #"Proton" : needs_proton,
                        "Type" : steam_env["type"]
                    }
                    install_dir: str = None
                    if mapping.is_lutris(app_options):
                        lutris_id = mapping.get_id_from_lutris_command(app_options)
                        install_dir = mapping.get_property_from_lutris(lutris_id, "directory")
                    if install_dir:
                        games[app_id]["InstallDir"] = install_dir
        except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
            backend_log(f"Error processing {file}: {e} => {traceback.format_exc()}")
    return games

# Unused, will be implemented in future
def uninstall_steam_game(steam: dict, appid: str, game: dict = None) -> None:
    ''' Uninstall a Steam game '''
    steam_library_file = steam["libraryFile"]
    libraries = get_steam_libraries(steam_library_file)
    if game is None:
        games = get_steam_games(steam)
        game = games[appid]
    if game["Source"] != "steam":
        backend_log("Unsupported source")
        return
    if "InstallDir" not in game:
        backend_log("Unsupported game")
        return
    for lib in libraries:
        game_manifest = os.path.join(lib,f"appmanifest_{appid}.acf")
        if Path(game_manifest).is_file():
            os.remove(game_manifest)
        break
    shutil.rmtree(game["InstallDir"])

def get_steam_libraries(vdf_path) -> list:
    """Get Steam library paths from libraryfolders.vdf"""
    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = parse_text_vdf(f.read())
    except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
        backend_log(f"Error reading libraryfolders.vdf: {e}")
        return []
    library_folders = data.get("libraryfolders", {})
    paths = []
    for key, val in library_folders.items():
        if key.isdigit():  # Library folders have numerical keys
            if isinstance(val, dict):
                folder_path = val.get("path", "")
                backend_log(f"steam folder_path : {folder_path}")
                if folder_path:
                    norm_path = os.path.normpath(os.path.join(folder_path, "steamapps"))
                    paths.append(norm_path)
    # Include main Steam folder (this is likely unnnecesary)
    return paths

def get_rungameid(shortcut_appid: int) -> int:
    """Turn a 32‑bit shortcut AppID into the 64‑bit value."""
    return (shortcut_appid << 32) | 0x02000000

def get_proton_command(app_id: str, command: str, user_config: dict) -> str:
    ''' run game using proton '''
    steam = get_steam_env()
    proton_list = get_proton_list()
    proton_version = proton_list[0]
    if app_id in user_config["protonConfig"]:
        proton_version = user_config["protonConfig"][app_id]
    else:
        backend_log(f"Using default {proton_version}")
    proton = os.path.join(steam["path"], "steamapps", "common", proton_version, "proton")
    if not Path(proton).exists():
        backend_log("proton runtime not found")
        return command
    compat_data_path = os.path.join(steam["path"], "steamapps", "compatdata", app_id)
    if not Path(compat_data_path).exists():
        backend_log("compat_data not found")
        return command
    os.environ["STEAM_COMPAT_DATA_PATH"] = compat_data_path
    os.environ["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = steam["path"]
    if " " in proton:
        proton = f'"{proton}"'
    return f"{proton} run {command}"

def get_proton_list() -> list:
    ''' list proton builds '''
    proton_builds = []
    steam = get_steam_env()
    if steam is None:
        return proton_builds
    proton_root = os.path.join(steam["path"], "steamapps", "common")
    for proton_build in os.listdir(proton_root):
        if proton_build.startswith("Proton "):
            proton_builds.append(proton_build)
    return proton_builds

def get_steam_games(steam: dict) -> dict:
    """ Get steam games """
    games = {}
    if steam is None:
        return games
    steam_library_file = steam["libraryFile"]
    steam_path = steam["path"]
    steam_launch_path = steam["launchPath"]

    libraries = get_steam_libraries(steam_library_file)
    # crossover hotfix
    main_folder = os.path.join(steam["path"], "steamapps")
    if not main_folder in libraries:
       libraries.append(main_folder)
    
    library_cache = os.path.join(steam_path, "appcache", "librarycache")
    # Scan Steam games
    for lib in libraries:
        print(f"steam lib {lib}")
        for acf_file in Path(lib).glob("appmanifest_*.acf"):
            acf = parse_acf(str(acf_file))
            app_id = acf["appid"]
            name = acf["name"]
            app_options = get_launch_options(steam, app_id)

            common_path = os.path.join(lib, "common")
            install_dir =  os.path.join(common_path, acf["install_dir"])

            if name in hardcoded_exclusions:
                print(f"Skipping {name} since is a hardcoded exclusion")
                continue
            if app_id:
                games[app_id] = {
                    "AppName": name,
                    "icon": os.path.join(library_cache, f"{app_id}_icon.jpg"),
                    "Exe": os.path.join(steam_launch_path),
                    "AppOptions" : app_options,
                    "LaunchOptions" : f'steam://rungameid/{app_id}',
                    "InstallDir" : install_dir,
                    "StartDir" : install_dir,
                    "Hero": os.path.join(library_cache, f"{app_id}", "library_hero.jpg"),
                    "Logo": os.path.join(library_cache, f"{app_id}", "logo.png"),
                    "Managed" : "mukkuru" in app_options,
                    "Source" : "steam",
                    "Type" : steam["type"]
                }
    return games

@lru_cache(maxsize=1)
def read_steam_username(steam_config) -> Optional[str]:
    ''' get username from steam files '''
    with open(steam_config, "r", encoding="utf-8") as file:
        content = file.read()
        # Regex to match the structure under "Accounts"
        matches = re.findall(r'"Accounts"\s*{\s*"(.*?)"', content)
        if matches:
            return matches[0]  # Return the first found username
        backend_log("No usernames found under 'Accounts'.")
        return None

def get_steam_avatar_from_cache(artwork_dir: str, steam_username: str) -> bool:
    ''' Copy steam avatar from disk '''
    steam = get_steam_env()
    avatarcache = os.path.join(steam["path"], "config", "avatarcache")
    avatar_file = None
    extension = None
    if not Path(avatarcache).is_dir():
        backend_log("avatarcache dir not found")
        return False
    for file in os.listdir(avatarcache):
        if file.endswith(".png") or file.endswith(".jpg"):
            avatar_file = file
            extension = ".jpg" if file.endswith(".jpg") else ".png"
            break
    if avatar_file is None:
        backend_log("avatarcache image not found")
        return False
    avatar_image = os.path.join(avatarcache, avatar_file)
    avatar_path = os.path.join(artwork_dir, "Avatar", steam_username + extension)
    shutil.copy(avatar_image, avatar_path)
    return True

def get_steam_avatar(artwork_dir: str) -> bool:
    ''' Wrapper for get_steam_avatar_from_cache '''
    steam = get_steam_env()
    if steam is None:
        return False
    steam_config = steam["config.vdf"]
    steam_username = read_steam_username(steam_config)
    if steam_username is None:
        backend_log("Unable to query avatar picture")
        return False
    avatar_path = os.path.join(artwork_dir, "Avatar", steam_username+".jpg")
    avatar_path_alt = os.path.join(artwork_dir, "Avatar", steam_username+".png")
    avatar_exists = Path(avatar_path).is_file() and os.path.getsize(avatar_path) > 0
    alt_exists = Path(avatar_path_alt).is_file() and os.path.getsize(avatar_path_alt) > 0
    if Path(avatar_path).is_file() and not avatar_exists:
        os.remove(avatar_path)
    if Path(avatar_path_alt).is_file() and not alt_exists:
        os.remove(avatar_path_alt)
    if avatar_exists or alt_exists:
        backend_log("Avatar image exists, skipping...")
        return False
    return get_steam_avatar_from_cache(artwork_dir, steam_username)

def map_shortcuts_path(shortcut_path: str) -> Optional[str]:
    ''' find shortcuts path '''
    find_stuser = shortcut_path.split('*')[0]
    st_user = None
    # This will prevent annoying .DS_Store from breaking the path detection
    try:
        for file in os.listdir(find_stuser):
            if file.isdigit() and file != "0":
                st_user = file
                break
    except FileNotFoundError:
        return None
    return shortcut_path.replace("*", st_user, 1)

def get_crossover_steam() -> Optional[dict]:
    ''' gets steam paths for crossover install'''
    system = platform.system()
    steam = {}
    prefix = ""
    if system == "Darwin":
        crossenv = wrapper.get_crossover_env("Steam")
        prefix = crossenv["CX_DISK"]
    else:
        return None
    prefix = os.path.expanduser(prefix)
    steam["path"] = os.path.join(prefix, "Program Files (x86)/Steam")
    if not Path(steam["path"]).exists():
        backend_log("(CrossOver) Steam is not available")
        return None
    steam["libraryFile"] = os.path.join(steam["path"],"steamapps", "libraryfolders.vdf")
    shortcut_path = os.path.join(steam["path"],"userdata", "*", "config", "shortcuts.vdf")
    steam["shortcuts"] = map_shortcuts_path(shortcut_path)
    steam["launchPath"] = os.path.join("C:", "Program Files (x86)", "Steam", "Steam.exe")
    steam["crossover"] = True
    if not Path(steam["libraryFile"]).is_file():
        backend_log("(CrossOver) Steam is not available")
        return None
    steam["gridPath"] = steam["shortcuts"].replace("shortcuts.vdf", "grid", 1)
    steam["config.vdf"] = os.path.join(steam["path"], "config", "config.vdf")
    steam["localconfig.vdf"] = steam["shortcuts"].replace("shortcuts.vdf", "localconfig.vdf")
    steam["type"] = "CROSSOVER"
    if not Path(steam["shortcuts"]).is_file():
        backend_log(f'Unable to find: {steam["shortcuts"]}\n')
    # To-do:
    # -Find linux crossover bottle directory
    print(steam)
    return steam

@lru_cache(maxsize=1)
def get_steam_env() -> Optional[dict]:
    ''' Get steam paths depending on platform '''
    system = platform.system()
    steam = {}
    if system == "Windows":
        program_files = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles")
        steam["path"] = os.path.join(program_files, "Steam")
        if not Path(steam["path"]).is_dir():
            backend_log("Steam not in common path, reading registry as a failover...")
            vsk = r"SOFTWARE\WOW6432Node\Valve\Steam"
            steam["path"] = common.read_registry_value(0, vsk, "InstallPath")
        steam["libraryFile"] = os.path.join(steam["path"], "steamapps", "libraryfolders.vdf")
        shortcut_path = os.path.join(steam["path"],"userdata", "*", "config", "shortcuts.vdf")
        steam["shortcuts"] = map_shortcuts_path(shortcut_path)
        steam["launchPath"] = os.path.join(steam["path"], "Steam.exe")
    if system == "Linux":
        launch_paths = [
            "/usr/bin/steam",
            "/snap/bin/steam"
        ]
        main_paths = [
            "~/.local/share/Steam",
            "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",
            "~/snap/steam/common/.steam/steam"
        ]
        steam["launchPath"] = common.find_path(launch_paths)
        steam["path"] = common.find_path(main_paths)
        steam["libraryFile"] = os.path.join(steam["path"],"steamapps", "libraryfolders.vdf")
        shortcut_path = os.path.join(steam["path"], "userdata", "*", "config", "shortcuts.vdf")
        steam["shortcuts"] = map_shortcuts_path(shortcut_path)
        if steam["launchPath"] is None and steam["path"] == os.path.expanduser(main_paths[1]):
            steam["launchPath"] = "flatpak run com.valvesoftware.Steam"
    if system == "Darwin":
        steam["launchPath"] = "/Applications/Steam.app/Contents/MacOS/steam_osx"
        steam["path"] = os.path.expanduser("~/Library/Application Support/Steam")
        steam["libraryFile"] = os.path.join(steam["path"],
                                                           "steamapps", "libraryfolders.vdf")
        shortcut_path = os.path.join(steam["path"], "userdata", "*", "config", "shortcuts.vdf")
        steam["shortcuts"] = map_shortcuts_path(shortcut_path)
    if not Path(steam["libraryFile"]).is_file():
        backend_log("Steam is not available")
        return None
    steam["gridPath"] = steam["shortcuts"].replace("shortcuts.vdf", "grid", 1)
    steam["localconfig.vdf"] = steam["shortcuts"].replace("shortcuts.vdf", "localconfig.vdf")
    steam["config.vdf"] = os.path.join(steam["path"], "config", "config.vdf")
    steam["type"] = "NATIVE"
    if not Path(steam["shortcuts"]).is_file():
        backend_log(f'Unable to find: {steam["shortcuts"]}\n')
    return steam
