'''
Mukkuru passthrough module\n
Imports utils.archiving\n
'''
import os
import sys
import platform
import subprocess
from subprocess import Popen
import threading
import signal

from flask import Flask, jsonify
from waitress.server import create_server, MultiSocketServer

from utils import archiving
from utils.core import get_config, backend_log, PASSTHROUGH_PORT, AVAILABLE_P_PORTS

passthrough_server = Flask(__name__)

def start_listener(pserver: MultiSocketServer):
    ''' starts waitress server '''
    pserver.run()

def controller(proc: Popen[bytes]) -> MultiSocketServer:
    '''  starts server and setup listeners'''
    pserver = None
    passthrough_port = PASSTHROUGH_PORT
    @passthrough_server.route('/status', methods = 'GET')
    def app_status():
        ''' returns status '''
        status = {}
        status["appid"] = os.environ["SteamAppId"]
        status["status"] = "OK"
        return jsonify(status)
    @passthrough_server.route('/stop', methods = ['POST'])
    def terminate_process():
        ''' terminate process '''
        proc.terminate()
        return jsonify(200)
    @passthrough_server.route('/kill', methods = ['POST'])
    def kill_process():
        ''' kills child process '''
        proc.kill()
        return jsonify(200)
    @passthrough_server.route('/pause', methods = ['POST'])
    def pause_process():
        ''' pauses process '''
        if platform.system() == "Windows":
            proc.pause()
        else:
            os.kill(proc.pid, signal.SIGSTOP)#pylint: disable = E1101
    @passthrough_server.route('/resume', methods = ['POST'])
    def resume_process():
        ''' pauses process '''
        if platform.system() == "Windows":
            proc.resume()
        else:
            os.kill(proc.pid, signal.SIGCONT)#pylint: disable = E1101
    used_ports = 0
    while used_ports < AVAILABLE_P_PORTS:
        try:
            pserver = create_server(passthrough_server, host="localhost", port=passthrough_port)
            threading.Thread(target=start_listener, args=(pserver,)).start()
        except OSError:
            # errno.EADDRINUSE: port already used
            # errno.EACCES: requires elevation
            # errno.EADDRNOTAVAIL: address not available
            # errno.EAFNOSUPPORT: address family not supported
            # besides EADDRINUSE other conditions are unlikely, that's why no check is in place
            used_ports = used_ports + 1
            passthrough_port = passthrough_port + 1
    return pserver

def transparent_execution():
    ''' Enter passthrough mode '''
    user_config = get_config()
    app_id = os.environ["SteamAppId"]
    target_exe = sys.argv[1]
    target_args = sys.argv[2:]
    target_exe = os.path.abspath(target_exe)
    if app_id in user_config["losslessScaling"] and platform.system() == "Linux":
        target_args = [target_exe] + target_args
        target_exe = os.path.expanduser("~/lsfg")
    if app_id in archiving.get_archived_games():
        if not archiving.restore_game(app_id):
            backend_log("Unable to extract game from archive")
            sys.exit(-1)
    process = subprocess.Popen([target_exe] + target_args)
    listener = controller(process)
    process.wait()
    if listener is not None:
        listener.close()
    backend_log("Exiting from passthough mode...")
    sys.exit(process.returncode)
