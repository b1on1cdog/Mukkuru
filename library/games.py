# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Mukkuru games module '''
import os
import json
import time
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from utils.core import mukkuru_env, backend_log, set_alive_status
from utils.core import get_config, update_config
from library.steam import get_steam_env, get_crossover_steam, get_crossover_env
from library.steam import get_steam_games, get_non_steam_games, read_steam_username
from library import grid_db
from library.egs import get_egs_games, read_heroic_username

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
    crossover_steam = get_crossover_steam()
    games = {}
    if steam is not None:
        if options & option_steam:
            steam_games = get_steam_games(steam)
            games.update(steam_games)
        if steam["shortcuts"] is not None and (options & option_nonsteam):
            non_steam_games = get_non_steam_games(steam)
            games.update(non_steam_games)
    if crossover_steam is not None:
        if options & option_steam:
            steam_games = get_steam_games(crossover_steam)
            games.update(steam_games)
        if steam["shortcuts"] is not None and (options & option_nonsteam):
            non_steam_games = get_non_steam_games(crossover_steam)
            games.update(non_steam_games)
    if options & option_egs:
        egs_games = get_egs_games()
        games.update(egs_games)
    return games

def get_games():
    '''get game library as json'''
    try:
        with open(mukkuru_env["library.json"], encoding='utf-8') as f:
            games = json.load(f)
    except FileNotFoundError:
        games = {}
        update_games(games)
    return games

def update_games(games):
    '''save game library'''
    with open(mukkuru_env["library.json"], 'w', encoding='utf-8') as f:
        json.dump(games, f)

def scan_games():
    ''' scan for games, download artwork if available '''
    user_config = get_config()
    options = user_config["librarySource"]
    games = library_scan(int(options))
    #game_library.update(games)
    threading.Thread(target=scan_artwork, args=(games,)).start()
    time.sleep(5)
    for k, _ in games.items(): #games.keys
        thumbnail_path = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}.jpg')
        if not Path(thumbnail_path).is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)
    return games

def fetch_artwork(app_id, game, b1, b2, b3, use_alt_images):
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
    hero = os.path.join(mukkuru_env["root"], "hero", f'{app_id}.png')
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

def scan_artwork(games = None):
    ''' scan for games artwork '''
    backend_log("scanning for new artwork..")
    config = get_config()
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
                print(f"scan_arwork error: {str(e)}")
    config["boxartBlacklist"] = blacklist1
    config["heroBlacklist"] = blacklist2
    config["logoBlacklist"] = blacklist3
    update_config(config)
    #clear_possible_mismatches(games)
    scan_thumbnails(games)
    set_alive_status({"command": "ScanFinished"})
    return "200"


def scan_thumbnails(games):
    '''update the thumbnail status for all games'''
    for k in games.keys():
        thumbnail_path = os.path.join(mukkuru_env["root"], "thumbnails", f'{k}.jpg')
        if not Path(thumbnail_path).is_file():
            games[k]["Thumbnail"] = False
        else:
            games[k]["Thumbnail"] = True
    update_games(games)


def get_game_properties(app_id):
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

def launch_app(app_id):
    '''launches an app using its appID'''
    process_env = os.environ.copy()
    games = get_games()
    game_path = games[app_id]["Exe"].strip('"')
    working_dir = None
    backend_log(f'Launching game: {game_path} using {games[app_id]["LaunchOptions"]}')
    if "flatpak" in game_path:
        pass
    else:
        game_path = f'"{game_path}"'
    launch_command = f'{game_path} {games[app_id]["LaunchOptions"]}'
    #if '%command%' in games[app_id]["LaunchOptions"]:
    #    launch_command = games[app_id]["LaunchOptions"].replace('%command', game_path)
    if "Type" in games[app_id] and games[app_id]["Type"] == "CROSSOVER":
        process_env = get_crossover_env()
        launch_command = f"wine --cx-app {launch_command}"
        working_dir = process_env["CX_DISK"]
    backend_log(f"using {launch_command}")
    subprocess.run(launch_command,
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   cwd=working_dir,
                   env=process_env, shell=True, check=False)
    user_config = get_config()
    if user_config["lastPlayed"] != app_id:
        user_config["lastPlayed"] = app_id
        update_config(user_config)
    #os.environ.pop("STEAM_COMPAT_DATA_PATH", None)
    #os.environ.pop("STEAM_COMPAT_CLIENT_INSTALL_PATH", None)

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
