'''
Games archiving library\n
Imports library.games, utils.(bootstrap, expansion)\n
'''
import os
from pathlib import Path
import glob
import shutil
import json
from library.games import get_games
from utils import bootstrap
from utils.core import backend_log
from utils.core import mukkuru_env
from utils.expansion import translate_str

def is_game_archived(app_id) -> bool:
    ''' Determines whether a game is archived or not\n
     :returns: A boolean indicating if game is archived\n'''
    archives = get_archived_games()
    if app_id in archives:
        return True
    games = get_games()
    game = games[app_id]
    install_dir = game["InstallDir"]
    archive_placeholder = os.path.join(install_dir, ".archived")
    return Path(archive_placeholder).exists()

def get_archived_games() -> dict:
    '''Get a dictionary with archived games\n
    :returns: a dictionary containing archived games\n'''
    archive_path = os.path.join(mukkuru_env["root"], "archived.json")
    archives = {}
    if not Path(archive_path).is_file():
        update_archived_games(archives)
    with open(archive_path, "r", encoding='utf-8') as f:
        archives = json.load(f)
    return archives

def update_archived_games(archives: dict) -> None:
    ''' updates disk archived dictionary\n
    :param dict archives: dictionary with archives to update\n'''
    archive_path = os.path.join(mukkuru_env["root"], "archived.json")
    with open(archive_path, "w", encoding='utf-8') as f:
        json.dump(archives, f)

def archive_game(app_id: str) -> bool:
    ''' archive game to save storage\n
    :param str app_id: app_id of game to archive\n
    :returns: boolean indicating operation success\n'''
    if bootstrap.get_7z() is None:
        backend_log("7z missing, archiving not supported")
        return False
    bootstrap.set_global_progress_context(translate_str("Starting"))
    games: dict = get_games()
    game: dict = games[app_id]
    if "InstallDir" not in game:
        backend_log("Game missing InstallDir, unable to proceed")
        return False
    install_dir: str = game["InstallDir"]
    # To-do: allow archiving in another disk/path
    archive_dir = os.path.abspath(os.path.join(install_dir, "..", "..", "archives"))
    archive_file = os.path.join(archive_dir, f"{app_id}.7z")

    os.makedirs(archive_dir, exist_ok=True)
    archive = {
        "AppName" : game["AppName"],
        "Size" : bootstrap.get_dir_size(install_dir),
        "CompressedSize" : 0,
        "InstallDir" : install_dir,
        "ArchivePath" : archive_file,
    }
    files: list = glob.glob(os.path.join(install_dir, "*"))
    files = files + glob.glob(os.path.join(install_dir, ".*"))
    bootstrap.set_global_progress_context(f'{translate_str("Compressing")} {game["AppName"]}')
    success: bool = bootstrap.compress_7z(files, archive_file, bootstrap.global_progress_callback)
    if success:
        archive["CompressedSize"] = os.path.getsize(archive_file)
        for file in files:
            if Path(file).is_dir():
                shutil.rmtree(file)
            elif Path(file).is_file():
                os.remove(file)
        with open(os.path.join(install_dir, ".archived"), "w", encoding="utf-8") as placeholder:
            placeholder.write(str(archive["Size"]))
        archives = get_archived_games()
        archives[app_id] = archive
        update_archived_games(archives)
    bootstrap.clear_global_progress()
    return success

def restore_game(app_id: str) -> bool:
    ''' restores archived game '''
    archives = get_archived_games()
    bootstrap.set_global_progress_context(translate_str("Starting"))
    if app_id not in archives:
        backend_log(f"Error: {app_id} not in archives")
        games = get_games()
        if app_id not in games:
            return False
        game = games[app_id]
        if "InstallDir" not in game:
            backend_log("Unable to rebuild game from placeholder")
            return False
        install_dir = game["InstallDir"]
        placeholder = os.path.join(install_dir, ".archived")
        if not Path(placeholder).is_file():
            return False
        archives = os.path.abspath(os.path.join(install_dir, "..", "..", "archives"))
        archive = {}
        archive["Size"] = int(Path(placeholder).read_text(encoding='utf-8'))
        archive["AppName"] = game["AppName"]
        archive["InstallDir"] = install_dir
        archive["ArchivePath"] = os.path.join(archives, f"{app_id}.7z")
        if not Path(archive["ArchivePath"]).exists():
            return False
        archive["CompressedSize"] = os.path.getsize(archive["ArchivePath"])
    else:
        archive = archives[app_id]
    if not bootstrap.has_enough_space(archive["InstallDir"], archive["Size"]):
        backend_log("Unable to extract game")
        return False
    bootstrap.extract_archive(archive["ArchivePath"], archive["InstallDir"])
    backend_log("Game extraction succeded, removing placeholder...")
    bootstrap.clear_global_progress()
    try:
        os.remove(os.path.join(archive["InstallDir"], ".archived"))
    except FileNotFoundError:
        pass
    return True
