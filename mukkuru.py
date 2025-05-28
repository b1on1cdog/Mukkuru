#!/usr/bin/env python3
""" Mukkuru, cross-platform game launcher """
# -*- coding: utf-8 -*-
import os
import glob
import json
from pathlib import Path
import subprocess
import math
import re
import base64
import threading
import struct
import time
# Debug only
import sys
import hashlib
import logging
import socket
import platform
import distro
import psutil

import requests

from flask import Flask, request
from flask import send_from_directory
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import grid_db
import binvdf

from mukkuru_pyside6 import Frontend
#from mukkuru_pywebview import Frontend

if platform.system() == "Windows":
    import winreg

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.CRITICAL)

mukkuru_env = {}
hardcoded_exclusions = ["Proton Experimental",
                        "Steamworks Common Redistributables",
                        "Steam Linux Runtime 1.0 (scout)",
                        "Steam Linux Runtime 2.0 (soldier)",
                        "Steam Linux Runtime 3.0 (sniper)",
                        "Proton 9.0",
                        "Proton 8.0",
                        "Proton 7.0",
                        "Proton 5.0",
                        "Proton 4.2",
                        "Proton 3.7",
                        "Proton 3.16",
                        "Proton 3.0",
                        "Proton Hotfix"]

AVATAR_DOWNLOAD_URL = "https://api.panyolsoft.com/steam/avatar/[USERNAME]"

def app_version():
    ''' generate 5 MD5 digits to use as build number '''
    path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    full_md5 = hasher.hexdigest()
    return "Mukkuru v0.2.9 build-"+full_md5[-5:]

def read_binary_vdf(vdf_path):
    """Read binary VDF file using a Python implementation"""
    try:
        with open(vdf_path, 'rb') as f:
            return parse_binary_vdf(f)
    except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
        print(f"Error reading binary VDF: {e}")
        return "{}"
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

def get_steam_libraries(vdf_path):
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
    paths.append(os.path.join(mukkuru_env["steam"]["path"], "steamapps"))
    return paths

def get_egs_games():
    ''' [Windows only] get games from epic games launcher '''
    #To-do: look for alternate ProgramData paths
    manifest_dir = r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
    if not os.path.exists(manifest_dir):
        print(f"Manifest directory not found: {manifest_dir}")
    games = {}
    for filename in os.listdir(manifest_dir):
        if filename.endswith(".item"):
            filepath = os.path.join(manifest_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    app_name = manifest["DisplayName"]
                    app_id = manifest["AppName"]
                    game_dir = os.path.join(manifest["InstallLocation"],
                                            manifest["LaunchExecutable"])
                    if app_name and app_id:
                        games[app_id] = {
                            "AppName" : app_name,
                            "catalogNamespace" : manifest["MainGameCatalogNamespace"],
                            "catalogItemID" : manifest["MainGameCatalogItemId"],
                            "LaunchOptions" : "",
                            "Exe" : game_dir,
                            "StartDir" : manifest["InstallLocation"],
                            "Source" : "egs"
                        }

            except (PermissionError, IndexError, json.decoder.JSONDecodeError) as e:
                print(f"Exception occured: {e}")
    return "Not implemented"

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
                        "Cover": os.path.join(mukkuru_env["steam"]["gridPath"], app_id+"p.jpg"),
                        "Source" : "non-steam"
                    }
        except (FileNotFoundError, PermissionError, struct.error, ValueError, IndexError) as e:
            print(f"Error processing {file}: {e}")
    return games

def library_scan(options):
    '''
    1 - Steam
    2 - Non-Steam
    4 - EGS
    '''
    option_steam = 1 << 0  # 0001 = 1
    option_nonsteam = 1 << 1  # 0010 = 2
    option_egs = 1 << 2  # 0100 = 4

    # Get Steam library paths
    if options & option_steam:
        libraries = get_steam_libraries(mukkuru_env["steam"]["libraryFile"])
    else:
        libraries = {}

    games = {}
    library_cache = os.path.join(mukkuru_env["steam"]["path"], "appcache", "librarycache")
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
                    "Exe": os.path.join(mukkuru_env["steam"]["launchPath"]),
                    "LaunchOptions": f'steam://rungameid/{app_id}',
                    "Hero": os.path.join(library_cache, f"{app_id}", "library_hero.jpg"),
                    "Logo": os.path.join(library_cache, f"{app_id}", "logo.png"),
                    "Source" : "steam",
                }
    # Scan Non-Steam games
    if options & option_nonsteam:
        non_steam_games = get_non_steam_games(mukkuru_env["steam"]["shortcuts"])
        games.update(non_steam_games)
    if options & option_egs:
        egs_games = get_egs_games()
        games.update(egs_games)
    if Path(mukkuru_env["steam"]["shortcuts"]).is_file():
        print(f'Using { mukkuru_env["steam"]["shortcuts"] }\n')
    else:
        print(f'Unable to find: {mukkuru_env["steam"]["shortcuts"]}\n')
    return games

def get_cpu_name():
    ''' get cpu name as string '''
    system = platform.system()

    if system == "Windows":
        try:
            output = subprocess.check_output(["wmic", "cpu", "get", "Name"], shell=True)
            lines = output.decode().splitlines()
            # Remove empty lines and strip whitespace
            lines = [line.strip() for line in lines if line.strip()]
            if len(lines) > 1:
                return lines[1]
        except (subprocess.CalledProcessError, IndexError, UnicodeDecodeError):
            pass
        return platform.processor()
    if system == "Darwin":  # macOS
        try:
            return subprocess.check_output(["sysctl",
                                            "-n", "machdep.cpu.brand_string"]).decode().strip()
        except (subprocess.CalledProcessError, IndexError, UnicodeDecodeError):
            return platform.processor()

    if system == "Linux":
        try:
            with open("/proc/cpuinfo", encoding='utf-8') as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except (FileNotFoundError, PermissionError, IndexError):
            pass
        return platform.processor()
    return "Unknown CPU"


def get_gpu_name():
    ''' get GPU name '''
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
        except (subprocess.CalledProcessError, IndexError, UnicodeDecodeError, PermissionError):
            return "Unknown GPU"

    elif system == "Linux":
        try:
            output = subprocess.check_output(
                ["lspci"], stderr=subprocess.DEVNULL
            ).decode()
            gpus = []
            for line in output.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    gpus.append(line)
            return gpus[0].split(":")[-1].strip() if gpus else "Unknown GPU"
        except (PermissionError, IndexError, subprocess.CalledProcessError):
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
        except (IndexError, UnicodeDecodeError, PermissionError):
            return "Unknown GPU"

    return "Unknown GPU"

def get_active_net_interfaces():
    ''' get net interfaces as an array'''
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    active = []
    for iface, info in stats.items():
        if info.isup and iface in addrs:
            active.append(iface)
    return active

def has_internet(host="8.8.8.8", port=53, timeout=0.3):
    ''' Ping servers to determine whether device has access to net '''
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except TimeoutError:
        return False

def is_using_wireless():
    ''' return whether a Wireless connection is being used '''
    interfaces = get_active_net_interfaces()
    interface = interfaces[0]
    system = platform.system()

    if system == "Darwin":
        try:
            hwports = subprocess.check_output(["networksetup", "-listallhardwareports"]).decode()
            blocks = hwports.strip().split("Hardware Port:")
            for block in blocks:
                if "Wi-Fi" in block or "AirPort" in block:
                    match = re.search(r"Device: (\w+)", block)
                    if match and match.group(1) == interface:
                        return True
            return False
        except (IndexError, PermissionError):
            return False
    if system == "Linux":
        return os.path.isdir(f"/sys/class/net/{interface}/wireless")
    if system == "Windows":
        try:
            output = subprocess.check_output("netsh wlan show interfaces",
                                             shell=True).decode(errors="ignore")
            return interface.lower() in output.lower()
        except (IndexError, subprocess.CalledProcessError, PermissionError):
            return False

def wireless_signal():
    '''Get the signal of Wi-Fi'''
    return 100

@app.route("/hardware/network")
def connection_status():
    ''' returns a json with connection status'''
    status = {}
    status["wifi"] = is_using_wireless()
    status["internet"] = has_internet() or has_internet()
    if status["internet"] is False:
        status["internet"] = has_internet(host="8.8.4.4") or has_internet(host="1.1.1.1")
    status["signal"] = wireless_signal()
    return json.dumps(status)
@app.route("/hardware/battery")
def battery_info():
    ''' Return a JSON containing battery details '''
    response = json.dumps(psutil.sensors_battery())
    return response

@app.route("/hardware")
def harware_info():
    ''' get hardware info as a json '''
    memory_info = psutil.virtual_memory()
    platform_info = platform.uname()

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
        except subprocess.CalledProcessError:
            hardware_info["distro"] = "Windows"

    disk_info = psutil.disk_usage('/')
    if hardware_info["os"] == "Linux":
        disk_info = psutil.disk_usage('/home')
    hardware_info["disk_total"] = math.ceil(disk_info.total/(1000*1000*1000))
    hardware_info["disk_used"] = round(disk_info.used/(1000*1000*1000),1)
    hardware_info["disk_free"] = round(disk_info.free/(1000*1000*1000),1)
    hardware_info["cpu"] = get_cpu_name()
    gpu = get_gpu_name()
    if "Custom GPU 0405" in gpu:
        gpu = "AMD Custom GPU 0405"

    gpu = gpu.replace("Advanced Micro Devices, Inc. ", "")
    gpu = gpu.replace("[AMD/ATI] ", "")
    hardware_info["gpu"] = gpu
    hardware_info["app_version"] = app_version()
    return json.dumps(hardware_info)

@app.route('/app/exit')
def quit_app():
    ''' exit mukkuru '''
    os._exit(0)

@app.route('/library/launch/<app_id>')
def launch_app(app_id):
    '''launches an app using its appID'''
    games = get_games(True)
    game_path = games[app_id]["Exe"].strip('"')
    print(f'Launching game: {game_path} using {games[app_id]["LaunchOptions"]}')
    subprocess.run(f'"{game_path}" {games[app_id]["LaunchOptions"]}',
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=os.environ.copy(), shell=True, check=False)
    user_config = get_config(True)
    user_config["lastPlayed"] = app_id
    update_config(user_config)
    return "200"

def read_steam_username():
    ''' get username from steam files '''
    with open(mukkuru_env["steam"]["config.vdf"], "r", encoding="utf-8") as file:
        content = file.read()
        # Regex to match the structure under "Accounts"
        matches = re.findall(r'"Accounts"\s*{\s*"(.*?)"', content)
        if matches:
            return matches[0]  # Return the first found username
        print("No usernames found under 'Accounts'.")
        return None

def download_steam_avatar():
    ''' (if not exists) downloads steam avatar picture '''
    steam_username = read_steam_username()
    if steam_username is None:
        print("Unable to query avatar picture")
        return
    avatar_path = os.path.join(mukkuru_env["artwork"], "Avatar", steam_username+".jpg")
    if Path(avatar_path).is_file():
        print("Avatar image exists, skipping...")
        return
    r=requests.get(AVATAR_DOWNLOAD_URL.replace("[USERNAME]", steam_username), timeout=20)
    avatar_url = r.text
    if "http" in avatar_url:
        print("downloading steam user avatar image...")
        grid_db.download_file(avatar_url, avatar_path)
    else:
        print(f"Invalid avatar url: {avatar_url}")

def number_aware_scorer(s1, s2):
    '''give bad score to filenames with wrong number, to prevent game sequels confusions'''
    base_score = fuzz.token_set_ratio(s1, s2)  # Start with standard fuzzy score
    # Extract all numbers from both strings
    nums1 = set(re.findall(r'\d+', s1))
    nums2 = set(re.findall(r'\d+', s2))
    # Penalize if numbers don't match exactly
    if nums1 != nums2:
        base_score = max(base_score - 50, 0)  # Heavy penalty for number mismatches
    return base_score

def find_strict_number_match(game_title, image_files, threshold=80):
    ''' calculate a score for the game title, discard if under threshold '''
    match, score = process.extractOne(game_title, image_files, scorer=number_aware_scorer)
    # Reject if score is below threshold
    if score >= threshold:
        return match
    return None

def copy_file(source, destination):
    ''' copy a file from "source" to "destination" '''
    with open(source, 'rb') as src, open(destination,'wb') as dst:
        dst.write(src.read())


def fetch_artwork(game_title, app_id, platform_name, force_online = False):
    '''get apps artwork'''
    user_config = get_config(True)
    square_thumbnail_dir = f'ui/{user_config["theme"]}/thumbnails/'
    square_fetch_dir = os.path.join(mukkuru_env["artwork"],"Square")
    if not Path(square_fetch_dir).is_dir():
        os.mkdir(square_fetch_dir)
    if not Path(square_thumbnail_dir).is_dir():
        os.mkdir(square_thumbnail_dir)

    if force_online is False:
        image_files = glob.glob(os.path.join(square_fetch_dir, '*.jpg'))
        if len(image_files) == 0:
            match = None
        else:
            match =find_strict_number_match(grid_db.sanitize_filename_ascii(game_title),image_files)
    else:
        match = None
    if match is None:
        game_identifier = grid_db.GameIdentifier(game_title, app_id, platform_name) # pylint: disable=E1101
        filename = grid_db.download_square_image(game_identifier, square_fetch_dir)
        if filename is not False:
            if filename.endswith(".jpg"):
                print(f'downloaded {game_title} artwork from api')
                copy_file(filename, f'{square_thumbnail_dir}{app_id}.jpg')
            else:
                print(f'failed to download {game_title} artwork from api')
        return None
    #print(f'Found: {match} for {game_title}')
    copy_file(match, f'{square_thumbnail_dir}{app_id}.jpg')
    return match

def sha256_hash_file(filepath, chunk_size=8192):
    ''' get sha256 of file, processed as chunks to prevent memory overuse '''
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def clear_possible_mismatches(games):
    ''' clear artwork duplicates '''
    print("start artwork cleanup....")
    file_hashes = {}
    #square_path = os.path.join(mukkuru_env["artwork"],"Square")
    user_config = get_config(True)
    square_path = f'ui/{user_config["theme"]}/thumbnails/'
    user_config = get_config(True)
    #app_hashes = {}
    files = glob.glob(os.path.join(square_path, '*.jpg'))
    for file in files:
        file_hash = sha256_hash_file(file)
        file_hashes.setdefault(file_hash, []).append(file)
    for _, v in file_hashes.items():
        if len(v) > 1:
            for x in v:
                # Get appid
                #app_hashes.setdefault(k, []).append(os.path.splitext(os.path.basename(x))[0])
                app_id = os.path.splitext(os.path.basename(x))[0]
                app_name = games[app_id]["AppName"]
                src_image =  os.path.join(grid_db.sanitize_filename_ascii(app_name), ".jpg")
                games[app_id]["Thumbnail"] = False
                print(f"removing duplicated {x}")
                os.remove(x) # delete duplicated thumbnail
                if Path(src_image).is_file():
                    copy_file(src_image, f'ui/{user_config["theme"]}/thumbnails/{app_id}.jpg')
                else:
                    game_source = games[app_id]["Source"]
                    fetch_artwork(app_name, app_id, game_source, force_online=True)
    #if len(file_hashes) > 0:
    #    for k in app_hashes:
    return

@app.route('/favicon.ico')
def favicon():
    ''' favicon image '''
    return send_from_directory(f'{os.getcwd()}/ui/', 'favicon.ico')
@app.route('/store/<storefront>')
def open_store(storefront):
    ''' Launch the desired game storefront '''
    if storefront == "steam":
        subprocess.run(f'"{mukkuru_env["steam"]["launchPath"]}" steam://open/bigpicture',
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=os.environ.copy(), shell=True, check=False)
        time.sleep(3)
        subprocess.run(f'"{mukkuru_env["steam"]["launchPath"]}" steam://store',
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=os.environ.copy(), shell=True, check=False)
    elif storefront == "epic_games":
        print("Unimplemented store")
    else:
        print(f"unknown storefront {storefront}")

@app.route('/library/artwork/scan')
def scan_artwork(games = None):
    ''' scan for games artwork '''
    if games is None:
        games = get_games(True)
    for k in games.keys():
        if not Path(f"ui/SwitchUI/assets/thumbnail/{k}.jpg").is_file():
            game_source = games[k]["Source"]
            fetch_artwork(games[k]["AppName"], k, game_source)
        else:
            print(f"{k} already has artwork, skipping...")
    clear_possible_mismatches(games)
    scan_thumbnails(games)
    return "200"
@app.route('/localization')
def localize():
    ''' get a json with current selected language strings'''
    user_config = get_config(True)
    language = user_config["language"]
    with open(Path(f'ui/{user_config["theme"]}/translations.json'), encoding='utf-8') as f:
        localization = json.load(f)
        if language in localization:
            localization = localization[language]
            localization["available"] = True
            return localization
    localization = {"available" : False}
    return json.dumps(localization)

#This one must receive POST data
@app.route('/library/add')
def add_game():
    '''add a game manually'''
    #update_games(game_library)
    return "Not implemented"
def update_games(games):
    '''save game library'''
    with open(mukkuru_env["library.json"], 'w', encoding='utf-8') as f:
        json.dump(games, f)

@app.route('/library/get')
def get_games(raw = False):
    '''get game library as json'''
    try:
        with open(mukkuru_env["library.json"], encoding='utf-8') as f:
            games = json.load(f)
    except FileNotFoundError:
        games = {}
        update_games(games)
    if raw is False:
        return json.dumps(games)
    return games
@app.route('/config/get')
def get_config(raw = False):
    ''' get user configuration'''
    user_config = {
            "loop" : False,
            "skipNoArt" : False,
            "maxGamesInHomeScreen" : 12,
            "theme" : "SwitchUI",
            "librarySource" : 3, #0
            "darkMode" : False,
            "startupGameScan" : False,
            "12H" : True,
            "fullScreen" : False,
            "language" : "EN",
            "blacklist" : [],
            "favorite" : [],
            "lastPlayed" : ""
        }
    while "config.json" not in mukkuru_env:
        time.sleep(0.1)

    if not Path(mukkuru_env["config.json"]).is_file():
        print("No config.json")
        with open(mukkuru_env["config.json"], 'w', encoding='utf-8') as f:
            json.dump(user_config, f)
    with open(mukkuru_env["config.json"], encoding='utf-8') as f:
        configuration = json.load(f)
        for key, value in user_config.items():
            if key not in configuration:
                configuration[key] = value
            user_config = configuration
    if raw is False:
        return json.dumps(user_config)
    return user_config

@app.route('/config/set', methods = ['GET', 'POST', 'DELETE'])
def set_config():
    '''update user configuration from request'''        
    #print("setting configuration...")
    if request.method == 'POST':
        #print(request.get_json())
        user_config = request.get_json()
        update_config(user_config)
        return "200"
    if request.method == 'GET':
        return get_config()
    if request.method == 'DELETE':
        return "500"
    return "400"

def update_config(user_config):
    ''' update user configuration '''
    with open(mukkuru_env['config.json'] , 'w', encoding='utf-8') as f:
        json.dump(user_config, f)

@app.route('/ping')
def ping_request():
    '''reply with "pong", its purpose is making sure backend is running'''
    return "pong"

@app.route('/library/scan')
def scan_games():
    ''' scan for games, download artwork if available '''
    user_config = get_config(True)
    options = user_config["librarySource"]
    games = library_scan(int(options))
    #game_library.update(games)
    scan_artwork(games)
    for k, _ in games.items(): #games.keys
        if not Path(f'ui/{user_config["theme"]}/thumbnails/{k}.jpg').is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)
    return json.dumps(games)

@app.route('/log/<message>')
def log_message(message):
    ''' prints frontend messages in backend, useful for debugging '''
    print(f'[frontend] { base64.b64decode(message).decode("utf-8") }')
    return "200"

# To-do: allow custom specified username from userConfiguration
@app.route('/username')
def get_user():
    '''Get username'''
    username = read_steam_username()
    if username is None:
        return os.environ.get('USER', os.environ.get('USERNAME'))
    return username

@app.route('/frontend/')
def main_web():
    ''' homePage '''
    return static_file("index.html")

@app.route('/frontend/<path:path>')
def static_file(path):
    ''' serve asset '''
    if path == "assets/avatar.jpg":
        avatar_file = os.path.join(mukkuru_env["artwork"], "Avatar", f"{get_user()}.jpg")
        if Path(avatar_file).is_file():
            return send_from_directory(mukkuru_env["artwork"], f"Avatar/{get_user()}.jpg")
    user_config = get_config(True)
    return send_from_directory(f'{os.getcwd()}/ui/{user_config["theme"]}/', path)

def scan_thumbnails(games):
    '''update the thumbnail status for all games'''
    for k in games.keys():
        user_config = get_config(True)
        if not Path(f'ui/{user_config["theme"]}/thumbnails/{k}.jpg').is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)

@app.route('/config/fullscreen')
def is_fullscreen():
    ''' show whether app should be in fullscreen '''
    user_config = get_config(True)
    return user_config["fullScreen"]

def start_server():
    ''' init server '''
    app.run(host='localhost', port=49347, debug=True, use_reloader=False)

def main():
    ''' start of app execution '''
    mukkuru_env["steam"] = {}
    system = platform.system()
    if system == 'Windows':
        print("Running on Windows")
        # common_sdir = os.path.join("C:\\", "Program Files (x86)", "Steam")
        # User can alter ProgramFiles dir to a different folder
        program_files = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles")
        mukkuru_env["steam"]["path"] = os.path.join(program_files, "Steam")
        if not Path(mukkuru_env["steam"]["path"]).is_dir():
            print("Steam not in common path, reading registry as a failover...")
            vsk = r"SOFTWARE\WOW6432Node\Valve\Steam"
            mukkuru_env["steam"]["path"] = read_registry_value(0, vsk, "InstallPath")
        mukkuru_env["steam"]["shortcuts"] = os.path.join(mukkuru_env["steam"]["path"],
                                                         "userdata", "*", "config", "shortcuts.vdf")
        mukkuru_env["steam"]["libraryFile"] = os.path.join(mukkuru_env["steam"]["path"],
                                                           "steamapps", "libraryfolders.vdf")

        find_stuser = mukkuru_env["steam"]["shortcuts"].split('*')[0]
        steam_id = os.listdir(find_stuser)[0]
        mukkuru_env["steam"]["shortcuts"] = mukkuru_env["steam"]["shortcuts"].replace("*",
                                                                                      steam_id, 1)
        mukkuru_env["steam"]["launchPath"] = os.path.join(mukkuru_env["steam"]["path"], "Steam.exe")
        mukkuru_env["root"] = os.path.join(os.environ.get('APPDATA'), "Mukkuru")
    elif system == 'Linux':
        print("Running in Linux")
        # To-do: determine different steam installs
        mukkuru_env["steam"]["launchPath"] = "/usr/bin/steam"
        mukkuru_env["steam"]["path"] = os.path.expanduser("~/.local/share/Steam")
        mukkuru_env["steam"]["libraryFile"] = os.path.join(mukkuru_env["steam"]["path"],
                                                           "steamapps", "libraryfolders.vdf")
        mukkuru_env["steam"]["shortcuts"] = os.path.join(mukkuru_env["steam"]["path"],
                                                         "userdata", "*", "config", "shortcuts.vdf")
        mukkuru_env["root"] = os.path.join(os.path.expanduser("~"), ".config", "Mukkuru")
    elif system == 'Darwin':
        print('MacOS support is not yet implemented')
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
        os.mkdir(os.path.join(mukkuru_env["artwork"], "Avatar") )
    user_config = get_config(True)
    if not Path(mukkuru_env["library.json"]).is_file():
        print("No library.json")
    else:
        games = get_games(True)
        scan_thumbnails(games)
    if user_config["startupGameScan"] is True:
        print("[debug] startupGameScan: True, starting library scan")
        threading.Thread(target=scan_games).start()
    mukkuru_env["steam"]["gridPath"] = mukkuru_env["steam"]["shortcuts"].replace("shortcuts.vdf",
                                                                                 "grid", 1)
    mukkuru_env["steam"]["config.vdf"] = os.path.join(mukkuru_env["steam"]["path"],
                                                      "config", "config.vdf")
    download_steam_avatar()
    if threading.current_thread() is threading.main_thread():
        threading.Thread(target=start_server).start()
        #This might cause a race condition if your computer is slower than a snail
        time.sleep(2)
        Frontend(is_fullscreen(), app_version()).start()
    else:
        start_server()
if __name__ == "__main__":
    main()
