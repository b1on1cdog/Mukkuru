# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Steam library module '''
import struct
import glob
import os
import re
import platform
import sys
from pathlib import Path
from functools import lru_cache
# third-party imports
import requests
from library import binary_vdf_parser
from library import grid_db

if platform.system() == "Windows":
    import winreg
hardcoded_exclusions = ["Proton Experimental",
                        "Steamworks Common Redistributables",
                        "Steam Linux Runtime 1.0 (scout)",
                        "Steam Linux Runtime 2.0 (soldier)",
                        "Steam Linux Runtime 3.0 (sniper)",
                        "Proton 10.0 (Beta)"
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
                        "Proton BattlEye Runtime"]

AVATAR_DOWNLOAD_URL = "https://api.panyolsoft.com/steam/avatar/[USERNAME]"

def read_binary_vdf(vdf_path):
    """Read binary VDF file using a Python implementation"""
    try:
        with open(vdf_path, 'rb') as f:
            return parse_binary_vdf(f)
    except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
        print(f"Error reading binary VDF: {e}")
        return "{}"

def parseshortcut(file):
    ''' returns shortcuts '''
    vdf = binary_vdf_parser.BinaryVDFParser(None)
    return vdf.parse_shortcut(file)

def parse_binary_vdf(file_obj):
    """Parse binary VDF file"""
    result = {}
    while True:
        key = read_string(file_obj)
        if not key:
            break
        value_type = file_obj.read(1)[0]
        if value_type == 0x00:  # End of file
            break
        if value_type == 0x01:  # String
            result[key] = read_string(file_obj)
        elif value_type == 0x02:  # Int32
            result[key] = struct.unpack('<i', file_obj.read(4))[0]
        elif value_type == 0x08:  # Dictionary
            result[key] = parse_binary_vdf(file_obj)
        else:
            raise ValueError(f"Unknown value type: {value_type}")
    return result

def read_string(file_obj):
    """Read null-terminated string from file"""
    chars = []
    while True:
        c = file_obj.read(1)
        if not c or c == b'\x00':
            break
        chars.append(c)
    return b''.join(chars).decode('utf-8')

def parse_acf(acf_path):
    """Parse an ACF file to get AppID and game name"""
    try:
        with open(acf_path, 'r', encoding='utf-8') as f:
            data = parse_text_vdf(f.read())
    except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
        print(f"Error reading ACF file {acf_path}: {e}")
        return "", ""
    app_state = data.get("AppState", {})
    app_id = app_state.get("appid", "")
    name = app_state.get("name", "")
    return app_id, name

def parse_text_vdf(vdf_text):
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

def get_non_steam_games(steam_env):
    """Get Non-Steam games from shortcuts.vdf files"""
    games = {}
    if steam_env is None:
        return games
    steam_launch_path = steam_env["launchPath"]
    # Find all shortcuts.vdf files
    shortcuts_pattern = steam_env["shortcuts"]
    shortcuts_files = glob.glob(shortcuts_pattern)
    for file in shortcuts_files:
        try:
            # Read and parse the binary VDF file
            data = parseshortcut(file)
            # Extract the "shortcuts" section
            shortcuts = data.get("shortcuts", {})
            # Iterate over each shortcut, 'key' discarded with _
            for _, shortcut in shortcuts.items():
                if not isinstance(shortcut, dict):
                    continue
                app_name = shortcut.get("AppName", "")
                if app_name in hardcoded_exclusions:
                    continue

                app_exe = shortcut.get("Exe", "")

                if "moondeckrun" in app_exe:
                    continue

                app_dir = shortcut.get("StartDir", "")
                #app_options = shortcut.get("LaunchOptions", "")

                app_id = int(shortcut.get("appid", 0)) if shortcut.get("appid") else 0
                app_id = str(get_rungameid(app_id))
                icon = shortcut.get("icon", "")

                #needs_proton = False

                #if app_exe.strip('"').endswith(".exe") and platform.system() == "Linux":
                #    needs_proton = True

                if app_name and app_id:
                    games[app_id] = {
                        "AppName": app_name,
                        "icon": icon,
       #                 "Exe": app_exe,
                        "StartDir": app_dir,
       #                 "LaunchOptions": app_options,
                        "Exe": os.path.join(steam_launch_path),
                        "LaunchOptions" : f'steam://rungameid/{app_id}',
                        "Hero": os.path.join(steam_env["gridPath"], app_id+"_hero.jpg"),
                        "Logo": os.path.join(steam_env["gridPath"], app_id+"_logo.png"),
                        "Cover": os.path.join(steam_env["gridPath"], app_id+"p.jpg"),
                        "Source" : "non-steam",
                        #"Proton" : needs_proton,
                        "Type" : steam_env["type"]
                    }
        except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
            print(f"Error processing {file}: {e}")
    return games

def get_steam_libraries(vdf_path, steam_env):
    """Get Steam library paths from libraryfolders.vdf"""
    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = parse_text_vdf(f.read())
    except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
        print(f"Error reading libraryfolders.vdf: {e}")
        return []
    library_folders = data.get("libraryfolders", {})
    paths = []
    for key, val in library_folders.items():
        if key.isdigit():  # Library folders have numerical keys
            if isinstance(val, dict):
                folder_path = val.get("path", "")
                if folder_path:
                    paths.append(os.path.join(folder_path, "steamapps"))
    # Include main Steam folder
    paths.append(os.path.join(steam_env["path"], "steamapps"))
    return paths

def get_rungameid(shortcut_appid: int) -> int:
    """
    Turn a 32‑bit shortcut AppID into the 64‑bit value.
    """
    return (shortcut_appid << 32) | 0x02000000

def get_proton_command(app_id, command, user_config):
    ''' run game using proton '''
    steam = get_steam_env()
    proton_list = get_proton_list()
    proton_version = proton_list[0]
    if app_id in user_config["protonConfig"]:
        proton_version = user_config["protonConfig"][app_id]
    else:
        print(f"Using default {proton_version}")
    proton = os.path.join(steam["path"], "steamapps", "common", proton_version, "proton")
    if not Path(proton).exists():
        print("proton runtime not found")
        return command
    compat_data_path = os.path.join(steam["path"], "steamapps", "compatdata", app_id)
    if not Path(compat_data_path).exists():
        print("compat_data not found")
        return command
    os.environ["STEAM_COMPAT_DATA_PATH"] = compat_data_path
    os.environ["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = steam["path"]
    if " " in proton:
        proton = f'"{proton}"'
    return f"{proton} run {command}"

def get_proton_list():
    ''' list proton builds '''
    proton_builds = []
    steam = get_steam_env()
    proton_root = os.path.join(steam["path"], "steamapps", "common")
    for proton_build in os.listdir(proton_root):
        if proton_build.startswith("Proton "):
            proton_builds.append(proton_build)
    return proton_builds

def get_steam_games(steam):
    """ Get steam games """
    games = {}
    if steam is None:
        return games
    steam_library_file = steam["libraryFile"]
    steam_path = steam["path"]
    steam_launch_path = steam["launchPath"]

    libraries = get_steam_libraries(steam_library_file, steam)
    library_cache = os.path.join(steam_path, "appcache", "librarycache")
    # Scan Steam games
    for lib in libraries:
        for acf_file in Path(lib).glob("appmanifest_*.acf"):
            app_id, name = parse_acf(str(acf_file))
            if name in hardcoded_exclusions:
                continue
            if app_id:
                games[app_id] = {
                    "AppName": name,
                    "icon": os.path.join(library_cache, f"{app_id}_icon.jpg"),
                    "Exe": os.path.join(steam_launch_path),
                    "LaunchOptions" : f'steam://rungameid/{app_id}',
                    "Hero": os.path.join(library_cache, f"{app_id}", "library_hero.jpg"),
                    "Logo": os.path.join(library_cache, f"{app_id}", "logo.png"),
                    "Source" : "steam",
                    "Type" : steam["type"]
                }
    return games

@lru_cache(maxsize=1)
def read_steam_username(steam_config):
    ''' get username from steam files '''
    with open(steam_config, "r", encoding="utf-8") as file:
        content = file.read()
        # Regex to match the structure under "Accounts"
        matches = re.findall(r'"Accounts"\s*{\s*"(.*?)"', content)
        if matches:
            return matches[0]  # Return the first found username
        print("No usernames found under 'Accounts'.")
        return None

def copy_file(source, destination):
    ''' copy a file from "source" to "destination" '''
    with open(source, 'rb') as src, open(destination,'wb') as dst:
        dst.write(src.read())

def get_steam_avatar_from_cache(artwork_dir, steam_username):
    ''' Copy steam avatar from disk '''
    steam = get_steam_env()
    avatarcache = os.path.join(steam["path"], "config", "avatarcache")
    avatar_file = None
    extension = None
    if not Path(avatarcache).is_dir():
        print("avatarcache dir not found")
        return None
    for file in os.listdir(avatarcache):
        if file.endswith(".png") or file.endswith(".jpg"):
            avatar_file = file
            extension = ".jpg" if file.endswith(".jpg") else ".png"
            break
    if avatar_file is None:
        print("avatarcache image not found")
        return None
    avatar_image = os.path.join(avatarcache, avatar_file)
    avatar_path = os.path.join(artwork_dir, "Avatar", steam_username + extension)
    copy_file(avatar_image, avatar_path)

def download_steam_avatar(artwork_dir):
    ''' (if not exists) downloads steam avatar picture '''
    steam = get_steam_env()
    if steam is None:
        return None
    steam_config = steam["config.vdf"]
    steam_username = read_steam_username(steam_config)
    if steam_username is None:
        print("Unable to query avatar picture")
        return
    avatar_path = os.path.join(artwork_dir, "Avatar", steam_username+".jpg")
    avatar_path_alt = os.path.join(artwork_dir, "Avatar", steam_username+".png")
    if Path(avatar_path).is_file() or Path(avatar_path_alt).is_file():
        print("Avatar image exists, skipping...")
        return
    r=requests.get(AVATAR_DOWNLOAD_URL.replace("[USERNAME]", steam_username), timeout=20)
    avatar_url = r.text
    if "http" in avatar_url:
        print("downloading steam user avatar image...")
        grid_db.download_file(avatar_url, avatar_path)
    else:
        print(f"Invalid avatar url: {avatar_url}")
        get_steam_avatar_from_cache(artwork_dir, steam_username)

def read_registry_value(root, reg_key, reg_value):
    ''' [Windows only] read key from System Registry'''
    if platform.system() == 'Windows':
        if 'winreg' in sys.modules:
            hroot = winreg.HKEY_LOCAL_MACHINE
            if root == 1:
                hroot = winreg.HKEY_CURRENT_USER
            elif root == 2:
                hroot = winreg.HKEY_CURRENT_CONFIG
            elif root == 3:
                hroot = winreg.HKEY_CLASSES_ROOT
            key = winreg.OpenKey(hroot, reg_key)
            ret, _ = winreg.QueryValueEx(key, reg_value)
            return ret
        else:
            print("platform specific module not imported: winreg")
            return None
    else:
        print('Unsupported function called')
        return None

def map_shortcuts_path(shortcut_path):
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

def find_path(paths):
    ''' return which path exists of all the candidates '''
    for path in paths:
        if "~" in path:
            path = os.path.expanduser(path)
        if Path(path).exists():
            return path
    return None

def get_crossover_env():
    ''' get crossover environment variables '''
    crossenv = os.environ.copy()
    crossover_app = os.path.expanduser("~/Applications/CrossOver.app/")
    cxroot = os.path.join(crossover_app, "Contents", "SharedSupport", "CrossOver")
    cxbottlepath = os.path.expanduser("~/Library/Application Support/CrossOver/Bottles")
    crossenv["PYTHONPATH"] = os.path.join(cxroot, "lib", "python")
    crossenv["CX_MANAGED_BOTTLE_PATH"] = "/Library/Application Support/CrossOver/Bottles"
    crossenv["CX_BOTTLE"] = "Steam"
    crossenv["CX_BOTTLE_PATH"] = cxbottlepath
    crossenv["CX_APP_BUNDLE_PATH"] = crossover_app
    crossenv["CX_ROOT"] = cxroot
    crossenv["CX_DISK"] = os.path.join(cxbottlepath, crossenv["CX_BOTTLE"], "drive_c")
    crossenv["PATH"] = crossenv["PATH"] + os.pathsep + os.path.join(cxroot, "bin")
    return crossenv

def get_crossover_steam():
    ''' gets steam paths for crossover install (Not implemented yet) '''
    system = platform.system()
    steam = {}
    prefix = ""
    if system == "Darwin":
        crossenv = get_crossover_env()
        prefix = crossenv["CX_DISK"]
    else:
        return None
    prefix = os.path.expanduser(prefix)
    steam["path"] = os.path.join(prefix, "Program Files (x86)/Steam")
    if not Path(steam["path"]).exists():
        print("(CrossOver) Steam is not available")
        return None
    steam["libraryFile"] = os.path.join(steam["path"],"steamapps", "libraryfolders.vdf")
    shortcut_path = os.path.join(steam["path"],"userdata", "*", "config", "shortcuts.vdf")
    steam["shortcuts"] = map_shortcuts_path(shortcut_path)
    steam["launchPath"] = os.path.join("C:", "Program Files (x86)", "Steam", "Steam.exe")
    steam["crossover"] = True
    if not Path(steam["libraryFile"]).is_file():
        print("(CrossOver) Steam is not available")
        return None
    steam["gridPath"] = steam["shortcuts"].replace("shortcuts.vdf", "grid", 1)
    steam["config.vdf"] = os.path.join(steam["path"], "config", "config.vdf")
    steam["type"] = "CROSSOVER"
    if not Path(steam["shortcuts"]).is_file():
        print(f'Unable to find: {steam["shortcuts"]}\n')
    # To-do:
    # -Find linux crossover bottle directory
    return steam

@lru_cache(maxsize=1)
def get_steam_env():
    ''' Get steam paths depending on platform '''
    system = platform.system()
    steam = {}
    if system == "Windows":
        program_files = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles")
        steam["path"] = os.path.join(program_files, "Steam")
        if not Path(steam["path"]).is_dir():
            print("Steam not in common path, reading registry as a failover...")
            vsk = r"SOFTWARE\WOW6432Node\Valve\Steam"
            steam["path"] = read_registry_value(0, vsk, "InstallPath")
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
        steam["launchPath"] = find_path(launch_paths)
        steam["path"] = find_path(main_paths)
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
        print("Steam is not available")
        return None
    steam["gridPath"] = steam["shortcuts"].replace("shortcuts.vdf", "grid", 1)
    steam["config.vdf"] = os.path.join(steam["path"], "config", "config.vdf")
    steam["type"] = "NATIVE"
    if not Path(steam["shortcuts"]).is_file():
        print(f'Unable to find: {steam["shortcuts"]}\n')
    return steam
