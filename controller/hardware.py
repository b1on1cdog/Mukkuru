# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' hardware controller module '''
from flask import Blueprint, jsonify
from utils import hardware_if
from utils.core import app_version

hardware_controller = Blueprint('hardware_controller', __name__)

@hardware_controller.route("/hardware/network")
def connection_status():#segmentation fault
    ''' returns a json with connection status'''
    status = hardware_if.connection_status()
    return jsonify(status)

@hardware_controller.route("/hardware/battery")
def battery_info():
    ''' Return a JSON containing battery details '''
    return jsonify(hardware_if.get_battery())

@hardware_controller.route("/hardware")
def harware_info():
    ''' get hardware info as a json '''
    hardware_info = hardware_if.get_info()
    hardware_info["app_version"] = app_version()
    return jsonify(hardware_info)
