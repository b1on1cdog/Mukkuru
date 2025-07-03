# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
""" Mukkuru, cross-platform game launcher """
import os
#import glob
import json
from pathlib import Path
from functools import lru_cache
import stat
import subprocess
import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import hashlib
import logging
import platform
import shutil
from io import BytesIO

import qrcode
from waitress import serve
from waitress.server import create_server
from flask import Flask, request, jsonify
from flask import send_from_directory, send_file

from library import grid_db, video
from library.steam import get_non_steam_games, get_steam_games, get_steam_env
from library.steam import read_steam_username, download_steam_avatar
from library.steam import get_proton_list, get_proton_command

from library.egs import get_egs_games, read_heroic_username

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
wserver = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.CRITICAL)

mukkuru_env = {}

COMPILER_FLAG = False
APP_VERSION = "0.3.4"
BUILD_VERSION = None
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PORT = 49347
SERVER_PORT = 49351
sserver = create_server(wserver, host="0.0.0.0", port=SERVER_PORT)

@lru_cache(maxsize=1)
def app_version():
    ''' generate 6 MD5 digits to use as build number '''
    if COMPILER_FLAG is False:
        backend_log("Calculating build version at runtime....")
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
    if steam is not None:
        if options & option_steam:
            steam_games = get_steam_games(steam)
            games.update(steam_games)
        # Scan Non-Steam games
        if steam["shortcuts"] is not None and (options & option_nonsteam):
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
    themes = {}
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
            #themes.append(json.load(f))
            manifest = json.load(f)
            themes[Path(theme_manifest).parent.name] = manifest
    if raw is True:
        return themes
    return json.dumps(themes)

#@lru_cache(maxsize=1)
def get_theme(selected = None):
    ''' Return css of selected theme '''
    builtin_themes = ["Switch", "Switch 2", "PS5"]
    config = get_config(True)
    if selected is None:
        selected = config["theme"]

    sys_themes_dir = os.path.join(f'{APP_DIR}/ui/{config["interface"]}', "assets", "css")
    default_theme_dir = os.path.join(sys_themes_dir, "style.css")
    default_css = Path(default_theme_dir).read_text(encoding='utf-8')
    # Not a user theme
    if selected in builtin_themes:
        backend_log(f"using built-in theme {selected}")
        css = default_css
        if selected == "PS5":
            css = css + Path(os.path.join(sys_themes_dir, "ps5.css")).read_text(encoding='utf-8')
        elif selected == "Switch 2":
            css = css + Path(os.path.join(sys_themes_dir, "sw2.css")).read_text(encoding='utf-8')
        return css
    backend_log(f"loading user theme {selected}")
    themes_dir = os.path.join(mukkuru_env["root"], "themes")
    themes = get_themes(True)
    theme = themes[selected]
    css = ""
    if theme["style_overwrite"] is False:
        css = default_css

    for markup in theme["markup_files"]:
        markup_path = os.path.join(themes_dir,selected,markup)
        if Path(markup_path).is_file():
            css = css + Path(markup_path).read_text(encoding='utf-8')
        else:
            backend_log(f"Skipping {markup} markup since it does not exists")
    if css == '':
        backend_log("Unable to load theme, returning default")
        css = default_css
    return css


@app.route("/hardware/network")
def connection_status():#segmentation fault
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
    if FRONTEND_MODE == "WEF":
        terminate_wef()
    if os.environ.get("XDG_SESSION_DESKTOP", "").lower() == "gamescope":
        proc_flags = ["flatpak"]
        proc_flags.extend(["kill","org.mozilla.firefox"])
        subprocess.run(proc_flags, check=False)
    os._exit(0)

@app.route('/library/proton')
def get_proton():
    ''' list proton builds http '''
    return jsonify(get_proton_list())

@app.route('/library/launch/<app_id>')
def launch_app(app_id):
    '''launches an app using its appID'''
    games = get_games(True)
    game_path = games[app_id]["Exe"].strip('"')
    backend_log(f'Launching game: {game_path} using {games[app_id]["LaunchOptions"]}')
    if "flatpak" in game_path:
        pass
    else:
        game_path = f'"{game_path}"'
    launch_command = f'{game_path} {games[app_id]["LaunchOptions"]}'
    if '%command%' in games[app_id]["LaunchOptions"]:
        launch_command = games[app_id]["LaunchOptions"].replace('%command', game_path)
    # Linux cannot run exe without a compatibility layer
    if platform.system() == "Linux" and game_path.strip('"').endswith(".exe"):
        launch_command = get_proton_command(app_id, launch_command, get_config(True))
    backend_log(f"using {launch_command}")
    subprocess.run(launch_command,
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=os.environ.copy(), shell=True, check=False)
    user_config = get_config(True)
    if user_config["lastPlayed"] != app_id:
        user_config["lastPlayed"] = app_id
        update_config(user_config)
    os.environ.pop("STEAM_COMPAT_DATA_PATH", None)
    os.environ.pop("STEAM_COMPAT_CLIENT_INSTALL_PATH", None)
    return "200"

def copy_file(source, destination):
    ''' copy a file from "source" to "destination" '''
    with open(source, 'rb') as src, open(destination,'wb') as dst:
        dst.write(src.read())

def sha256_hash_file(filepath, chunk_size=8192):
    ''' get sha256 of file, processed as chunks to prevent memory overuse '''
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

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

def fetch_artwork(app_id, game, b1, b2, b3):
    ''' handle artwork '''
    thumbnail = os.path.join(mukkuru_env["root"], "thumbnails", f'{app_id}.jpg')
    game_source = game["Source"]
    game_identifier = grid_db.GameIdentifier(game["AppName"], app_id, game_source)
    if not Path(thumbnail).is_file() and app_id not in b1:
        if grid_db.download_image(game_identifier, thumbnail,"1:1") == "Missing":
            b1.append(app_id)
    hero = os.path.join(mukkuru_env["root"], "hero", f'{app_id}.png')
    if not Path(hero).is_file() and app_id not in b2:
        if grid_db.download_image(game_identifier, hero, "hero") == "Missing":
            b2.append(app_id)
    logo = os.path.join(mukkuru_env["root"], "logo", f'{app_id}.png')
    if not Path(logo).is_file() and app_id not in b3:
        if grid_db.download_image(game_identifier, logo,"logo") == "Missing":
            b3.append(app_id)
    result = {}
    result["1"] = b1
    result["2"] = b2
    result["3"] = b3
    return result

@app.route('/library/artwork/scan')
def scan_artwork(games = None):
    ''' scan for games artwork '''
    backend_log("scanning for new artwork..")
    config = get_config(True)
    blacklist1 = config["boxartBlacklist"]
    blacklist2 = config["heroBlacklist"]
    blacklist3 = config["logoBlacklist"]
    if games is None:
        games = get_games(True)
    results = {}
    counter = 0
    with ThreadPoolExecutor(max_workers=config["cores"]*2) as executor:
        future_to_key = {
            executor.submit(fetch_artwork, k, v, blacklist1, blacklist2, blacklist3): k
            for k, v in games.items()
        }
        for future in as_completed(future_to_key):
            k = future_to_key[future]
            try:
                results[k] = future.result()
                blacklist1.extend(results[k]["0"])
                blacklist2.extend(results[k]["1"])
                blacklist3.extend(results[k]["2"])
                counter = counter +1
                if counter % 12 == 0:
                    scan_thumbnails(games)
            except (KeyError, OSError, IndexError, FileNotFoundError) as e:
                results[k] = {"error": str(e)}
    config["boxartBlacklist"] = blacklist1
    config["heroBlacklist"] = blacklist2
    config["logoBlacklist"] = blacklist3
    update_config(config)
    #clear_possible_mismatches(games)
    scan_thumbnails(games)
    return "200"

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

@wserver.route('/localization')
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

@app.route('/media/get')
def get_media():
    ''' Get all Multimedia '''
    media = {}
    backend_log("fetching media...")
    user_config = get_config(True)
    video_manifest = mukkuru_env["video.json"]
    media["videos"] = video.get_videos(user_config["videoSources"], video_manifest)
    return json.dumps(media)

@app.route('/video/set', methods = ['POST'])
def set_videos():
    '''update videos json from request'''        
    if request.method == 'POST':
        videos = request.get_json()
        video.update_videos(mukkuru_env["video.json"], videos)
        return "200"
    return "400"

@app.route('/video/thumbnail/<video_id>', methods = ['POST'])
def set_video_thumbnail(video_id):
    '''update video thumbnail from request'''        
    if request.method == 'POST':
        thumbnail = request.get_json()
        video.update_thumbnail(mukkuru_env["video.json"], video_id, thumbnail)
        return "200"
    return "400"

@lru_cache(maxsize=2)
def get_config(raw = False):
    ''' get user configuration'''
    user_config = {
            "loop" : False,
            "skipNoArt" : False,
            "maxGamesInHomeScreen" : 12,
            "interface" : "LuntheraUI",
            "enableServer" : False,
            "autoPlayMedia" : False,
            "videoSources" : [os.path.join(mukkuru_env["root"], "video")],
            "musicSources" : [os.path.join(mukkuru_env["root"], "music")],
            "pictureSources" : [os.path.join(mukkuru_env["root"], "pictures")],
            "protonConfig" : {},
            "librarySource" : 3,
            "darkMode" : False,
            "startupGameScan" : False,
            "safeMode" : False,
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
        backend_log("No config.json")
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

@app.route('/themes/get')
def get_user_themes():
    ''' get_themes() http controller, returns a json '''
    return get_themes()

@app.route('/theme/<theme_id>/<asset>')
def get_theme_asset(theme_id, asset):
    ''' get the asset of a user theme '''
    theme_dir = os.path.join(mukkuru_env["root"], "themes", theme_id)
    backend_log(f"getting theme {theme_id} {asset}")
    return send_from_directory(theme_dir, asset)

@app.route('/config/get')
def get_user_configuration():
    ''' get_config() http controller, returns a json '''
    return get_config()

@app.route('/config/set', methods = ['GET', 'POST', 'DELETE'])
def set_config():
    '''update user configuration from request'''        
    if request.method == 'POST':
        user_config = request.get_json()
        update_config(user_config)
        return "200"
    if request.method == 'GET':
        return get_config()
    if request.method == 'DELETE':
        return "500"
    return "400"

@app.route('/app/restart')
def restart_app():
    ''' restarts app '''
    if COMPILER_FLAG:
        os.execv(sys.argv[0], sys.argv)
    else:
        os.execv(sys.executable, [sys.executable] + sys.argv)

def terminate_wef():
    ''' closes wef_bundle'''
    wef_bundle = os.path.join(mukkuru_env["root"], "wef_bundle", "wef_bundle")
    if platform.system() == "Windows":
        wef_bundle = wef_bundle+".exe"
    hardware_if.kill_executable_by_path(wef_bundle)

@app.route('/clear/<selection>', methods = ['POST'])
def delete_data(selection):
    ''' deletes app data '''
    backend_log(f"deleting data {selection}")
    tn_folder = os.path.join(mukkuru_env["root"], "thumbnails")
    logo_folder = os.path.join(mukkuru_env["root"], "logo")
    hero_folder = os.path.join(mukkuru_env["root"], "hero")
    if selection == "art":
        shutil.rmtree(tn_folder)
        os.mkdir(tn_folder)
        shutil.rmtree(logo_folder)
        os.mkdir(logo_folder)
        shutil.rmtree(hero_folder)
        os.mkdir(hero_folder)
    elif selection == "wef":
        terminate_wef()
        shutil.rmtree(os.path.join(mukkuru_env["root"], "wef_bundle"))
    elif selection == "all":
        if FRONTEND_MODE == "WEF":
            terminate_wef()
        try:
            shutil.rmtree(mukkuru_env["root"])
        except (OSError, FileNotFoundError, PermissionError):
            pass
        backend_log("deleted Mukkuru data folder, quitting....")
        quit_app()
    else:
        pass
    return "200"

def update_config(user_config):
    ''' update user configuration '''
    # clear cached config as the value was updated
    get_config.cache_clear()
    with open(mukkuru_env['config.json'] , 'w', encoding='utf-8') as f:
        json.dump(user_config, f)

@app.route('/alive')
def ping_request():
    '''reply with "ok", its purpose is making sure backend is running'''
    return get_alive_status(), 200

@app.route('/library/scan')
def scan_games():
    ''' scan for games, download artwork if available '''
    user_config = get_config(True)
    options = user_config["librarySource"]
    games = library_scan(int(options))
    #game_library.update(games)
    threading.Thread(target=scan_artwork, args=(games,)).start()
    time.sleep(8)
    for k, _ in games.items(): #games.keys
        thumbnail_path = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}.jpg')
        if not Path(thumbnail_path).is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)
    return json.dumps(games)

def backend_log(message):
    ''' print message and save to file '''
    print(message)
    if "log" in mukkuru_env:
        with open(mukkuru_env["log"], 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")

@wserver.route('/log/<message>')
@app.route('/log/<message>')
def log_message(message):
    ''' prints frontend messages in backend, useful for debugging '''
    msg = base64.b64decode(message).decode("utf-8")
    msg = f"[frontend] {msg}"
    backend_log(msg)
    return "200"

# To-do: allow custom specified username from userConfiguration
@app.route('/username')
def get_user():
    ''' Gets username '''
    return get_username()

@lru_cache(maxsize=1)
def get_username():
    '''Get username'''
    failover_user = os.environ.get('USER', os.environ.get('USERNAME'))
    steam = get_steam_env()
    if steam is None:
        heroic_user = read_heroic_username()
        if heroic_user is None:
            return failover_user

    username = read_steam_username(steam["config.vdf"])
    if username is None:
        return failover_user
    return username

@app.route('/frontend/')
def main_web():
    ''' homePage '''
    return static_file("index.html")

@app.route('/')
def main_uri():
    ''' redirect to homepage '''
    return app.redirect(location=f'http://localhost:{APP_PORT}/frontend/')

@wserver.route('/<path:path>')
def server_file(path):
    ''' returns dashboard static files '''
    user_config = get_config(True)
    serve_path = os.path.join(APP_DIR, "ui", user_config["interface"])
    return send_from_directory(serve_path, path)

@wserver.route('/upload', methods=['POST'])
def upload():
    ''' receive files as chunks from dashboard uploads '''
    file = request.files['chunk']
    filename = request.form['filename']
    chunk_index = int(request.form['chunkIndex'])
    chunk_size = int(request.form['chunkSize'])
    total_chunks = int(request.form['totalChunks'])

    video_files = ["mp4", "m4v"]
    image_files = ["png", "jpg", "webm"]
    music_files = ["mp3", "m4a"]
    #allowed_files = []
    # To-do: allow user to store these files in another drive
    # To-do: allow users to move and/or store files in OS user folder
    # To-do: restrict what file formats can be received
    cmd = None
    alt_cmd = None
    value = None
    file_extension = Path(filename).suffix.replace(".", "")
    user_config = get_config(True)
    if file_extension in video_files:
        upload_folder = user_config["videoSources"][0]
        cmd = "playVideo"
        alt_cmd = "reloadVideos"
        value = f"video/0/{filename}"
    elif file_extension in image_files:
        upload_folder = os.path.join(mukkuru_env["root"], "pictures")
        cmd = "openPicture"
        alt_cmd = "reloadPictures"
        value = f"pictures/0/{filename}"
    elif file_extension in music_files:
        upload_folder = os.path.join(mukkuru_env["root"], "music")
        cmd = "playAudio"
        alt_cmd = "reloadAudios"
        value = f"music/0/{filename}"
    else:
        upload_folder = os.path.join(mukkuru_env["root"], "miscellaneous")

    save_path = os.path.join(upload_folder, filename)
    os.makedirs(upload_folder, exist_ok=True)

    if chunk_index == 0:
        backend_log(f"downloading {filename}")
        if Path(save_path).exists():
            os.remove(save_path)

    with open(save_path, 'ab') as f:
        f.seek(chunk_index * chunk_size)
        f.write(file.read())
    if (chunk_index + 1) == total_chunks and cmd is not None:
        user_config = get_config(True)
        status = {}
        if user_config["autoPlayMedia"]:
            status["command"] = cmd
        else:
            status["command"] = alt_cmd
        status["value"] = value
        set_alive_status(status)
    return 'Chunk received', 200

@wserver.route('/')
@wserver.route('/index.html')
def server_main():
    ''' returns main dashboard page'''
    user_config = get_config(True)
    serve_path = os.path.join(APP_DIR, "ui", user_config["interface"])
    return send_from_directory(serve_path, "dashboard.html")

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
        else:
            return send_from_directory(serve_path, os.path.join("assets","avatar_man.png"))
    if path.startswith("assets/audio/"):
        audio_file = path.replace("assets/audio/", "")
        new_path = f'assets/audio/{user_config["uiSounds"]}/{audio_file}'
        return send_from_directory(serve_path, new_path)
    if path.startswith("thumbnails/") or path.startswith("hero/"):
        return send_from_directory(mukkuru_env["root"], path, mimetype='image/jpeg')
    if path.endswith("theme.css"):
        full_path = os.path.join(serve_path, path)
        theme = get_theme(user_config["theme"])
        css = CssPreprocessor(full_path, data=theme)
        css.process()
        return send_file(css.data(), mimetype="text/css")
    if path.endswith("web/qrcode"):
        #code = 123456
        ip = hardware_if.get_current_interface(get_ip = True)
       # img = qrcode.make(f'http://{ip}:{SERVER_PORT}/code/{code}')
        img = qrcode.make(f'http://{ip}:{SERVER_PORT}')
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
   # if path.startswith("video/"):
   #     video_path = os.path.join(mukkuru_env["root"], "video")
    #    video_file = path.replace("video/", "")
    #    return send_from_directory(video_path, video_file)
  #  print(f"path -> {path}")
    return send_from_directory(serve_path, path)

@app.route('/frontend/video/<source>/<filename>')
def video_serve(source, filename):
    '''serve video files'''
    user_config = get_config(True)
    video_path = user_config["videoSources"][int(source)]
    return send_from_directory(video_path, filename)

@app.route('/frontend/music/<source>/<filename>')
def music_serve(source, filename):
    '''serve music files'''
    user_config = get_config(True)
    music_path = user_config["musicSources"][int(source)]
    return send_from_directory(music_path, filename)

@app.route('/frontend/picture/<source>/<filename>')
def picture_serve(source, filename):
    '''serve music files'''
    user_config = get_config(True)
    pic_path = user_config["pictureSources"][int(source)]
    return send_from_directory(pic_path, filename)

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


@app.route('/server/<action>', methods = ['POST', 'GET'])
def init_server(action):
    ''' http controller for wserver start '''
    global sserver #pylint: disable=W0603
    if action == "start":
        threading.Thread(target=start_app, args=(True,)).start()
        return hardware_if.get_current_interface(get_ip=True), 200
    if action == "info":
        if "SERVER_RUNNING" in os.environ:
            ip = hardware_if.get_current_interface(get_ip=True)
            url = f'http://{ip}:{SERVER_PORT}'
            return url, 200
        loc = get_localization(True)
        return loc.get("OfflineServer", "Server: Offline"), 222
    else:
        sserver.close()
        os.environ.pop('SERVER_RUNNING', None)
        sserver = create_server(wserver, host="0.0.0.0", port=SERVER_PORT)
    return "200"

def start_app(is_server = False):
    ''' init server '''
    try:
        user_config = get_config(True)
        cores = user_config["cores"]
        if is_server:
            sserver.adj.core_count = cores
            os.environ["SERVER_RUNNING"] = "1"
            print("starting server....")
            sserver.run()
            #serve(wserver, host="0.0.0.0", threads=cores, port=SERVER_PORT)
        else:
            serve(app, host="localhost", threads=cores, port=APP_PORT)
    except ConnectionResetError:
        if not is_server:
            quit_app()

def close_update(m = None):
    ''' called when update is completed or aborted '''
    update_file = os.path.join(mukkuru_env["update"], "update")
    if platform.system() == "Windows":
        update_file = update_file + ".exe"
    if Path(update_file).resolve() == Path(sys.executable).resolve():
        #We are running from update itself, we cannot delete the update here
        e_path = None
        if "MUKK_EXECUTABLE" in os.environ:
            e_path = os.environ["MUKK_EXECUTABLE"]
        if m is not None and "executable" in "m":
            e_path = m["executable"]
        if e_path is not None:
            subprocess.Popen([e_path])
        os._exit(0)
    shutil.rmtree(mukkuru_env["update"])
    return

def process_update():
    '''We have an update we need to handle'''
    update_manifest = os.path.join(mukkuru_env["update"], "update.json")
    if not Path(update_manifest).is_file():
        # We cannot proceed without a manifest, aborting
        return close_update()
    update_file = os.path.join(mukkuru_env["update"], "update")
    if platform.system() == "Windows":
        update_file = update_file + ".exe"
    with open(update_manifest, encoding='utf-8', mode='r') as manifest_file:
        manifest = json.loads(manifest_file)
        if not "version" in manifest:
            # Bad update, aborting
            return close_update(manifest)
        if manifest["version"] == APP_VERSION:
            # already updated
            shutil.rmtree(mukkuru_env["update"])
            return close_update(manifest)
        executable = manifest["executable"]
        shutil.copy(update_file, executable)
        if platform.system() != "Windows":
            current_permissions = os.stat(executable).st_mode
            os.chmod(manifest["executable"], current_permissions | stat.S_IXUSR)
        close_update(manifest)

def get_alive_status():
    ''' get alive status'''
    default = {"Status": "OK" }
    response = mukkuru_env["alive"]
    if response != default:
        set_alive_status(default)
    return response

def set_alive_status(value):
    ''' set alive status, this will be periodically read from frontend '''
    mukkuru_env["alive"] = value

def main():
    ''' start of app execution '''
    system = platform.system()
    backend_log(f"Running on {system}")
    backend_log(f'Using { FRONTEND_MODE } for rendering')
    if system == 'Windows':
        mukkuru_env["root"] = os.path.join(os.environ.get('APPDATA'), "Mukkuru")
    elif system == 'Linux':
        mukkuru_env["root"] = os.path.join(os.path.expanduser("~"), ".config", "Mukkuru")
    elif system == 'Darwin':
        mukkuru_env["root"] = os.path.join(os.path.expanduser("~"), ".config", "Mukkuru")
    else:
        backend_log("Running in unsupported OS")
    mukkuru_env["library.json"] = os.path.join(mukkuru_env["root"], "library.json")
    mukkuru_env["config.json"] = os.path.join(mukkuru_env["root"], "config.json")
    mukkuru_env["video.json"] = os.path.join(mukkuru_env["root"], "video.json")
    mukkuru_env["artwork"] = os.path.join(mukkuru_env["root"], "artwork")
    mukkuru_env["log"] = os.path.join(mukkuru_env["root"], "mukkuru.log")
    mukkuru_env["app_path"] = APP_DIR
    mukkuru_env["update"] = os.path.join(mukkuru_env["root"], "update")
    # Instead of writing another executable, this one will conditionally
    # act as the updater
    if Path(mukkuru_env["update"]).is_dir():
        process_update()

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
        os.path.join(mukkuru_env["root"], "plugins"),
    ]

    set_alive_status({"Status": "OK" })

    for needed_dir in needed_dirs:
        if not os.path.isdir(needed_dir):
            os.mkdir(needed_dir)

    user_config = get_config(True)
    if not Path(mukkuru_env["library.json"]).is_file():
        backend_log("No library.json")
    else:
        games = get_games(True)
        scan_thumbnails(games)
    if user_config["startupGameScan"] is True:
        backend_log("[debug] startupGameScan: True, starting library scan")
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
            threading.Thread(target=start_app).start()
            time.sleep(2)
            if os.environ.get("XDG_SESSION_DESKTOP", "").lower() == "gamescope":
                mukkuru_url = 'http://localhost:49347/frontend/frame.html'
                proc_flags = []
                proc_flags.extend(["flatpak", "run", "org.mozilla.firefox"])
                proc_flags.append("--kiosk")
                proc_flags.append("-private-window")
                proc_flags.append(mukkuru_url)
                subprocess.run(proc_flags, check=False)
            else:
                Frontend(is_fullscreen(), app_version(), mukkuru_env).start()

    else:
        start_app()
if __name__ == "__main__":
    main()
