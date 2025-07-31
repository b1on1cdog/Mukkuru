''' Mukkuru module for addons handling '''
import os
import shutil
import time
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from functools import lru_cache
import requests
from utils.core import mukkuru_env, get_config, update_config, backend_log
from utils.core import APP_DIR
from utils import bootstrap, hardware_if
from library.games import get_games

@lru_cache(maxsize=1)
def get_localization():
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
    return localization

def translate_str(loc_key, default_string = None):
    ''' returns a localized string, returns original if missing '''
    if default_string is None:
        default_string = loc_key
    localization = get_localization()
    if loc_key in localization:
        return localization[loc_key]
    return default_string

def copy_patch(source_dir, destination_dir) -> None:
    ''' copy/merge directories for patch install '''
    if source_dir.endswith(".exe/*"):
        print("extracting exe file")
        source_dir = source_dir.replace(".exe/*", ".exe")
        bootstrap.extract_archive(source_dir, destination_dir)
        return
    if source_dir.endswith("*"):
        filename = Path(urlparse(source_dir).path).name
        filename = filename.replace("*", "")
        source_dir = Path(source_dir).parent.absolute()
        for file in os.listdir(source_dir):
            if file.startswith(filename):
                copy_patch(os.path.join(source_dir, file), destination_dir)
        return
    elif Path(source_dir).is_file():
        print(f"copy {source_dir} -> {destination_dir}")
        shutil.copy2(source_dir, destination_dir)
    elif Path(source_dir).is_dir():
        print(f"copytree {source_dir} -> {destination_dir}")
        shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)
    elif not Path(source_dir).exists():
        print(f"{source_dir} do not exists")
    else:
        print(f"copy_patch {source_dir} -> {destination_dir} ignored")

def install_patch(game_id, patch) -> None:
    ''' install patches in game '''
    games = get_games()
    if game_id not in games:
        print("failed to install patch : game not installed")
        return
    if "InstallDir" not in games[game_id]:
        print("failed to install patch : no install path")
        return
    install_dir = games[game_id]["InstallDir"]
    source_archive = patch["filename"]
    output_dir = os.path.join(mukkuru_env["root"], "misc", "patch_wd")
    source_archive = os.path.join(output_dir, source_archive)
    os.makedirs(output_dir, exist_ok=True)
    bootstrap.extract_archive(source_archive, output_dir)
    source = patch["source"]
    destination = patch["destination"]
    destination = destination.replace("$GAME_DIR", install_dir)
    source = os.path.join(output_dir, source)
    copy_patch_files_str = translate_str("CopyingPatchFiles", "Copying patch files....")
    bootstrap.set_global_progress_context(copy_patch_files_str)
    copy_patch(source, destination)
    shutil.rmtree(output_dir, ignore_errors=True)
    user_config = get_config()
    user_config["patches"].append(patch["id"])
    update_config(user_config)
    get_patches.cache_clear()
    bootstrap.clear_global_progress()

def download_patch(patch_url, filename=None) -> None:
    ''' download patch for game '''
    output_dir = os.path.join(mukkuru_env["root"], "misc", "patch_wd")
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)
    if filename is not None:
        bootstrap.set_global_progress_context(f'{translate_str("Downloading")} {filename}...')
        output_dir = os.path.join(output_dir, filename)
    bootstrap.download_file(patch_url, output_dir,
                            progress_callback=bootstrap.global_progress_callback)

@lru_cache(maxsize=1)
def get_patches():
    ''' fetch patches from repo '''
    patches = {}
    user_config = get_config()
    repos = user_config["repos"]
    for repo in repos:
        if not repo.endswith("/"):
            repo = f"{repo}/"
        repo = f"{repo}mukkuru/patches.json"
        try:
            r = requests.get(repo, stream=True, timeout=20)
            content = r.json()
        except (requests.exceptions.RequestException,
                requests.exceptions.JSONDecodeError):
            return patches
        patches.update(content)
    for _, patch_list in patches.items():
        for i in reversed(range(len(patch_list))):
            patch = patch_list[i]
            if patch["id"] in user_config["patches"]:
                patch["installed"] = True
            else:
                patch["installed"] = False
            adult_patch = "adult" in patch and patch["adult"]
            if adult_patch and not user_config["adultContent"]:
                del patch_list[i]
    return patches

def get_packages():
    ''' list installed and downloadable patches '''
    packages = {}
    user_config = get_config()
    repos = user_config["repos"]
    for repo in repos:
        if not repo.endswith("/"):
            repo = f"{repo}/"
        repo = f"{repo}mukkuru/packages.json"
        try:
            r = requests.get(repo, stream=True, timeout=20)
            content = r.json()
        except (requests.exceptions.RequestException,
                requests.exceptions.JSONDecodeError):
            return packages
        packages.update(content)
    return packages

def install_patch_from_index(app_id, patch_index) -> None:
    ''' downloads and install game patch '''
    backend_log(f"installing patch {patch_index} for {app_id}")
    bootstrap.set_global_progress_context(translate_str("Starting", "Starting..."))
    patch_index = int(patch_index)
    patches = get_patches()
    patch = patches[app_id][patch_index]
    download_url = patch["assets"]["universal"]
    patch_filename = patch["filename"]
    try:
        download_patch(download_url, patch_filename)
    except requests.exceptions.RequestException as e:
        backend_log(f"download failed due to {e}")
        bootstrap.set_global_progress_context("Download failed")
        time.sleep(3)
        bootstrap.clear_global_progress()
        return
    bootstrap.set_global_progress_context(f'{translate_str("Extracting")} {patch_filename}')
    install_patch(app_id, patch)
# to-do: support multiple OS
def add_to_startup():
    ''' (SteamOS only) Set Mukkuru to open when system boots '''
    user_config = get_config()
    device_info = hardware_if.get_info()
    if "SteamOS" not in device_info["distro"]:
        return translate_str("UnsupportedFunction", "This feature is not available for your setup")
    if "mukkuru_steam_id" not in user_config:
        return translate_str("MustAddToSteam", "You must add Mukkuru to Steam first")
    mukkuru_steam_id = user_config["mukkuru_steam_id"]
    mukkuru_service = []
    mukkuru_service.append("[Unit]")
    mukkuru_service.append("Description=Open Mukkuru from Gamescope at startup")
    mukkuru_service.append("PartOf=graphical-session.target")
    mukkuru_service.append("After=graphical-session.target")
    mukkuru_service.append("[Service]")
    mukkuru_service.append(f"ExecStart=/usr/bin/steam steam://rungameid/{mukkuru_steam_id}")
    mukkuru_service.append("Restart=no")
    mukkuru_service.append("[Install]")
    mukkuru_service.append("WantedBy=graphical-session.target")
    mukkuru_service_path = os.path.expanduser("~/.config/systemd/user/mukkuru.service")
    with open(mukkuru_service_path,"w", encoding="utf-8") as file:
        file.write("\n".join(mukkuru_service))
    subprocess.run(["systemctl", "--user", "enable", "mukkuru.service"], check=False)
    return translate_str("OperationSuccess", "Operation was completed successfully")

def remove_from_startup():
    ''' (SteamOS only) removes Mukkuru from system startup '''
    mukkuru_service_path = os.path.expanduser("~/.config/systemd/user/mukkuru.service")
    subprocess.run(["systemctl", "--user", "disable", "mukkuru.service"], check=False)
    os.remove(mukkuru_service_path)
    return translate_str("OperationSuccess", "Operation was completed successfully")
