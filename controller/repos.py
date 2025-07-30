# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' repos controller module '''
import threading
from flask import Blueprint, jsonify
from utils import expansion

repos_blueprint = Blueprint('repos', __name__)

@repos_blueprint.route("/repos/patches")
def get_patches():
    ''' returns a json of repo patches '''
    patches = expansion.get_patches()
    return jsonify(patches, 200)

@repos_blueprint.route("/repos/patches/<appid>/<patch_index>", methods = ['POST'])
def install_patch(appid, patch_index):
    ''' expansion.install_patch_from_index controller '''
    thread = threading.Thread(target=expansion.install_patch_from_index,
                     args=(appid, patch_index))
    thread.start()
    return jsonify("OK", 200)
