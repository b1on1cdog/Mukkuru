#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import glob
import json
from pathlib import Path
import binvdf
import re
import subprocess
import signal
import grid_db
import math
import psutil
import platform
import distro
import base64

from flask import Flask, request # type: ignore
from flask import send_from_directory # type: ignore
from fuzzywuzzy import fuzz # type: ignore
from fuzzywuzzy import process # type: ignore

app = Flask(__name__)

# Steam paths
game_library = {}
# App settings
mukkuru_env = {}
userConfiguration = {}
hardcoded_exclusions = ["Proton Experimental", "Steamworks Common Redistributables", "Steam Linux Runtime 3.0 (sniper)"]


def read_binary_vdf(vdf_path):
    """Read binary VDF file using a Python implementation"""
    try:
        with open(vdf_path, 'rb') as f:
            return parse_binary_vdf(f)
    except Exception as e:
        print(f"Error reading binary VDF: {e}")
        return "{}"

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
        elif value_type == 0x01:  # String
            result[key] = read_string(file_obj)
        elif value_type == 0x02:  # Int32
            result[key] = struct.unpack('<i', file_obj.read(4))[0] # type: ignore
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

def get_steam_libraries(vdf_path):
    """Get Steam library paths from libraryfolders.vdf"""
    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = parse_text_vdf(f.read())
    except Exception as e:
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
    paths.append(os.path.join(mukkuru_env["steam"]["path"], "steamapps"))
    return paths

def parse_text_vdf(vdf_text):
    """Simple text VDF parser (simplified version)"""
    # This is a simplified version - for full parsing you might want to use a proper VDF parser
    lines = vdf_text.split('\n')
    stack = []
    current = {}
    result = current
    
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

def parse_acf(acf_path):
    """Parse an ACF file to get AppID and game name"""
    try:
        with open(acf_path, 'r', encoding='utf-8') as f:
            data = parse_text_vdf(f.read())
    except Exception as e:
        print(f"Error reading ACF file {acf_path}: {e}")
        return "", ""
    
    app_state = data.get("AppState", {})
    app_id = app_state.get("appid", "")
    name = app_state.get("name", "")
    return app_id, name

def get_non_steam_games(shortcuts_pattern):
    """Get Non-Steam games from shortcuts.vdf files"""
    games = {}
    
    # Find all shortcuts.vdf files
    shortcuts_files = glob.glob(shortcuts_pattern)
    
    for file in shortcuts_files:
        try:
            # Read and parse the binary VDF file
            data = binvdf.parseshortcut(file)
            
            # Extract the "shortcuts" section
            shortcuts = data.get("shortcuts", {})
            
            # Iterate over each shortcut
            for key, shortcut in shortcuts.items():
                if not isinstance(shortcut, dict):
                    continue
                
                app_name = shortcut.get("AppName", "")
                if app_name in hardcoded_exclusions:
                    continue

                app_exe = shortcut.get("Exe", "")

                if "moondeckrun" in app_exe:
                    continue

                app_dir = shortcut.get("StartDir", "")
                app_options = shortcut.get("LaunchOptions", "")

                app_id = str(int(shortcut.get("appid", 0))) if shortcut.get("appid") else ""
                icon = shortcut.get("icon", "")


                if app_name and app_id:
                    games[app_id] = {
                        "AppName": app_name,
                        "icon": icon,
                        "Exe": app_exe,
                        "StartDir": app_dir,
                        "LaunchOptions": app_options,
                        "Hero": os.path.join(mukkuru_env["steam"]["gridPath"], app_id+"_hero.jpg"),
                        "Logo": os.path.join(mukkuru_env["steam"]["gridPath"], app_id+"_logo.png"),
                        "Cover": os.path.join(mukkuru_env["steam"]["gridPath"], app_id+"p.jpg")
                    }
                    
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    return games

def library_scan(options):
    global mukkuru_env
    '''
    1 - Steam
    2 - Non-Steam
    '''
    OPTION_STEAM = 1 << 0  # 0001 = 1
    OPTION_NONSTEAM = 1 << 1  # 0010 = 2

    # Get Steam library paths
    if options & OPTION_STEAM:
        libraries = get_steam_libraries(mukkuru_env["library_file"])
    else:
        libraries = {}

    games = {}
    
    # Scan Steam games
    for lib in libraries:
        for acf_file in Path(lib).glob("appmanifest_*.acf"):
            app_id, name = parse_acf(str(acf_file))
            print(f"found {app_id}")
            if app_id:
                games[app_id] = {
                    "AppName": name,
                    "icon": os.path.join(mukkuru_env["steam"]["path"], "appcache", "librarycache", f"{app_id}_icon.jpg"),
                    "Exe": os.path.join(mukkuru_env["steam"]["launchPath"]),
                    "LaunchOptions": f'steam://rungameid/{app_id}',
                    "Hero": os.path.join(mukkuru_env["steam"]["path"], "appcache", "librarycache", f"{app_id}", "library_hero.jpg"),
                    "Logo": os.path.join(mukkuru_env["steam"]["path"], "appcache", "librarycache", f"{app_id}", "logo.png"),
                }
    
    # Scan Non-Steam games

    if options & OPTION_NONSTEAM:
        non_steam_games = get_non_steam_games(mukkuru_env["steam"]["shortcuts"])
        games.update(non_steam_games)
    
    if Path(mukkuru_env["steam"]["shortcuts"]).is_file():
        print(f'Using { mukkuru_env["steam"]["shortcuts"] }\n')
    else:
        print(f'Unable to find: {mukkuru_env["steam"]["shortcuts"]}\n')
    return games

def get_cpu_name():
    system = platform.system()

    if system == "Windows":
        try:
            output = subprocess.check_output(["wmic", "cpu", "get", "Name"], shell=True)
            lines = output.decode().splitlines()
            # Remove empty lines and strip whitespace
            lines = [line.strip() for line in lines if line.strip()]
            if len(lines) > 1:
                return lines[1]
        except Exception:
            pass
        return platform.processor()

    elif system == "Darwin":  # macOS
        try:
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        except Exception:
            return platform.processor()

    elif system == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except Exception:
            pass
        return platform.processor()

    return "Unknown CPU"


def get_gpu_name():
    system = platform.system()

    if system == "Windows":
        try:
            output = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                shell=True
            )
            lines = output.decode().splitlines()
            lines = [line.strip() for line in lines if line.strip()]
            return lines[1] if len(lines) > 1 else "Unknown GPU"
        except Exception:
            return "Unknown GPU"

    elif system == "Linux":
        try:
            output = subprocess.check_output(
                ["lspci"], stderr=subprocess.DEVNULL
            ).decode()
            gpus = [line for line in output.splitlines() if "VGA compatible controller" in line or "3D controller" in line]
            return gpus[0].split(":")[-1].strip() if gpus else "Unknown GPU"
        except Exception:
            return "Unknown GPU"

    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"]
            ).decode()
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("Chipset Model:"):
                    return line.split(":", 1)[1].strip()
            return "Unknown GPU"
        except Exception:
            return "Unknown GPU"

    return "Unknown GPU"

@app.route("/hardware")
def harware_info():
    memory_info = psutil.virtual_memory()
    platform_info = platform.uname()
    disk_info = psutil.disk_usage('/')

    hardware_info = {}

    hardware_info["total_ram"] = round(memory_info.total/(1024*1024*1024),1)
    hardware_info["used_ram"] = round(memory_info.used/(1024*1024*1024),1)

    hardware_info["computer_name"] = platform_info.node
    hardware_info["arch"] = platform_info.machine
    hardware_info["os"] = platform_info.system

    hardware_info["distro"] = hardware_info["os"]

    if hardware_info["os"] == "Linux":
        hardware_info["distro"] = distro.name(pretty=True)
    elif hardware_info["os"] == "Windows":
        try:
            output = subprocess.check_output(['wmic', 'os', 'get', 'Caption'], shell=True)
            lines = output.decode().splitlines()
            # to-do: fix possible empty reply if lines[2] returns nothing
            hardware_info["distro"] = lines[2].strip() if len(lines) > 1 else "Microsoft Windows"
        except Exception as e:
            hardware_info["distro"] = "Windows"       

    hardware_info["disk_total"] = math.ceil(disk_info.total/(1000*1000*1000))
    hardware_info["disk_used"] = round(disk_info.used/(1000*1000*1000),1)
    hardware_info["disk_free"] = round(disk_info.free/(1000*1000*1000),1)
    hardware_info["cpu"] = get_cpu_name()
    hardware_info["gpu"] = get_gpu_name()
    return json.dumps(hardware_info)

@app.route('/app/exit')
def quit_app():
    os.kill(mukkuru_env["pid"], signal.SIGTERM)
    os._exit(0)

@app.route('/library/launch/<appId>')
def launch_app(appId):
    gamePath = game_library[appId]["Exe"].strip('"')
    print(f'Launching game: {gamePath} using {game_library[appId]["LaunchOptions"]}')
    subprocess.run(f'"{gamePath}" {game_library[appId]["LaunchOptions"]}', stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=os.environ.copy(), shell=True)
    return "200"

def read_steam_username():
    with open(mukkuru_env["steam"]["config.vdf"], "r", encoding="utf-8") as file:
            content = file.read()
            # Regex to match the structure under "Accounts"
            matches = re.findall(r'"Accounts"\s*{\s*"(.*?)"', content)
            if matches:
                return matches[0]  # Return the first found username
            else:
                print("No usernames found under 'Accounts'.")
                return None

def number_aware_scorer(s1, s2):
    base_score = fuzz.token_set_ratio(s1, s2)  # Start with standard fuzzy score
    
    # Extract all numbers from both strings
    nums1 = set(re.findall(r'\d+', s1))
    nums2 = set(re.findall(r'\d+', s2))
    
    # Penalize if numbers don't match exactly
    if nums1 != nums2:
        base_score = max(base_score - 50, 0)  # Heavy penalty for number mismatches
    
    return base_score

def find_strict_number_match(game_title, image_files, threshold=80):
    # Get the best match (even if bad)
    match, score = process.extractOne(game_title, image_files, scorer=number_aware_scorer)
    
    # Reject if score is below threshold
    if score >= threshold:
        return match
    else:
        return None  # Explicit "no match"

def fetch_local_artwork(game_title, appID):
    image_files = glob.glob(os.path.join(mukkuru_env["artwork"],"Square", '*.jpg'))
    match = find_strict_number_match(game_title, image_files, threshold=80)
    if match == None:
        filename = grid_db.download_square_image(game_title, savePath=os.path.join(mukkuru_env["artwork"],"Square"))
        if filename != False:
            if filename.endswith(".jpg"):
                print(f'downloaded {game_title} artwork from api')
                with open(filename, 'rb') as src, open(f'ui/{userConfiguration["theme"]}/thumbnails/{appID}.jpg', 'wb') as dst:
                    dst.write(src.read())
            else:
                print(f'failed to download {game_title} artwork from api')
        return None
    else:
        print(f'Found: {match} for {game_title}')
        with open(match, 'rb') as src, open(f'ui/{userConfiguration["theme"]}/thumbnails/{appID}.jpg', 'wb') as dst:
            dst.write(src.read())
        return match

@app.route('/library/artwork/scan')
def scan_local_artwork(games = None):
    if games == None:
        games = game_library
    for k in games.keys():
        if not Path(f"ui/SwitchUI/assets/thumbnail/{k}.jpg").is_file():
            fetch_local_artwork(games[k]["AppName"], k)
        else:
            print(f"{k} already has artwork, skipping...")
    return "200"

#This one must receive POST data
@app.route('/library/add')
def add_game():
    with open('library.json', 'w') as f:
        json.dump(game_library, f)
    return "Not implemented"            

@app.route('/library/get')
def get_games():
    return json.dumps(game_library)

@app.route('/config/get')
def get_config():
    return json.dumps(userConfiguration)

@app.route('/config/set', methods = ['GET', 'POST', 'DELETE'])
def set_config():
    global userConfiguration
    print("setting configuration...")
    if request.method == 'POST':
        print(request.get_json())
        userConfiguration = request.get_json()
        with open(mukkuru_env['config.json'] , 'w') as f:
            json.dump(userConfiguration, f)
        return "200"
    elif request.method == 'GET':
        return get_config()
    elif request.method == 'DELETE':
        return "500"
    return "400"

@app.route('/ping')
def ping_request():
    return "pong"


@app.route('/library/scan')
def scan_games():
    global game_library
    options = userConfiguration["librarySource"]
    games = library_scan(int(options))
    game_library.update(games)
    scan_local_artwork(games)
    for k in games.keys():
        if not Path(f'ui/{userConfiguration["theme"]}/thumbnails/{k}.jpg').is_file():
            game_library[k]["Thumbnail"] = False
        else:
            game_library[k]["Thumbnail"] = True
    with open('library.json', 'w') as f:
        json.dump(game_library, f)
#    print(json.dumps(game_library))
    return json.dumps(games)

@app.route('/log/<message>')
def log_message(message):
    print(f'[frontend] { base64.b64decode(message).decode("utf-8") }')
    return "200"

# To-do: allow custom specified username from userConfiguration
@app.route('/username')
def get_user():
    username = read_steam_username()


    if username == None:
        return os.environ.get('USER', os.environ.get('USERNAME'))
    return username

@app.route('/frontend/')
def main_web():
    return static_file("index.html")

@app.route('/frontend/<path:path>')
def static_file(path):
    query = request.args.get('pid', default='', type=str)
    if not query == '':
        global mukkuru_env
        mukkuru_env["pid"] = int(query)

    return send_from_directory(f'{os.getcwd()}/ui/{userConfiguration["theme"]}/', path)

def main():
    global mukkuru_env
    global game_library
    global userConfiguration

    mukkuru_env["steam"] = {}
    if os.name == 'nt':
        print("Running on Windows")
        mukkuru_env["steam"]["path"] = os.path.join("C:\\", "Program Files (x86)", "Steam")
        mukkuru_env["steam"]["shortcuts"] = os.path.join(mukkuru_env["steam"]["path"], "userdata", "*", "config", "shortcuts.vdf")
        mukkuru_env["steam"]["libraryFile"] = os.path.join(mukkuru_env["steam"]["path"], "steamapps", "libraryfolders.vdf")

        find_stuser = mukkuru_env["steam"]["shortcuts"].split('*')[0]
        print(find_stuser)
        steam_id = os.listdir(find_stuser)[0]
        mukkuru_env["steam"]["shortcuts"] = mukkuru_env["steam"]["shortcuts"].replace("*", steam_id, 1)
        mukkuru_env["steam"]["launchPath"] = os.path.join(mukkuru_env["steam"]["path"], "Steam.exe")
        mukkuru_env["root"] = os.path.join(os.environ.get('APPDATA'), "Mukkuru")
    elif os.name == 'posix':
        print("Running in Linux")
        # To-do: determine different steam installs
        mukkuru_env["steam"]["launchPath"] = "/usr/bin/steam"
        mukkuru_env["steam"]["path"] = os.path.expanduser("~/.local/share/Steam")
        mukkuru_env["steam"]["libraryFile"] = os.path.join(mukkuru_env["steam"]["path"], "steamapps", "libraryfolders.vdf")
        mukkuru_env["steam"]["shortcuts"] = os.path.join(mukkuru_env["steam"]["path"], "userdata", "*", "config", "shortcuts.vdf")
        mukkuru_env["root"] = os.path.join(os.path.expanduser("~"), ".config", "Mukkuru")
    else:
        print(f"Running in unsupported OS: {os.name}")
    
    if not os.path.isdir(mukkuru_env["root"]):
        os.mkdir(mukkuru_env["root"])

    mukkuru_env["library.json"] = os.path.join(mukkuru_env["root"], "library.json")
    mukkuru_env["config.json"] = os.path.join(mukkuru_env["root"], "config.json")
    mukkuru_env["artwork"] = os.path.join(mukkuru_env["root"], "artwork")

    if not os.path.isdir(mukkuru_env["artwork"]):
        os.mkdir(mukkuru_env["artwork"])
        os.mkdir(os.path.join(mukkuru_env["artwork"], "Square")  )
        os.mkdir(os.path.join(mukkuru_env["artwork"], "Logo") )
        os.mkdir(os.path.join(mukkuru_env["artwork"], "Heroes") ) 
        os.mkdir(os.path.join(mukkuru_env["artwork"], "Grid") )

    if not Path(mukkuru_env["library.json"]).is_file():
        print("No library.json")
    else:
        with open(mukkuru_env["library.json"]) as f:
            print("loading library.json")
            game_library = json.load(f)
    
    if not Path(mukkuru_env["config.json"]).is_file():
        print("No config.json")
        userConfiguration = {
            "loop" : False,
            "skipNoArt" : False,
            "maxGamesInHomeScreen" : 12,
            "theme" : "SwitchUI",
            "librarySource" : 3, #0
            "darkMode" : False,
        }
        with open(mukkuru_env["config.json"], 'w') as f:
            json.dump(userConfiguration, f)

    else:
        with open(mukkuru_env["config.json"]) as f:
            print("loading config.json")
            userConfiguration = json.load(f)

    mukkuru_env["steam"]["gridPath"] = mukkuru_env["steam"]["shortcuts"].replace("shortcuts.vdf", "grid", 1)
    mukkuru_env["steam"]["config.vdf"] = os.path.join(mukkuru_env["steam"]["path"], "config", "config.vdf")
    app.run(host='localhost', port=49347, debug=True)

if __name__ == "__main__":
    main()