# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' webui dashboard '''
import os
from pathlib import Path

from flask import Blueprint, request, redirect, jsonify
from flask import send_from_directory, send_file, url_for
from utils.core import APP_DIR, mukkuru_env
from utils.core import get_config, backend_log, set_alive_status
from utils.bootstrap import build_file_tree, get_userprofile_folder

dashboard_blueprint = Blueprint('library', __name__)

@dashboard_blueprint.route('/<path:path>')
def server_file(path: str):
    ''' returns dashboard static files '''
    serve_path = os.path.join(APP_DIR, "ui")
    if path.startswith("thumbnails/") or path.startswith("hero/"):
        return send_from_directory(mukkuru_env["root"], path, mimetype='image/jpeg')
    if path == "dashboard":
        path = "dashboard.html"
    return send_from_directory(serve_path, path)

@dashboard_blueprint.route('/upload', methods=['POST'])
def upload():
    ''' receive files as chunks from dashboard uploads '''
    file = request.files['chunk']
    filename = request.form['filename']
    chunk_index = int(request.form['chunkIndex'])
    chunk_size = int(request.form['chunkSize'])
    total_chunks = int(request.form['totalChunks'])

    video_files = ["mp4", "m4v"]
    image_files = ["png", "jpg", "webm"]
    music_files = ["mp3", "m4a"]
    #allowed_files = []
    # To-do: allow user to store these files in another drive
    # To-do: allow users to move and/or store files in OS user folder
    # To-do: restrict what file formats can be received
    cmd = None
    alt_cmd = None
    value = None
    file_extension = Path(filename).suffix.replace(".", "")
    user_config = get_config()
    if file_extension in video_files:
        upload_folder = user_config["videoSources"][0]
        cmd = "playVideo"
        alt_cmd = "reloadVideos"
        value = f"video/0/{filename}"
    elif file_extension in image_files:
        upload_folder = os.path.join(mukkuru_env["root"], "pictures")
        cmd = "openPicture"
        alt_cmd = "reloadPictures"
        value = f"pictures/0/{filename}"
    elif file_extension in music_files:
        upload_folder = os.path.join(mukkuru_env["root"], "music")
        cmd = "playAudio"
        alt_cmd = "reloadAudios"
        value = f"music/0/{filename}"
    else:
        upload_folder = os.path.join(mukkuru_env["root"], "miscellaneous")

    save_path = os.path.join(upload_folder, filename)
    os.makedirs(upload_folder, exist_ok=True)

    if chunk_index == 0:
        backend_log(f"downloading {filename}")
        if Path(save_path).exists():
            os.remove(save_path)
    with open(save_path, 'ab') as f:
        f.seek(chunk_index * chunk_size)
        f.write(file.read())
    if (chunk_index + 1) == total_chunks and cmd is not None:
        user_config = get_config()
        status = {}
        if user_config["autoPlayMedia"]:
            status["command"] = cmd
        else:
            status["command"] = alt_cmd
        status["value"] = value
        set_alive_status(status)
    return 'Chunk received', 200

@dashboard_blueprint.route('/dashboard', methods=['POST'])
def main_dashboard():
    ''' dashboard page '''
    serve_path = os.path.join(APP_DIR, "ui")
    return send_from_directory(serve_path, "dashboard.html")

@dashboard_blueprint.route('/')
@dashboard_blueprint.route('/index.html')
def server_redirect():
    ''' returns main dashboard page'''
    return  redirect(url_for('library.main_dashboard'), code=301)

@dashboard_blueprint.route('/list/')
def get_base_folders_list():
    ''' returns a dictionary of navigatable folders'''
    base_paths = {
        "folders" : list(get_base_paths_dir().keys())
    }
    return jsonify(base_paths)

def get_base_paths_dir():
    ''' returns the actual directory of base paths '''
    user_config = get_config()
    path_dirs = {
        "miscellaneous" : os.path.join(mukkuru_env["root"], "miscellaneous"),
        "downloads" : get_userprofile_folder("Downloads"),
        "video" : user_config["videoSources"][0],
        "music" : user_config["musicSources"][0],
        "pictures" : user_config["pictureSources"][0],
    }
    for _, path_dir in path_dirs.items():
        os.makedirs(path_dir, exist_ok=True)
    return path_dirs

def get_base_path(base_path):
    ''' get directories that allow file download '''
    base_dirs = get_base_paths_dir()
    if base_path in base_dirs:
        return build_file_tree(base_dirs[base_path])
    return {}

def get_target_dir(path):
    ''' gets a target dir from a path '''
    base_paths = get_base_paths_dir()
    parts = path.split('/')
    last_part_index = len(parts)-1
    if parts[last_part_index] == '':
        parts.pop(last_part_index)
    base_path = parts.pop(0)
    if base_path not in base_paths:
        return "[ERR]"
    if len(parts) == 0:
        return base_paths[base_path]
    target_dir = os.path.join(base_paths[base_path], *parts)
    return target_dir

@dashboard_blueprint.route('/list/<path:path>')
def get_files_list(path):
    ''' returns a dictionary representing files '''
    print(f"access to path {path} requested")
    target_dir = get_target_dir(path)
    if target_dir == "[ERR]":
        return "Permission denied", 403
    if not Path(target_dir).exists():
        return "File do not exists", 404
    if Path(target_dir).is_file():
        # We cannot list a file
        # So i'm going to assume user wants to download it
        return download_file_item(path)
    file_tree = build_file_tree(target_dir)
    backend_log(f"listing {target_dir}")
    return jsonify(file_tree)

@dashboard_blueprint.route('/download/<path:path>')
def download_file_item(path):
    ''' provides a file download to browser '''
    print(f"download from path {path} requested")
    target_dir = get_target_dir(path)
    if target_dir == "[ERR]":
        return "Permission denied", 403
    backend_log(f"downloading {target_dir}")
    return send_file(target_dir, as_attachment=True)
