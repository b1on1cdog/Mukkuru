''' Epic Games library module '''
import os
import platform
import json
from pathlib import Path
from functools import lru_cache
from typing import Optional
from library import wrapper, common

system = platform.system()

def find_path(paths) -> Optional[str]:
    ''' return which path exists of all the candidates '''
    for path in paths:
        if "~" in path:
            path = os.path.expanduser(path)
        if Path(path).exists():
            return path
    return None

@lru_cache(maxsize=1)
def read_heroic_username(heroic = None) -> Optional[str]:
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
def get_heroic_env() -> Optional[dict]:
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
    heroic["Type"] = "NATIVE"
    return heroic

def get_heroic_games() -> dict:
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
                    "Type" : heroic["Type"]
                }
    except (PermissionError, IndexError, json.decoder.JSONDecodeError) as e:
        print(f"Exception occured: {e}")
    installed.close()
    return games

def get_egs_env() -> Optional[dict]:
    ''' Windows/MacOS gets egs environment '''
    egs = {}
    egs["Type"] = "NATIVE"
    disk = "C:\\"
    if platform.system() == "Darwin":
        crossover_env = wrapper.get_crossover_env("Epic Games Store")
        disk = crossover_env["CX_DISK"]
        egs["Type"] = "CROSSOVER"
    if platform.system() == "Linux":
        return None
    install_dirs = [
        os.path.join(disk, "Program Files (x86)", "Epic Games"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Epic Games")
    ]
    install_dir = common.find_path(install_dirs)
    if install_dir is None:
        return None
    egs["path"] = install_dir
    egs["launchPath"] = os.path.join(install_dir, "Launcher", "Portal",
                                     "Binaries", "Win32", "EpicGamesLauncher.exe")
    if not Path(egs["launchPath"]).is_file():
        print("hmmm, looks like egs launcher is missing, ignoring for the meanwhile")
    egs_reg = r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher"
    data_dirs = [
        os.path.join(disk, "ProgramData", "Epic", "EpicGamesLauncher", "Data"),
        common.read_registry_value(0, egs_reg, "AppDataPath")
    ]
    programdata_dir = common.find_path(data_dirs)
    if programdata_dir is None:
        print("Unable to find EGS ProgramData dir")
        return None
    egs["manifestDir"] = os.path.join(programdata_dir, "Manifests")
    print(f'manifest: {egs["manifestDir"]}')
    if not Path(egs["manifestDir"]).is_dir():
        print("Unable to find EGS Manifest dir")
        return None
    return egs

def get_egs_games() -> dict:
    ''' Windows/MacOS get games from epic games launcher '''
    games = {}
    egs = get_egs_env()
    if egs is None:
        print("Using heroic as failover....")
        return get_heroic_games()
    manifest_dir = egs["manifestDir"]
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
                            "Source" : "egs",
                            "Type" : egs["Type"]
                        }

            except (PermissionError, IndexError, json.decoder.JSONDecodeError) as e:
                print(f"Exception occured: {e}")
    return games
