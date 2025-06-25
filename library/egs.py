''' Epic Games library module '''
import os
import platform
import json
from pathlib import Path
from functools import lru_cache

system = platform.system()

def find_path(paths):
    ''' return which path exists of all the candidates '''
    for path in paths:
        if "~" in path:
            path = os.path.expanduser(path)
        if Path(path).exists():
            return path
    return None

@lru_cache(maxsize=1)
def read_heroic_username(heroic = None):
    ''' read heroic username '''
    if heroic is None:
        heroic = get_heroic_env()
        if heroic is None:
            print("Unable to read heroic username")
            return None
    try:
        with open(heroic["user.json"], encoding='utf-8') as usf:
            user_info = json.load(usf)
            return user_info["displayName"]
    except (PermissionError, FileNotFoundError, KeyError, IndexError, json.decoder.JSONDecodeError):
        pass
    return None

# Currently only Linux flatpak supported
@lru_cache(maxsize=1)
def get_heroic_env():
    ''' finds heroic paths '''
    main_paths = ['~/.var/app/com.heroicgameslauncher.hgl/']
    main_path = find_path(main_paths)
    if main_path is None:
        print("heroic is not available")
        return None
    heroic = {}
    heroic["path"] = main_path
    legendary_path = os.path.join(main_path,"config", "heroic", "legendaryConfig", "legendary")
    heroic["legendary"] = legendary_path
    heroic["libraryFile"] = legendary_path
    heroic["user.json"] = os.path.join(legendary_path, "user.json")
    heroic["installed.json"] = os.path.join(legendary_path, "installed.json")
    return heroic

def get_heroic_games():
    ''' get games from heroic launcher '''
    games = {}
    heroic = get_heroic_env()
    if heroic is None:
        return games
    if not Path(heroic["installed.json"]).exists():
        print("heroic installed.json not found")
        return games
    installed = open(heroic["installed.json"], encoding='utf-8')
    try:
        manifest = json.load(installed)
        for _, gameinfo in manifest.items():
            app_id = gameinfo["app_name"]
            app_name = gameinfo["title"]
            game_dir = os.path.join(gameinfo["install_path"], gameinfo["executable"])
            launch_option = f'launch --nogui --no-sandbox  "heroic://launch/legendary/{app_id}"'
            if app_name and app_id:
                games[app_id] = {
                    "AppName" : app_name,
                    "Exe" : "flatpak run com.heroicgameslauncher.hgl",
                    "LaunchOptions" : launch_option,
                    "Executable" : game_dir,
                    "StartDir" : gameinfo["install_path"],
                    "Source" : "egs",
                }
    except (PermissionError, IndexError, json.decoder.JSONDecodeError) as e:
        print(f"Exception occured: {e}")
    installed.close()
    return games

def get_egs_games():
    ''' [Windows only] get games from epic games launcher '''
    #To-do: look for alternate ProgramData paths
    games = {}
    if system != "Windows":
        return get_heroic_games()
    manifest_dir = r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
    if not os.path.exists(manifest_dir):
        print(f"Manifest directory not found: {manifest_dir}")
        print("Using heroic as failover....")
        return get_heroic_games()
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
