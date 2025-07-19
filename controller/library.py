# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' library controller module '''
import os
from flask import Blueprint, jsonify, request
from flask import send_from_directory
from library.steam import get_proton_list
from library.games import get_games, scan_games, scan_artwork
from library.games import launch_app, get_username
from library import video
from utils.core import get_config, mukkuru_env

library_controller = Blueprint('library', __name__)

@library_controller.route('/library/proton')
def get_proton():
    ''' list proton builds http '''
    return jsonify(get_proton_list())

#This one must receive POST data
@library_controller.route('/library/add')
def add_game():
    '''add a game manually'''
    #update_games(game_library)
    return "Not implemented"

@library_controller.route('/frontend/video/<source>/<filename>', methods=["GET", "DELETE"])
def video_serve(source, filename):
    '''serve or delete video file'''
    user_config = get_config()
    video_source = user_config["videoSources"][int(source)]
    if request.method == 'DELETE':
        video_path = os.path.join(video_source, filename)
        th = f"{os.path.splitext(filename)[0]}-thumbnail.png"
        th_path = os.path.join(video_source, th)
        os.remove(video_path)
        os.remove(th_path)
        return "200"
    return send_from_directory(video_source, filename)

@library_controller.route('/frontend/music/<source>/<filename>')
def music_serve(source, filename):
    '''serve music files'''
    user_config = get_config()
    music_path = user_config["musicSources"][int(source)]
    return send_from_directory(music_path, filename)

@library_controller.route('/frontend/picture/<source>/<filename>')
def picture_serve(source, filename):
    '''serve music files'''
    user_config = get_config()
    pic_path = user_config["pictureSources"][int(source)]
    return send_from_directory(pic_path, filename)

@library_controller.route('/video/thumbnail/<video_id>', methods = ['POST'])
def set_video_thumbnail(video_id):
    '''update video thumbnail from request'''
    if request.method == 'POST':
        thumbnail = request.get_json()
        video.update_thumbnail(mukkuru_env["video.json"], video_id, thumbnail)
        return "200"
    return "400"

@library_controller.route('/video/screenshot/', methods = ['POST'])
def add_video_screenshot():
    '''update video thumbnail from request'''
    if request.method == 'POST':
        screenshot = request.get_json()
        user_config = get_config()
        save_index = user_config["saveScreenshot"]
        pic_path = user_config["pictureSources"][save_index]
        video.save_screenshot(pic_path, screenshot)
        return "200"
    return "400"

@library_controller.route('/library/scan')
def scan_games_controller():
    ''' http controller for library.games scan_games()  '''
    games = scan_games()
    return jsonify(games)

@library_controller.route('/library/artwork/scan')
def scan_artwork_controller():
    ''' calls artwork scan '''
    scan_artwork()
    return "200"

@library_controller.route('/library/get')
def get_games_controller():
    ''' calls get_games '''
    games = get_games()
    return jsonify(games)

@library_controller.route('/library/launch/<app_id>')
def launch_app_controller(app_id):
    ''' executes library.games.launch_app, returns 200 '''
    launch_app(app_id)
    return "200"

@library_controller.route('/username')
def get_username_controller():
    ''' Gets username '''
    return get_username()
