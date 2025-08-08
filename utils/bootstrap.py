# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' download and extraction utils '''
import os
import platform
import subprocess
import shutil
import zipfile
import hashlib
import threading
from pathlib import Path

import requests
from utils.core import mukkuru_env, format_executable, sanitized_env

if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
    import uuid

operation_progress = {
    "active" : False,
    "downloaded" : 0,
    "progress" : 0,
    "total" : 0,
    "context" : "unknown",
}

def global_progress_callback(downloaded: int, total: int) -> None:
    ''' handles progress in a global context '''
    operation_progress["downloaded"] = downloaded
    operation_progress["total"] = total
    if total == 0:
        total = 0.1
    operation_progress["progress"] = (downloaded/total)*100
    operation_progress["active"] = True

def set_global_progress_context(title: str) -> None:
    ''' sets parameter as global_progress title '''
    operation_progress["context"] = title
    operation_progress["active"] = True

def clear_global_progress() -> None:
    ''' clears operation_progress '''
    operation_progress["downloaded"] = 0
    operation_progress["total"] = 0
    operation_progress["progress"] = 0
    operation_progress["active"] = False
    operation_progress["context"] = "unknown"

def download_file(url, path: str, progress_callback=None, chunk_size=8192):
    '''Download file from URL with optional progress callback'''
    with requests.get(url, stream=True, timeout=20) as response:
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

def get_unrar():
    ''' gets unrar path '''
    unrar_paths = [
        shutil.which("unrar"),
        os.path.join(mukkuru_env["root"], "tools", format_executable("unrar")),
        os.path.join(mukkuru_env["root"], "tools", format_executable("unar")),
    ]
    for unrar_path in unrar_paths:
        if unrar_path and Path(unrar_path).exists():
            return unrar_path
    return None

def get_7z():
    ''' gets 7z path '''
    z_paths = [
        shutil.which("7z"),
        os.path.join(mukkuru_env["root"], "tools", format_executable("7z")),
        shutil.which("7za"),
        os.path.join(mukkuru_env["root"], "tools", format_executable("7za")),
    ]
    wz_paths = [
        os.path.join(os.environ.get("ProgramFiles", ""), "7-Zip", "7z.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "7-Zip", "7z.exe")
    ]
    for z_path in z_paths:
        if z_path and Path(z_path).exists():
            return z_path
    if platform.system() == "Windows":
        for wz_path in wz_paths:
            if Path(wz_path).exists():
                return wz_path
    return None

def extract_rar(filename: str, output_dir:str):
    ''' extract .rar file '''
    unrar = get_unrar()
    if unrar is None:
        return "Unable to extract file, no decompressor available"
    subprocess.run([unrar, "x", filename, output_dir], check=False, env=sanitized_env())

def extract_7z(filename: str, output_dir: str):
    ''' extract .7z file'''
    zz = get_7z()
    if zz is None:
        return "Unable to extract file, no decompressor available"
    subprocess.run([zz, "x", filename, f"-o{output_dir}"], check=False, env=sanitized_env())

def extract_zip(filename: str, output_dir: str):
    ''' extract .zip file '''
    with zipfile.ZipFile(filename,"r") as zip_ref:
        zip_ref.extractall(output_dir)

def extract_archive(filename: str, output_dir: str):
    ''' extract archive '''
    if filename.endswith(".zip"):
        return extract_zip(filename, output_dir)
    #elif filename.endswith(".rar"):
    #    return extract_rar(filename, output_dir)
    elif filename.endswith(".7z") or filename.endswith(".exe") or filename.endswith(".rar"):
        return extract_7z(filename, output_dir)
    else:
        return "unknown compression"

def get_ffmpeg():
    ''' finds ffmpeg path '''
    ffmpeg_paths = [
        shutil.which("ffmpeg"),
        os.path.join(mukkuru_env["root"], "tools", format_executable("ffmpeg"))
    ]
    for ffmpeg_path in ffmpeg_paths:
        if ffmpeg_path and Path(ffmpeg_path).exists():
            return ffmpeg_path
    return None

if platform.system() == "Windows":
    SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
    SHGetKnownFolderPath.argtypes = [ctypes.POINTER(ctypes.c_byte),
                                     wintypes.DWORD, wintypes.HANDLE,
                                     ctypes.POINTER(ctypes.c_wchar_p)]
    SHGetKnownFolderPath.restype = ctypes.HRESULT
    def get_known_folder_path(folder_id):
        ''' [Windows only] determines user folder '''
        fid = (ctypes.c_byte * 16).from_buffer_copy(folder_id.bytes_le)
        path_ptr = ctypes.c_wchar_p()
        if SHGetKnownFolderPath(fid, 0, 0, ctypes.byref(path_ptr)) != 0:
            raise ctypes.WinError()
        return path_ptr.value

def get_userprofile_folder(desired_dir: str):
    ''' returns a user folder (Music, Videos, Downloads, Pictures)'''
    home_dir = Path('~').expanduser()
    user_dir = os.path.join(home_dir, desired_dir)
    if Path(user_dir).is_dir():
        return user_dir
    if platform.system() == "Windows":
        win_uuids = {
            "Videos" : "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}",
            "Downloads" : "{374DE290-123F-4565-9164-39C4925E467B}",
            "Pictures" : "{33E28130-4E1E-4676-835A-98395C3BC3BB}",
            "Music" : "{4BD8D571-6D19-48D3-BE97-422220080E43}",
        }
        if desired_dir in win_uuids:
            return get_known_folder_path(uuid.UUID(win_uuids[desired_dir]))
    elif platform.system() == "Linux":
        linux_path_name = desired_dir.capitalize()
        if linux_path_name == "DOWNLOADS":
            linux_path_name = "DOWNLOAD"
        result = subprocess.run(['xdg-user-dir', linux_path_name],
                                 capture_output=True, text=True,
                                 check=False, env=sanitized_env())
        return result.stdout.strip() if result.returncode == 0 else None
    return None


def build_file_tree(root_path: str):
    ''' return files and folders as a dictionary '''
    tree = {}

    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            tree.setdefault("folders", []).append(item)
        else:
            tree.setdefault("files", []).append(item)
    return tree

def sha256_file(path, chunk_size=8192):
    ''' calculate sha256 of file in chunks '''
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def terminate_mukkuru_backend(app_port: int):
    ''' send a quit request to mukkuru port '''
    quit_url = f"http://localhost:{app_port}/app/exit"
    try:
        requests.get(quit_url, stream=True, timeout=0.15)
        threading.Event().wait(1.25)
        print("Previous Mukkuru instance was killed successfully")
    except requests.exceptions.RequestException:
        pass
