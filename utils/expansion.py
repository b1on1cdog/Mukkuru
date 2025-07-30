''' Mukkuru module for addons handling '''
import os
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse
from functools import lru_cache
import requests
from utils.core import mukkuru_env, get_config, update_config, backend_log
from utils import bootstrap
from library.games import get_games

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
    bootstrap.set_global_progress_context("Copying patch files....")
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
        bootstrap.set_global_progress_context(f"Downloading {filename}...")
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

def install_patch_from_index(app_id, patch_index) -> None:
    ''' downloads and install game patch '''
    backend_log(f"installing patch {patch_index} for {app_id}")
    patch_index = int(patch_index)
    patches = get_patches()
    patch = patches[app_id][patch_index]
    download_url = patch["assets"]["universal"]
    patch_filename = patch["filename"]
    try:
        download_patch(download_url, patch_filename)
    except requests.exceptions.RequestException:
        bootstrap.set_global_progress_context("Download failed")
        time.sleep(3)
        bootstrap.clear_global_progress()
        return
    bootstrap.set_global_progress_context(f"Extracting {patch_filename}")
    install_patch(app_id, patch)
