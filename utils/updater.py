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
import hashlib
import requests
from utils.core import format_executable, APP_VERSION, mukkuru_env, COMPILER_FLAG

REPO_URL = "https://api.github.com/repos/b1on1cdog/Mukkuru/releases"

def process_update():
    ''' Replaces executable with new version, then starts new version '''
    update_file = os.path.abspath(sys.executable)
    update_file = format_executable(update_file)
    executable = os.environ["MUKKURU_UPDATE"]
    shutil.copy(update_file, executable)
    current_permissions = os.stat(executable).st_mode
    os.chmod(executable, current_permissions | stat.S_IXUSR)
    os.environ.pop("MUKKURU_UPDATE")
    subprocess.Popen([executable])
    os._exit(0)

# to-do: close frontend
def start_update(update_path):
    ''' Windows/Linux: replaces current executable with new one
        MacOS: opens new dmg and terminates current app
    '''
    if platform.system() == "Darwin":
        subprocess.run(["open", update_path], check=False)
        os._exit(0)
    else:
        os.environ["MUKKURU_UPDATE"] = os.path.abspath(sys.executable)
        subprocess.Popen([update_path])
        os._exit(0)

def get_platform_str():
    ''' Returns string used in executables names '''
    current_os = platform.system().lower()
    if current_os == "darwin":
        current_os = "macos"
    current_arch = platform.uname().machine.lower()
    if current_arch == "amd64":
        current_arch = "x86_64"
    return f"{current_os}-{current_arch}"

def ver_compare(ver1, ver2):
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

def find_latest_release():
    ''' finds latest asset url '''
    manifest = requests.get(REPO_URL, stream=True, timeout=20).content
    releases = json.loads(manifest)
    platform_str = get_platform_str()
    for release in releases:
        try:
            # if release version is equal or lower than app_version, refuse
            tag_name = release["tag_name"]
            if ver_compare(tag_name, APP_VERSION) < 2:
                print(f"current version is up-to-date ({APP_VERSION} vs {tag_name}) ")
                return "", ""
            print(tag_name)
            for asset in release["assets"]:
                download_url = asset["browser_download_url"]
                digest = asset["digest"].replace("sha256:", "")
                if platform_str in download_url:
                    print(f"Found update url {download_url}")
                    return download_url, digest
        except (KeyError, IndexError):
            print("Key does not exists")
            return "", ""

def download_mukkuru_update():
    ''' downloads latest binary from Github '''
    if not COMPILER_FLAG:
        return "unsupported"
    release_url, release_digest = find_latest_release()
    if release_url != "" and release_digest != "":
        data = requests.get(release_url, stream=True, timeout=20).content
        sha256_hash = hashlib.sha256(data).hexdigest()
        if sha256_hash == release_digest:
            print("file checksum is OK")
            update_path = os.path.join(mukkuru_env["root"], format_executable("update"))
            with open(update_path, "wb") as f:
                f.write(data)
            start_update(update_path)
        else:
            print("corrupted download, failed")
            return "bad_download"
    else:
        return "up-to-date"
