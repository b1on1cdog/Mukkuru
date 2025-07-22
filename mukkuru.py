# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
""" Mukkuru, cross-platform game launcher """
#pylint: disable=C0413
import os
import json
from pathlib import Path
import subprocess
import base64
import threading
import time
import sys
import logging
import platform
import shutil
from io import BytesIO
import qrcode
from waitress import serve
from waitress.server import create_server
from flask import Flask, request, jsonify
from flask import send_from_directory, send_file

import utils.core as core
from utils import hardware_if, updater, test
from utils.css_preprocessor import CssPreprocessor
core.APP_DIR = os.path.dirname(os.path.abspath(__file__))
from utils.core import mukkuru_env, COMPILER_FLAG, FRONTEND_MODE
from utils.core import APP_PORT, SERVER_PORT, APP_DIR
from utils.core import app_version, get_config, backend_log, set_alive_status
from utils.core import update_config, format_executable
from utils.bootstrap import get_userprofile_folder

from library import video
from library.games import get_games, scan_games, scan_thumbnails, get_username, artwork_worker
from library.steam import get_steam_env, download_steam_avatar

from controller.license import license_controller
from controller.hardware import hardware_controller
from controller.library import library_controller, external_library
from controller.dashboard import dashboard_blueprint

if FRONTEND_MODE == "PYWEBVIEW":
    from view.pywebview import Frontend
elif FRONTEND_MODE == "WEF":
    from view.wef_view import Frontend
elif FRONTEND_MODE == "FLASKUI":
    from view.alternate_ui import Frontend
else:
    print("FATAL: Unknown webview, unable to produce interface")
    os._exit(0)

app = Flask(__name__)
app.register_blueprint(license_controller)
app.register_blueprint(hardware_controller)
app.register_blueprint(library_controller)
app.json.sort_keys = False


wserver = Flask(__name__)
wserver.json.sort_keys = False
wserver.register_blueprint(dashboard_blueprint)
wserver.register_blueprint(external_library)
log = logging.getLogger('werkzeug')
log.setLevel(logging.CRITICAL)

sserver = create_server(wserver, host="0.0.0.0", port=SERVER_PORT)

def is_valid_json(filepath, template = None):
    ''' Returns True if JSON is valid, otherwise returns False '''
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if template is not None:
                return set(template.keys()).issubset(data)
        return True
    except (json.JSONDecodeError, OSError):
        return False

def get_themes():
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
            manifest = json.load(f)
            themes[Path(theme_manifest).parent.name] = manifest
        return themes

def get_theme(selected = None):
    ''' Return css of selected theme '''
    builtin_themes = ["Switch", "Switch 2", "PS5"]
    config = get_config()
    if selected is None:
        selected = config["theme"]

    sys_themes_dir = os.path.join(f'{APP_DIR}/ui/', "assets", "css")
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
    themes = get_themes()
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

@app.route('/app/exit')
def quit_app():
    ''' exit mukkuru '''
    if FRONTEND_MODE == "FLASKUI":
        Frontend().close() # pylint: disable=E0606, E0601
    if FRONTEND_MODE == "WEF":
        terminate_wef()
    #if os.environ.get("XDG_SESSION_DESKTOP", "").lower() == "gamescope":
    os._exit(0)

@wserver.route('/favicon.ico')
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

def get_localization(raw = False):
    ''' Returns a localization dictionary '''
    user_config = get_config()
    language = user_config["language"]
    loc_path = f'{APP_DIR}/ui/translations.json'
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

@app.route('/video/set', methods = ['POST'])
def set_videos():
    '''update videos json from request'''
    if request.method == 'POST':
        videos = request.get_json()
        video.update_videos(mukkuru_env["video.json"], videos)
        return "200"
    return "400"

@app.route('/audios/get')
def get_audio_packs():
    ''' get audio pack'''
    audio_packs = []
    builtin_sfx = os.path.join(APP_DIR, "ui", "assets", "audio")
    user_sfx = os.path.join(mukkuru_env["root"], "sfx")
    audio_packs.extend(os.listdir(builtin_sfx))
    audio_packs.extend(os.listdir(user_sfx))
    return jsonify(audio_packs)

@app.route('/themes/get')
def get_user_themes():
    ''' get_themes() http controller, returns a json '''
    themes = get_themes()
    return jsonify(themes)

@app.route('/theme/<theme_id>/<asset>')
def get_theme_asset(theme_id, asset):
    ''' get the asset of a user theme '''
    theme_dir = os.path.join(mukkuru_env["root"], "themes", theme_id)
    backend_log(f"getting theme {theme_id} {asset}")
    return send_from_directory(theme_dir, asset)

@wserver.route('/config/get')
@app.route('/config/get')
def get_user_configuration():
    ''' get_config() http controller, returns a json '''
    return jsonify(get_config())

@app.route('/config/set', methods = ['GET', 'POST', 'DELETE'])
def set_config():
    '''update user configuration from request'''        
    if request.method == 'POST':
        user_config = request.get_json()
        update_config(user_config)
        return "200"
    if request.method == 'GET':
        return jsonify(get_config())
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
    wef_bundle = format_executable(wef_bundle)
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

@app.route('/alive')
def ping_request():
    '''reply with "ok", its purpose is making sure backend is running'''
    return get_alive_status(), 200

@wserver.route('/log/<message>')
@app.route('/log/<message>')
def log_message(message):
    ''' prints frontend messages in backend, useful for debugging '''
    msg = base64.b64decode(message).decode("utf-8")
    msg = f"[frontend] {msg}"
    backend_log(msg)
    return "200"

# To-do: allow custom specified username from userConfiguration
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
    user_config = get_config()
    serve_path = os.path.join(APP_DIR, "ui")
    if path == "store":
        return send_from_directory(serve_path, "store.html")
    if path == "settings":
        return send_from_directory(serve_path, "settings.html")
    if path == "assets/avatar":
        avatar_file = os.path.join(mukkuru_env["artwork"], "Avatar", f"{get_username()}.jpg")
        avatar_png = os.path.join(mukkuru_env["artwork"], "Avatar", f"{get_username()}.png")
        if Path(avatar_file).is_file():
            return send_from_directory(mukkuru_env["artwork"], f"Avatar/{get_username()}.jpg")
        elif Path(avatar_png).is_file():
            return send_from_directory(mukkuru_env["artwork"], f"Avatar/{get_username()}.png")
        else:
            return send_from_directory(serve_path, os.path.join("assets","avatar_man.png"))
    if path.startswith("assets/audio/"):
        user_sfx = os.path.join(mukkuru_env["root"], "sfx")
        user_audios = os.listdir(user_sfx)
        audio_file = path.replace("assets/audio/", "")
        new_path = f'assets/audio/{user_config["uiSounds"]}/{audio_file}'
        if user_config["uiSounds"] in user_audios:
            serve_path = user_sfx
            new_path = new_path.replace("assets/audio/", "")
        ogg_file = f'{new_path}.ogg'
        wav_file = f'{new_path}.wav'
        mp3_file = f'{new_path}.mp3'
        if Path(os.path.join(serve_path, ogg_file)).exists():
            new_path = ogg_file
        elif Path(os.path.join(serve_path, wav_file)).exists():
            new_path = wav_file
        elif Path(os.path.join(serve_path, mp3_file)).exists():
            new_path = mp3_file
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
    return send_from_directory(serve_path, path)

@app.route('/app/update')
def start_app_update():
    ''' downloads update if available '''
    ret = updater.download_mukkuru_update()
    return ret

@app.route('/config/fullscreen')
def is_fullscreen():
    ''' show whether app should be in fullscreen '''
    user_config = get_config()
    return user_config["fullScreen"]

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

def get_destination_map():
    ''' returns a dictinary with user folders '''
    user_config = get_config()
    destination_map = {
        "video" : user_config["videoSources"][1],
        "misc" : get_userprofile_folder("Downloads"),
        "music" : user_config["musicSources"][1],
        "pictures" : user_config["pictureSources"][1]
    }
    return destination_map

@app.route("/app/user_dirs")
def get_user_dirs():
    ''' retrieves a dictionary with user_dirs '''
    destination_map = get_destination_map()
    return jsonify(destination_map)

@app.route('/app/move/<folder>', methods = ['POST'])
def move_files_controller(folder):
    ''' move files between folders '''
    user_config = get_config()
    source_map = {
        "video" : user_config["videoSources"][0],
        "misc" : os.path.join(mukkuru_env["root"], "miscellaneous"),
        "music" : user_config["musicSources"][0],
        "pictures" : user_config["pictureSources"][0]
    }
    if folder not in source_map:
        return "Invalid option"
    destination_map = get_destination_map()
    source_folder = source_map[folder]
    destination_folder = destination_map[folder]
    loc = localize()
    if len(os.listdir(source_folder)) == 0:
        return loc.get("filesMoveMissing", "There are no files to move"), 404
    for item in os.listdir(source_folder):
        source_path = os.path.join(source_folder, item)
        destination_path = os.path.join(destination_folder, item)
        shutil.move(source_path, destination_path)
    return loc.get("filesMoveSuccess", "Files moved successfully"), 200

def start_app(is_server = False):
    ''' init server '''
    try:
        user_config = get_config()
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

def get_alive_status():
    ''' get alive status'''
    default = {"Status": "OK" }
    response = mukkuru_env["alive"]
    if response != default:
        set_alive_status(default)
    return response

def fix_file_sources():
    ''' add user dirs to file sources '''
    user_config = get_config()
    if len(user_config["pictureSources"]) == 1:
        user_config["pictureSources"].append(get_userprofile_folder("Pictures"))
    if len(user_config["videoSources"]) == 1:
        user_config["videoSources"].append(get_userprofile_folder("Videos"))
    if len(user_config["musicSources"]) == 1:
        user_config["musicSources"].append(get_userprofile_folder("Music"))
    get_config.cache_clear()
    if user_config != get_config():
        backend_log("Adding user paths...")
        update_config(user_config)

def main():
    ''' start of app execution '''
    system = platform.system()
    backend_log(f"Running on {system}")
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
    if len(sys.argv) >= 2:
        print("Running in test mode")
        arg = sys.argv[1]
        if arg == "--test":
            test.run_tests()
            return
    backend_log(f'Using { FRONTEND_MODE } for rendering')
    backend_log(f"COMPILER_FLAG: {COMPILER_FLAG}")
    hardware_if.kill_process_on_port(APP_PORT)#to-do: send an app/quit request to Mukkuru
    # Instead of writing another executable, this one will conditionally act as updater
    if "MUKKURU_UPDATE" in os.environ and COMPILER_FLAG:
        updater.process_update()
    elif COMPILER_FLAG:
        Path(os.path.join(mukkuru_env["root"], format_executable("update"))).unlink(missing_ok=True)

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
        os.path.join(mukkuru_env["root"], "tools"),
        os.path.join(mukkuru_env["root"], "sfx"),
    ]

    set_alive_status({"Status": "OK" })

    for needed_dir in needed_dirs:
        if not os.path.isdir(needed_dir):
            os.makedirs(needed_dir, exist_ok=True)

    user_config = get_config()
    if not Path(mukkuru_env["library.json"]).is_file():
        backend_log("No library.json")
    else:
        games = get_games()
        scan_thumbnails(games)
    if user_config["startupGameScan"] is True:
        backend_log("[debug] startupGameScan: True, starting library scan")
        threading.Thread(target=scan_games).start()
    download_steam_avatar(mukkuru_env["artwork"])
    fix_file_sources()
    if threading.current_thread() is threading.main_thread():
        threading.Thread(target=start_app).start()
        threading.Thread(target=artwork_worker, daemon=True).start()
        hardware_if.wait_for_server("localhost", APP_PORT)
        Frontend(is_fullscreen(), app_version(), mukkuru_env).start()
        # if main thread returns, ThreadExecutor won't work
        threading.Event().wait()
    else:
        start_app()
if __name__ == "__main__":
    main()
