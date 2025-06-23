# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Handles wef_bundle procedures '''
import platform
import os
import zipfile
from pathlib import Path
import threading
import requests
from view import simple_ui

AARCH = {'x86_64': 'x86_64',
         'AMD64': 'x86_64',
         'aarch64': 'arm64'}.get(platform.machine(), platform.machine())

def download_file_with_progress(url, dest_path, wef_dir, progress_callback=None,on_complete = None):
    ''' download file in a way you can track the progress of it '''
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        total_length = int(r.headers.get('content-length', 0))
        downloaded = 0
        chunk_size = 8192

        mb_size = 1000 * 1000
        mb_total = round(total_length/mb_size, 1)

        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_length and progress_callback:
                        percent = (downloaded / total_length) * 100
                        if downloaded > mb_size:
                            mb = round(downloaded/mb_size, 1)
                            text= f"{str(mb)}mb/{str(mb_total)}mb downloaded"
                            progress_callback(percent, text)
        install_wef_bundle(wef_dir, dest_path)
        if on_complete is not None:
            on_complete()

def install_wef_bundle(wef_dir, file_path):
    ''' Literally does nothing'''
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(wef_dir)
    os.remove(file_path)
    return

def download_wef(wef_dir, on_complete):
    ''' Download wef from cloud '''
    parent = os.path.dirname(os.path.normpath(wef_dir)) + "/"
    output_path = os.path.join(parent, "wef_bundle.zip")
    if Path(output_path).is_file():
        os.remove(output_path)
    update, loop = simple_ui.create_progress_bar("Downloading wef_bundle...")

    repo_url = "https://github.com/b1on1cdog/pyside6_wef"
    platform_suffix = f"{platform.system().lower()}-{AARCH}"
    file_tag = "wef_bundle"
    download_url = f"{repo_url}/releases/download/{file_tag}/wef_bundle-{platform_suffix}.zip"

    download_thread = threading.Thread(target=download_file_with_progress,
                     args=(download_url, output_path, wef_dir, update, on_complete))
    download_thread.start()
    return loop

def pick_wef(wef_dir, wef_ready):
    ''' select wef using file picker '''
    if threading.current_thread() is not threading.main_thread():
        simple_ui.gui_task_queue.put(lambda: pick_wef(wef_dir, wef_ready))
        return
    wef_file = simple_ui.open_filepicker("Select wef_bundle.zip", [("zip", "*.zip")])
    if wef_file is None:
        simple_ui.show_messagebox("Error", "no wef_bundle provided", "Error")
    else:
        install_wef_bundle(wef_dir, wef_file)
        wef_ready()

def complain():
    ''' yes '''
    simple_ui.show_messagebox("Error", "failed to import wef_bundle", "Error")
    os._exit(0)
