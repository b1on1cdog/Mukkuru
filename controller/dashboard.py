# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' webui dashboard '''
import os
from pathlib import Path

from flask import Blueprint, request
from flask import send_from_directory
from utils.core import APP_DIR, mukkuru_env
from utils.core import get_config, backend_log, set_alive_status

dashboard_blueprint = Blueprint('library', __name__)

@dashboard_blueprint.route('/<path:path>')
def server_file(path):
    ''' returns dashboard static files '''
    serve_path = os.path.join(APP_DIR, "ui")
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
