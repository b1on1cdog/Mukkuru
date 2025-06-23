# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
""" Mukkuru, cross-platform game launcher """
import os
import glob
import json
from pathlib import Path
from functools import lru_cache
import subprocess
import base64
import threading
import time

import sys
import hashlib
import logging
import platform

from waitress import serve
from flask import Flask, request
from flask import send_from_directory, send_file

from library import grid_db
from library.steam import get_non_steam_games, get_steam_games, get_steam_env
from library.steam import read_steam_username, download_steam_avatar

from utils import hardware_if
from utils.css_preprocessor import CssPreprocessor

FRONTEND_MODE = "PYWEBVIEW"

if FRONTEND_MODE == "PYWEBVIEW":
    from view.pywebview import Frontend
elif FRONTEND_MODE == "WEF":
    from view.wef_view import Frontend
elif FRONTEND_MODE == "FLASKUI":
    from flaskwebgui import FlaskUI as Frontend, close_application
    # Darwin, Windows, Linux: Chrome, Brave, Edge
    # Linux: Chromium
else:
    print("FATAL: Unknown webview, unable to produce interface")
    os._exit(0)

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.CRITICAL)

mukkuru_env = {}

COMPILER_FLAG = False
APP_VERSION = "0.2.16"
BUILD_VERSION = None
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PORT = 49347

@lru_cache(maxsize=1)
def app_version():
    ''' generate 6 MD5 digits to use as build number '''
    if COMPILER_FLAG is False:
        print("Calculating build version at runtime....")
        path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        hasher = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        full_md5 = hasher.hexdigest()
        build_version = full_md5[-6:]
    else:
        build_version = BUILD_VERSION
    return f"Mukkuru v{APP_VERSION} build-{build_version}"

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
    return games

def library_scan(options):
    '''
    Scan library for games
    1 - Steam
    2 - Non-Steam
    4 - EGS
    '''
    option_steam = 1 << 0  # 0001 = 1
    option_nonsteam = 1 << 1  # 0010 = 2
    option_egs = 1 << 2  # 0100 = 4

    steam = get_steam_env()

    games = {}
    if options & option_steam:
        steam_games = get_steam_games(steam)
        games.update(steam_games)
    # Scan Non-Steam games
    if options & option_nonsteam:
        non_steam_games = get_non_steam_games(steam)
        games.update(non_steam_games)
    if options & option_egs:
        egs_games = get_egs_games()
        games.update(egs_games)
    return games

def has_required_keys(json_data, required):
    ''' Returns whether json has required keys '''
    return set(required.keys()).issubset(json_data)

def is_valid_json(filepath, template = None):
    ''' Returns True if JSON is valid, otherwise returns False '''
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if template is not None:
                return has_required_keys(data, required=template)
        return True
    except (json.JSONDecodeError, OSError):
        return False

def get_themes(raw = False):
    ''' Return a list of themes '''
    themes_dir = os.path.join(mukkuru_env["root"], "themes")
    theme_manifests = []
    themes = []
    required = {
        "name" : "",
        "author" : "",
        "theme_version" : "",
        "markup_files" : [],
        "style_overwrite" : False,
        "banner" : ""
    }
    for theme_dir in os.listdir(themes_dir):
        theme_manifest = os.path.join(themes_dir, theme_dir, "manifest.json")
        if Path(theme_manifest).is_file() and is_valid_json(theme_manifest, template=required):
            theme_manifests.append(theme_manifest)
    for theme_manifest in theme_manifests:
        with open(theme_manifest, 'r', encoding='utf-8') as f:
            themes.append(json.load(f))
    if raw is True:
        return themes
    return json.dumps(themes)

@app.route("/hardware/network")
def connection_status():
    ''' returns a json with connection status'''
    status = hardware_if.connection_status()
    return json.dumps(status)
@app.route("/hardware/battery")
def battery_info():
    ''' Return a JSON containing battery details '''
    response = json.dumps(hardware_if.get_battery())
    return response

@app.route("/hardware")
def harware_info():
    ''' get hardware info as a json '''
    hardware_info = hardware_if.get_info()
    hardware_info["app_version"] = app_version()
    return json.dumps(hardware_info)

@app.route('/app/exit')
def quit_app():
    ''' exit mukkuru '''
    if FRONTEND_MODE == "FLASKUI":
        close_application() # pylint: disable=E0606, E0601
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
    if user_config["lastPlayed"] != app_id:
        user_config["lastPlayed"] = app_id
        update_config(user_config)
    return "200"

def copy_file(source, destination):
    ''' copy a file from "source" to "destination" '''
    with open(source, 'rb') as src, open(destination,'wb') as dst:
        dst.write(src.read())


def fetch_artwork(game_title, app_id, platform_name):
    '''get apps artwork'''
    square_thumbnail_dir = os.path.join(mukkuru_env["root"], "thumbnails")
    square_fetch_dir = os.path.join(mukkuru_env["artwork"],"Square")
    if not Path(square_fetch_dir).is_dir():
        os.mkdir(square_fetch_dir)
    if not Path(square_thumbnail_dir).is_dir():
        os.mkdir(square_thumbnail_dir)

    match = None
    if match is None:
        game_identifier = grid_db.GameIdentifier(game_title, app_id, platform_name)
        if game_identifier.platform != "non-steam":
            output_file = output_file = os.path.join(square_thumbnail_dir, f'{app_id}.jpg')
        else:
            output_file = square_fetch_dir
        filename = grid_db.download_image(game_identifier, output_file, "1:1")
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
    square_path = os.path.join(mukkuru_env["artwork"],"Square")
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
                    thumbnail_path= os.path.join(mukkuru_env["root"], "thumbnails", f'{app_id}.jpg')
                    copy_file(src_image, thumbnail_path)
                else:
                    game_source = games[app_id]["Source"]
                    fetch_artwork(app_name, app_id, game_source)
    #if len(file_hashes) > 0:
    #    for k in app_hashes:
    return

@app.route('/favicon.ico')
def favicon():
    ''' favicon image '''
    return send_from_directory(os.path.join(APP_DIR, "ui"), 'mukkuru.ico')
@app.route('/store/<storefront>')
def open_store(storefront):
    ''' Launch the desired game storefront '''
    steam = get_steam_env()
    if storefront == "steam":
        subprocess.run(f'"{steam["launchPath"]}" steam://open/bigpicture',
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=os.environ.copy(), shell=True, check=False)
        time.sleep(3)
        subprocess.run(f'"{steam["launchPath"]}" steam://store',
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
    config = get_config(True)
    blacklist1 = config["boxartBlacklist"]
    blacklist2 = config["heroBlacklist"]
    blacklist3 = config["logoBlacklist"]
    if games is None:
        games = get_games(True)
    for k in games.keys():
        thumbnail = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}.jpg')
        game_source = games[k]["Source"]
        game_identifier = grid_db.GameIdentifier(games[k]["AppName"], k, game_source)
        if not Path(thumbnail).is_file() and k not in blacklist1:
            if grid_db.download_image(game_identifier, thumbnail,"1:1") == "Missing":
                blacklist1.append(k)
        hero = os.path.join(mukkuru_env["root"], "hero", f'{k}.png')
        if not Path(hero).is_file() and k not in blacklist2:
            if grid_db.download_image(game_identifier, hero, "hero") == "Missing":
                blacklist2.append(k)
        logo = os.path.join(mukkuru_env["root"], "logo", f'{k}.png')
        if not Path(logo).is_file() and k not in blacklist3:
            if grid_db.download_image(game_identifier, logo,"logo") == "Missing":
                blacklist3.append(k)
    config["boxartBlacklist"] = blacklist1
    config["heroBlacklist"] = blacklist2
    config["logoBlacklist"] = blacklist3
    update_config(config)
    #clear_possible_mismatches(games)
    scan_thumbnails(games)
    return "200"

@lru_cache(maxsize=1)
def get_localization(raw = False):
    ''' Returns a localization dictionary '''
    user_config = get_config(True)
    language = user_config["language"]
    loc_path = f'{APP_DIR}/ui/{user_config["interface"]}/translations.json'
    with open(Path(loc_path),encoding='utf-8') as f:
        localization = json.load(f)
        if language in localization:
            localization = localization[language]
            localization["available"] = True
            return localization
    localization = {"available" : False}
    if raw is True:
        return localization
    return json.dumps(localization)

@app.route('/localization')
def localize():
    ''' get a json with current selected language strings'''
    return get_localization()

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

@lru_cache(maxsize=2)
def get_config(raw = False):
    ''' get user configuration'''
    user_config = {
            "loop" : False,
            "skipNoArt" : False,
            "maxGamesInHomeScreen" : 12,
            "interface" : "LuntheraUI",
            "librarySource" : 3, #0
            "darkMode" : False,
            "startupGameScan" : False,
            "12H" : True,
            "fullScreen" : False,
            "language" : "EN",
            "blacklist" : [],
            "favorite" : [],
            "lastPlayed" : "",
            "showKeyGuide" : True,
            "theme" : "Switch",
            "cores" : 6,
            "alwaysShowBottomBar" : True,
            "uiSounds" : "Switch",
            "boxartBlacklist" : [],
            "logoBlacklist" : [],
            "heroBlacklist" : [],
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

@app.route('/config/get')
def get_user_configuration():
    ''' get_config() http controller, returns a json '''
    return get_config()

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
    # clear cached config as the value was updated
    get_config.cache_clear()
    with open(mukkuru_env['config.json'] , 'w', encoding='utf-8') as f:
        json.dump(user_config, f)

@app.route('/alive')
def ping_request():
    '''reply with "ok", its purpose is making sure backend is running'''
    return "ok", 200

@app.route('/library/scan')
def scan_games():
    ''' scan for games, download artwork if available '''
    user_config = get_config(True)
    options = user_config["librarySource"]
    games = library_scan(int(options))
    #game_library.update(games)
    scan_artwork(games)
    for k, _ in games.items(): #games.keys
        thumbnail_path = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}.jpg')
        if not Path(thumbnail_path).is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)
    return json.dumps(games)

@app.route('/log/<message>')
def log_message(message):
    ''' prints frontend messages in backend, useful for debugging '''
    msg = base64.b64decode(message).decode("utf-8")
    print(f'[frontend] { msg }')
    with open(mukkuru_env["log"], 'a', encoding='utf-8') as f:
        f.write(f"{msg}\n")
    return "200"

# To-do: allow custom specified username from userConfiguration
@app.route('/username')
def get_user():
    '''Get username'''
    steam = get_steam_env()
    username = read_steam_username(steam["config.vdf"])
    if username is None:
        return os.environ.get('USER', os.environ.get('USERNAME'))
    return username

@app.route('/frontend/')
def main_web():
    ''' homePage '''
    return static_file("index.html")

@app.route('/')
def main_uri():
    ''' redirect to homepage '''
    return app.redirect(location=f'http://localhost:{APP_PORT}/frontend/')

@app.route('/frontend/<path:path>')
def static_file(path):
    ''' serve asset '''
    user_config = get_config(True)
    serve_path = os.path.join(APP_DIR, "ui", user_config["interface"])
    if path == "assets/avatar":
        avatar_file = os.path.join(mukkuru_env["artwork"], "Avatar", f"{get_user()}.jpg")
        avatar_png = os.path.join(mukkuru_env["artwork"], "Avatar", f"{get_user()}.png")
        if Path(avatar_file).is_file():
            return send_from_directory(mukkuru_env["artwork"], f"Avatar/{get_user()}.jpg")
        elif Path(avatar_png).is_file():
            return send_from_directory(mukkuru_env["artwork"], f"Avatar/{get_user()}.png")
    if path.startswith("assets/audio/"):
        audio_file = path.replace("assets/audio/", "")
        new_path = f'assets/audio/{user_config["uiSounds"]}/{audio_file}'
        return send_from_directory(serve_path, new_path)
    if path.startswith("thumbnails/") or path.startswith("hero/"):
        return send_from_directory(mukkuru_env["root"], path, mimetype='image/jpeg')
    if path.endswith(".css"):
        full_path = os.path.join(serve_path, path)
        css = CssPreprocessor(full_path)
        css.process()
        return send_file(css.data(), mimetype="text/css")
    return send_from_directory(serve_path, path)

def scan_thumbnails(games):
    '''update the thumbnail status for all games'''
    for k in games.keys():
        thumbnail_path = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}.jpg')
        if not Path(thumbnail_path).is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)

@app.route('/config/fullscreen')
def is_fullscreen():
    ''' show whether app should be in fullscreen '''
    user_config = get_config(True)
    return user_config["fullScreen"]

def kwserver(**server_kwargs):
    ''' start server using kwargs '''
    try:
        server = server_kwargs.pop("app", None)
        cores = get_config(True)["cores"]
        serve(server, host="localhost", threads=cores, port=APP_PORT)
    except ConnectionResetError:
        quit_app()

def start_server():
    ''' init server '''
    try:
        cores = get_config(True)["cores"]
        serve(app, host="localhost", threads=cores, port=APP_PORT)
    except ConnectionResetError:
        quit_app()
    #app.run(host='localhost', port=APP_PORT, debug=True, use_reloader=False)


def main():
    ''' start of app execution '''
    system = platform.system()
    print(f"Running on {system}")
    print(f'Using { FRONTEND_MODE } for rendering')
    if system == 'Windows':
        mukkuru_env["root"] = os.path.join(os.environ.get('APPDATA'), "Mukkuru")
    elif system == 'Linux':
        mukkuru_env["root"] = os.path.join(os.path.expanduser("~"), ".config", "Mukkuru")
    elif system == 'Darwin':
        mukkuru_env["root"] = os.path.join(os.path.expanduser("~"), ".config", "Mukkuru")
    else:
        print("Running in unsupported OS")
    mukkuru_env["library.json"] = os.path.join(mukkuru_env["root"], "library.json")
    mukkuru_env["config.json"] = os.path.join(mukkuru_env["root"], "config.json")
    mukkuru_env["artwork"] = os.path.join(mukkuru_env["root"], "artwork")
    mukkuru_env["log"] = os.path.join(mukkuru_env["root"], "mukkuru.log")
    mukkuru_env["app_path"] = APP_DIR

    needed_dirs = [
        mukkuru_env["root"],
        mukkuru_env["artwork"],
        os.path.join(mukkuru_env["artwork"], "Square"),
        os.path.join(mukkuru_env["artwork"], "Logo"),
        os.path.join(mukkuru_env["artwork"], "Heroes"),
        os.path.join(mukkuru_env["artwork"], "Grid"),
        os.path.join(mukkuru_env["artwork"], "Avatar"),
        os.path.join(mukkuru_env["root"], "logo"),
        os.path.join(mukkuru_env["root"], "thumbnails"),
        os.path.join(mukkuru_env["root"], "hero"),
        os.path.join(mukkuru_env["root"], "themes"),
    ]

    for needed_dir in needed_dirs:
        if not os.path.isdir(needed_dir):
            os.mkdir(needed_dir)

    user_config = get_config(True)
    if not Path(mukkuru_env["library.json"]).is_file():
        print("No library.json")
    else:
        games = get_games(True)
        scan_thumbnails(games)
    if user_config["startupGameScan"] is True:
        print("[debug] startupGameScan: True, starting library scan")
        threading.Thread(target=scan_games).start()
    download_steam_avatar(mukkuru_env["artwork"])
    if threading.current_thread() is threading.main_thread():
        if "flaskwebgui" in sys.modules:
            window_width = None
            window_height = None
            if not is_fullscreen():
                window_width = 1280
                window_height = 800
            Frontend(server=kwserver, server_kwargs={
            "app": app,
            "port": APP_PORT,
            "threaded": True,
            },
            on_shutdown=quit_app,
            fullscreen=is_fullscreen(),
            width=window_width,
            height=window_height
            ).run()
        else:
            threading.Thread(target=start_server).start()
            time.sleep(2)
            Frontend(is_fullscreen(), app_version(), mukkuru_env).start()

    else:
        start_server()
if __name__ == "__main__":
    main()
