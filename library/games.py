# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Mukkuru games module '''
import os
import subprocess
import queue
import time
import platform
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from utils.core import mukkuru_env, backend_log, set_alive_status, get_paths_from_extensions
from utils.core import get_config, update_config, sanitized_env, normalize_text
from utils.model import Game
import utils.database as db
from library.steam import get_steam_env, get_crossover_steam
from library.steam import get_steam_games, get_non_steam_games, read_steam_username
from library import grid_db, wrapper
from library.egs import read_heroic_username, get_heroic_env, get_egs_env
from library.egs import get_heroic_games, get_egs_games

artwork_queue = queue.Queue()
pending_tasks = queue.Queue()

def artwork_worker() -> None:
    ''' Processes artwork queue '''
    while True:
        print("arwork_work init")
        games = artwork_queue.get()
        print("received queue")
        if games is None:
            break
        try:
            scan_artwork(games)
        except (queue.Empty) as e:
            print("Worker error:", e)
        finally:
            artwork_queue.task_done()

def update_sgdb_api(user_config: dict) -> None:
    ''' updates sgdb api, if needed '''
    if user_config["sgdb_key"] == grid_db.API_KEY:
        print("sgdb api is unset")
        return
    else:
        grid_db.API_URL = grid_db.SGDB_URL
        grid_db.API_KEY = user_config["sgdb_key"]

def library_scan(options: int) -> dict:
    '''
    Scan library for games\n
    :param options: bitwise options representation\n
        1 - Steam\n
        2 - Non-Steam\n
        4 - EGS\n
        8 - Heroic\n
    :type options: int
    '''
    option_steam = 1 << 0  # 0001 = 1
    option_nonsteam = 1 << 1  # 0010 = 2
    option_egs = 1 << 2  # 0100 = 4
    option_heroic = 1 << 3 # 1000 = 8
    steam = get_steam_env()
    crossover_steam = get_crossover_steam()
    games = {}
    if steam is not None:
        if options & option_steam:
            steam_games = get_steam_games(steam)
            games.update(steam_games)
        if (options & option_nonsteam) and steam["shortcuts"] is not None:
            non_steam_games = get_non_steam_games(steam)
            games.update(non_steam_games)
    if crossover_steam is not None:
        if options & option_steam:
            crossover_steam_games = get_steam_games(crossover_steam)
            games.update(crossover_steam_games)
        if (options & option_nonsteam) and crossover_steam["shortcuts"] is not None:
            crossover_non_steam_games = get_non_steam_games(crossover_steam)
            games.update(crossover_non_steam_games)
    if options & option_egs:
        egs_games = get_egs_games()
        games.update(egs_games)
    if options & option_heroic:
        heroic_games = get_heroic_games()
        games.update(heroic_games)
    library_filtering(games)
    return games

def library_filtering(games: dict) -> None:
    ''' handles post scan game filtering '''
    user_config = get_config()
    if user_config["skipDuplicated"]:
        game_titles = []
        for key, value in games.copy().items():
            game_title = normalize_text(value["AppName"])
            if game_title in game_titles:
                backend_log(f"skipping duplicated: {game_title} due to user settings")
                del games[key]
            else:
                game_titles.append(game_title)

def get_games() -> dict:
    '''get game library as dictionary'''
    session = db.get_session()
    db_games: list[Game] = session.query(Game).all()
    games = {}
    for db_game in db_games:
        app_id = db_game.app_id
        games[app_id] = {}
        games[app_id] = db_game.dictionary
        games[app_id].update(db_game.Metadata)
    session.close()
    return games

def update_games(games: dict) -> None:
    '''save game library'''
    session = db.get_session()
    session.query(Game).delete()
    for app_id, game in games.items():
        game: dict
        current_game = Game(app_id=app_id)
        current_game.dictionary = game
        session.add(current_game)
    session.commit()
    session.close()

def scan_games(dry: bool = False) -> dict:
    ''' scan for games, download artwork if available '''
    user_config = get_config()
    options = user_config["librarySource"]
    games = library_scan(int(options))
    if not dry:
        artwork_queue.put(games)
        scan_thumbnails(games)
        time.sleep(0.1)
    return games

def fetch_artwork(app_id: str, game, b1, b2, b3, use_alt_images) -> dict:
    ''' handle artwork '''
    blacklist_1 = []
    blacklist_2 = []
    blacklist_3 = []
    hero_index = 0
    boxart_index = 0
    logo_index = 0
    if app_id in use_alt_images:
        alt_option = use_alt_images[app_id]
        option_boxart = 1 << 0  # 0001 = 1
        option_hero = 1 << 1  # 0010 = 2
        option_logo = 1 << 2  # 0100 = 4
        if alt_option & option_boxart:
            boxart_index = 1
        if alt_option & option_hero:
            hero_index = 1
        if alt_option & option_logo:
            logo_index = 1
        print(f"using alternate image for {game['AppName']}")
    thumbnail = os.path.join(mukkuru_env["root"], "thumbnails", f'{app_id}.jpg')
    game_source = game["Source"]
    game_identifier = grid_db.GameIdentifier(game["AppName"], app_id, game_source)
    if not Path(thumbnail).is_file() and app_id not in b1:
        if grid_db.download_image(game_identifier, thumbnail,"1:1", boxart_index) == "Missing":
            blacklist_1.append(app_id)
    hero = os.path.join(mukkuru_env["root"], "hero", f'{app_id}')
    if not Path(hero).is_file() and app_id not in b2:
        if grid_db.download_image(game_identifier, hero, "hero", hero_index) == "Missing":
            blacklist_2.append(app_id)
    logo = os.path.join(mukkuru_env["root"], "logo", f'{app_id}.png')
    if not Path(logo).is_file() and app_id not in b3:
        if grid_db.download_image(game_identifier, logo,"logo", logo_index) == "Missing":
            blacklist_3.append(app_id)
    result = {}
    result["1"] = blacklist_1
    result["2"] = blacklist_2
    result["3"] = blacklist_3
    return result

def scan_artwork(games = None) -> None:
    ''' scan for games artwork '''
    backend_log("scanning for new artwork..")
    config = get_config()
    update_sgdb_api(config)
    blacklist1 = config["boxartBlacklist"]
    blacklist2 = config["heroBlacklist"]
    blacklist3 = config["logoBlacklist"]
    use_alt_images = config["useAlternativeImage"]
    if games is None:
        games = get_games()
    results = {}
    with ThreadPoolExecutor(max_workers=config["cores"]*2) as executor:
        future_to_key = {
            executor.submit(fetch_artwork, k, v, blacklist1, blacklist2,
                            blacklist3, use_alt_images): k
            for k, v in games.items()
        }
        counter = 0
        for future in as_completed(future_to_key):
            k = future_to_key[future]
            try:
                results[k] = future.result()
                blacklist1.extend(results[k]["1"])
                blacklist2.extend(results[k]["2"])
                blacklist3.extend(results[k]["3"])
                counter = counter + 1
                if counter % 12 == 0:
                    set_alive_status({"command": "reloadGameThumbnails"})
                    scan_thumbnails(games)
            except (KeyError, OSError, IndexError, FileNotFoundError) as e:
                results[k] = {"error": str(e)}
                print(f"scan_artwork error: {str(e)}")
    config["boxartBlacklist"] = blacklist1
    config["heroBlacklist"] = blacklist2
    config["logoBlacklist"] = blacklist3
    update_config(config)
    scan_thumbnails(games)
    set_alive_status({"command": "ScanFinished"})

def scan_thumbnails(games: dict) -> None:
    '''update the thumbnail status for all games'''
    for k in games.keys():
        thumbnail_base = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}')
        thumbnail_list = get_paths_from_extensions(thumbnail_base, ["png", "jpg", "webp"])
        thumbnail_found = False
        for thumbnail_path in thumbnail_list:
            if Path(thumbnail_path).is_file():
                thumbnail_found = True
                break
        games[k]["Thumbnail"] = thumbnail_found
    update_games(games)

def get_game_properties(app_id: str) -> dict:
    ''' get game specific properties '''
    user_config = get_config()
    game_property = {
        "isFavorite" : False,
        "isHidden" : False,
        "useAlternativeImage" : 0,
        "useAlternativeHero" : False
    }
    game_properties = user_config["gameProperties"]
    if app_id in game_properties:
        return game_properties[app_id]
    return game_property

def launch_lossless_scaling():
    ''' (Windows) launchs lossless scaling executable and sends ctrl+alt+s after 30 seconds '''
    games = get_games()
    backend_log("Launching lossless_scaling....")
    lossless_scaling = games["993090"]
    lossless_path = os.path.join(lossless_scaling["InstallDir"], "LosslessScaling.exe")
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    subprocess.Popen([lossless_path], startupinfo=startupinfo)
    time.sleep(30)
    from utils.winkeys import send_ctrl_alt_s#pylint: disable=C0415
    send_ctrl_alt_s()

def find_app_id_from_path(path: str) -> str:
    ''' finds an app_id if a path is matched from all installed games '''
    games = get_games()
    for app_id, game in games.items():
        if "InstallDir" in game:
            if os.path.normpath(path) in os.path.normpath(game["InstallDir"]):
                backend_log(f"Using {app_id} due to matching InstallDir")
                return app_id
    return ""
# To-do:
# set env at provider (steam/heroic/egs) level
def launch_app(app_id: str) -> None:
    '''launches an app using its appID'''
    process_env = sanitized_env()
    games = get_games()
    game_path = games[app_id]["Exe"].strip('"')
    working_dir = None
    backend_log(f'Launching game: {game_path} using {games[app_id]["LaunchOptions"]}')
    if "flatpak" in game_path:
        pass
    else:
        game_path = f'"{game_path}"'
    launch_command = f'{game_path} {games[app_id]["LaunchOptions"]}'
    if "Type" in games[app_id] and games[app_id]["Type"] == "CROSSOVER":
        source = games[app_id]["Source"]
        bottle = "Steam"
        if source == "egs":
            bottle = "Epic Games Store"
        process_env = wrapper.get_crossover_env(bottle)
        launch_command = f"wine --cx-app {launch_command}"
        working_dir = process_env["CX_DISK"]
    user_config = get_config()
    lossless_scaling = user_config["losslessScaling"]
    if app_id in lossless_scaling and platform.system() == "Windows":
        threading.Thread(target=launch_lossless_scaling).start()
    backend_log(f"using {launch_command}")
    subprocess.run(launch_command,
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   cwd=working_dir,
                   env=process_env, shell=True, check=False)
    recent_played = user_config["recentPlayed"]
    if app_id not in recent_played:
        recent_played.insert(0, app_id)
        while len(recent_played) > 3:
            recent_played.pop(3)
        update_config(user_config)

def list_stores() -> list:
    ''' list valid storefronts for this device '''
    stores = []
    steam = get_steam_env()
    csv_steam = get_crossover_steam()
    heroic =  get_heroic_env()
    egs = get_egs_env()
    if steam is not None:
        stores.append("steam")
    if csv_steam is not None:
        stores.append("crossover_steam")
    if heroic is not None:
        stores.append("heroic")
    if egs is not None:
        stores.append("egs")
    return stores
# to-do: setup os.environ in steam_env dictionary
def launch_store(storefront: str) -> None:
    ''' opens a storefront '''
    store_env = sanitized_env()
    prefix = ""
    if storefront == "steam" or storefront == "crossover_steam":
        steam = get_steam_env()
        if storefront == "crossover_steam":
            steam = get_crossover_steam()
            store_env =  wrapper.get_crossover_env("Steam")
            prefix = "wine --cx-app "
        subprocess.run(f'{prefix}"{steam["launchPath"]}" steam://open/bigpicture',
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=store_env, shell=True, check=False)
        time.sleep(3)
        subprocess.run(f'{prefix}"{steam["launchPath"]}" steam://store',
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=store_env, shell=True, check=False)
    # Since EGS is natively Windows Only, any EGS instance
    # would be running from a compatibility layer
    elif storefront == "egs":
        egs = get_egs_env()
        if "Type" in egs and egs["Type"] == "CROSSOVER":
            store_env = wrapper.get_crossover_env("Epic Games Store")
            prefix = "wine --cx-app "
        launch_command = f'{prefix}"{egs["launchPath"]}"'
        subprocess.run(launch_command,
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   env=store_env, shell=True, check=False)
        backend_log(f"using {launch_command}")
    elif storefront == "heroic":
        backend_log("Unimplemented store")
    else:
        backend_log(f"unknown storefront {storefront}")

@lru_cache(maxsize=1)
def get_username() -> str:
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
