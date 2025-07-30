# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Handles Mukkuru updates '''
import os
import shutil
import subprocess
import sys
import platform
import stat
import json
from typing import Union, Optional
import requests
from utils.core import format_executable, APP_VERSION, mukkuru_env, COMPILER_FLAG
from utils.core import backend_log, sanitized_env
from utils import bootstrap

REPO_URL = "https://api.github.com/repos/b1on1cdog/Mukkuru/releases"

def process_update() -> None:
    ''' Replaces executable with new version, then starts new version '''
    update_file = os.path.abspath(sys.argv[0])
    update_file = format_executable(update_file)
    executable = os.environ["MUKKURU_UPDATE"]
    backend_log(f"replacing {executable} with {update_file}")
    shutil.copy(update_file, executable)
    current_permissions = os.stat(executable).st_mode
    os.chmod(executable, current_permissions | stat.S_IXUSR)
    os.environ.pop("MUKKURU_UPDATE")
    subprocess.Popen([executable])
    os._exit(0)

def start_update(update_path) -> None:
    ''' Windows/Linux: replaces current executable with new one
        MacOS: opens new dmg and terminates current app
    '''
    if platform.system() == "Darwin":
        subprocess.run(["open", update_path], check=False)
        os._exit(0)
    else:
        update_env = sanitized_env()
        update_env["MUKKURU_UPDATE"] = os.path.abspath(sys.argv[0])
        backend_log(f'{update_path} will replace {update_env["MUKKURU_UPDATE"]}')
        subprocess.Popen([update_path], env=update_env)
        os._exit(0)

def get_platform_str(alt = False) -> str:
    ''' Returns string used in executables names '''
    current_os = platform.system().lower()
    if current_os == "darwin" and not alt:
        current_os = "macos"
    current_arch = platform.uname().machine.lower()
    if current_arch == "amd64":
        current_arch = "x86_64"
    return f"{current_os}-{current_arch}"

def ver_compare(ver1, ver2) -> int:
    ''' compare 2 version strings 0 - lower, 1-equal, 2 bigger '''
    v1 = ver1.split(".")
    v2 = ver2.split(".")
    if ver1 == ver2:
        return 1
    while len(v1) > 0 and len(v2) > 0:
        if int(v2[0]) > int(v1[0]):
            return 0
        if int(v2[0]) < int(v1[0]):
            return 2
        del v1[0]
        del v2[0]
    if len(v1) > 0:
        if int(v1[0]) == 0:
            return 1
        else:
            return 2
    if len(v2) > 0:
        if int(v2[0]) == 0:
            return 1
        else:
            return 0

def find_latest_version(versions: list) -> Optional[str]:
    ''' returns the largest version '''
    if not versions:
        return None
    print(versions)
    largest = versions[0]
    for version in versions[1:]:
        if ver_compare(largest, version) == 0:
            largest = version
    return largest

def find_latest_release(version_info = False) -> Union[str, str]:
    ''' finds latest asset url '''
    manifest = requests.get(REPO_URL, stream=True, timeout=20).content
    releases = json.loads(manifest)
    platform_str = get_platform_str()
    alt_platform_str = get_platform_str(True)
    version_list = {}
    changelog = {}
    for release in releases:
        try:
            tag_name = release["tag_name"]
            changelog[tag_name] = release["body"]
            for asset in release["assets"]:
                download_url = asset["browser_download_url"]
                digest = asset["digest"].replace("sha256:", "")
                if platform_str in download_url or alt_platform_str in download_url:
                    version_list[tag_name] = {
                        "digest" : digest,
                        "url" : download_url,
                    }
        except (KeyError, IndexError):
            backend_log("Key does not exists")
            return "", ""
    print(f"Number of Mukkuru builds : {len(version_list)}")
    versions = list(version_list.keys())
    latest_version = find_latest_version(versions)
    if latest_version is None:
        return "",""
    if ver_compare(latest_version, APP_VERSION) == 2:
        if version_info:
            return latest_version, changelog[latest_version]
        backend_log(f'found update url {version_list[latest_version]["url"]}')
        return version_list[latest_version]["url"], version_list[latest_version]["digest"]
    return "", ""

def check_for_updates() -> dict:
    ''' returns whether device can be updated '''
    update_status = {}
    release_url, release_digest = find_latest_release()
    #if not COMPILER_FLAG:
    #    update_status["status"] = "unsupported"
    #    return update_status
    if release_url != "" and release_digest != "":
        update_status["status"] = "available"
        update_status["url"] = release_url
        update_status["digest"] = release_digest
        update_version, changelog = find_latest_release(True)
        changelog = changelog.replace("<br>", "\n")
        changelog = changelog.replace("<br/>", "\n")
        update_status["version"] = update_version
        update_status["changelog"] = changelog
    else:
        update_status["status"] = "up-to-date"
    return update_status
def download_mukkuru_update() -> str:
    ''' downloads latest binary from Github '''
    if not COMPILER_FLAG:
        return "unsupported"
    release_url, release_digest = find_latest_release()
    if release_url != "" and release_digest != "":
        update_path = os.path.join(mukkuru_env["root"], format_executable("update"))
        if platform.system() == "Darwin":
            update_path = f"{update_path}.dmg"
        bootstrap.set_global_progress_context("Downloading Mukkuru update.....")
        bootstrap.download_file(release_url, update_path,
                                progress_callback=bootstrap.global_progress_callback)
        sha256_hash = bootstrap.sha256_file(update_path)
        bootstrap.clear_global_progress()
        if sha256_hash == release_digest:
            backend_log("file checksum is OK")
            start_update(update_path)
        else:
            os.remove(update_path)
            backend_log("corrupted download, failed")
            return "bad_download"
    else:
        return "up-to-date"
