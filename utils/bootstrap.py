# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
'''
Download and extraction utils.\n
bootstrap do not import other Mukkuru libraries except utils.core.\n
'''
import os
import re
import platform
import subprocess
import shutil
import zipfile
import hashlib
import threading
from typing import Optional, Callable
from pathlib import Path

import requests
from utils.core import mukkuru_env, format_executable, sanitized_env

REQUESTS: requests = requests

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
    ''' Callback to update global progress bar\n
    :param int downloaded: Counter of processed units\n
    :param int total: Counter of total units\n
    '''
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

def download_file(url, path: str, progress_callback:Callable=None, chunk_size=8192):
    '''Download file from URL with optional progress callback\n
    :param str path: path of output file
    :param typing.Callable progress_callback: callback function to update progress'''
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

def get_unrar() -> Optional[str]:
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

def get_7z() -> Optional[str]:
    '''
    Gets 7z path\n
    Returns None if 7z is not installed\n'''
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

def compress_7z(files: list, output_file: str, progress_callback: Callable = None) -> bool:
    ''' Compress list of files using 7z\n
    :param list files: list of files to add to archive\n
    :param str output_file: path where compressed archive is going to be stored\n
    :param Callable progress_callback: function to report progress to\n
    :returns: a boolean indicating operation success\n
    '''
    suppress_output = ["-bsp1", "-bso0"]
    process = subprocess.Popen([get_7z(), 'a', output_file] + files + suppress_output,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=1)
    progress_pattern = re.compile(r"(\d+)%")
    for line in process.stdout:
        if progress_callback is None:
            break
        line = line.strip()
        match = progress_pattern.search(line)
        if match:
            percent = int(match.group(1))
            progress_callback(percent, 100)
    process.wait()
    return process.returncode == 0

def extract_rar(filename: str, output_dir:str) -> None:
    ''' Extracts .rar archive\n
    :param str filename: Filename of archive to extract\n
    :param str output_dir: Dir where to extract the files to\n '''
    unrar = get_unrar()
    if unrar is None:
        return "Unable to extract file, no decompressor available"
    subprocess.run([unrar, "x", filename, output_dir], check=False, env=sanitized_env())

def extract_7z(filename: str, output_dir: str, callback: Callable = None) -> bool:
    ''' Extracts archive using 7z\n
    :param str filename: filename of archive\n
    :param str output_dir: path of output where to extract files\n
    :param Callable callback: function to report the operation progress\n
    :returns: boolean indicating operation success\n
    '''
    zz = get_7z()
    if zz is None:
        print("Unable to extract file, no decompressor available")
        return False
    suppress_output = ["-bsp1", "-bso0"]
    process = subprocess.Popen([zz, "x", filename, f"-o{output_dir}"] + suppress_output,
                               stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=1, env=sanitized_env())
    progress_pattern = re.compile(r"(\d+)%")
    for line in process.stdout:
        if callback is None:
            break
        line = line.strip()
        match = progress_pattern.search(line)
        if match:
            percent = int(match.group(1))
            callback(percent, 100)
    process.wait()
    return process.returncode == 0

def extract_zip(filename: str, output_dir: str) -> bool:
    ''' Extract .zip file\n
    :param str filename: filename of archive to extract\n
    :param str output_dir: path of dir where files will be extracted\n'''
    with zipfile.ZipFile(filename,"r") as zip_ref:
        zip_ref.extractall(output_dir)
    return True

def extract_archive(filename: str, output_dir: str, callback: Callable = None) -> bool:
    ''' extract archive '''
    if filename.endswith(".zip"):
        return extract_zip(filename, output_dir)
    #elif filename.endswith(".rar"):
    #    return extract_rar(filename, output_dir)
    elif filename.endswith(".7z") or filename.endswith(".exe") or filename.endswith(".rar"):
        return extract_7z(filename, output_dir, callback)
    else:
        print("Unknown compression")
        return False

def get_ffmpeg() -> Optional[str]:
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

def get_userprofile_folder(desired_dir: str) -> Optional[str]:
    ''' Retrieves a user directory regardless of OS\n
    :param str desired_dir: Desired user directory (Music, Downloads, Pictures, etc) 
    :returns: Path to desired Folder as string (ex: /home/user/Downloads)'''
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


def build_file_tree(root_path: str) -> dict:
    ''' return files and folders as a dictionary '''
    tree = {}

    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            tree.setdefault("folders", []).append(item)
        else:
            tree.setdefault("files", []).append(item)
    return tree

def sha256_file(path: str, chunk_size:int=8192) -> str:
    ''' calculate sha256 of file in chunks
    :param str path: Path of file to hash
    :param int chunk_size: Size of chunks to load in memory
    :return: computed sha256 as string, lowercase
    '''
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_dir_size(start_path:str = '.') -> int:
    ''' get's file size of a folder '''
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def has_enough_space(target_path: str, required_bytes: int) -> bool:
    ''' returns whether target_path has enough disk space
    :param str target_path: Path of file to write, can also be a directory
    :param int required_bytes: Number of bytes of the file to write
    '''
    usage = shutil.disk_usage(target_path)
    free_bytes = usage.free
    return free_bytes >= required_bytes

def terminate_mukkuru_backend(app_port: int):
    '''
    Sends an /app/exit request to mukkuru port
    :param int app_port: Mukkuru App port
    '''
    quit_url = f"http://localhost:{app_port}/app/exit"
    try:
        requests.get(quit_url, stream=True, timeout=0.15)
        threading.Event().wait(1.25)
        print("Previous Mukkuru instance was killed successfully")
    except requests.exceptions.RequestException:
        pass
