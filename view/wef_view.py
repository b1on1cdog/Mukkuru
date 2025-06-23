# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
""" Using wef_bundle for webview """
import os
import stat
from pathlib import Path
import atexit

import platform
import subprocess

from view.wef_bundle import download_wef, pick_wef, complain

class Frontend():
    ''' Frontend class '''
    def __init__(self, fullscreen, app_version, environ = None):
        self.environ = environ
        self.fullscreen = fullscreen
        self.title = app_version
        embedded_wef = os.path.join(environ["app_path"], "wef_bundle")
        self.wef = os.path.join(environ["root"], "wef_bundle")
        self.ready = True
        self.wef_retry = True
        self.proc = None
        exec_name = "wef_bundle"
        if platform.system() == "Windows":
            exec_name = exec_name + ".exe"
        self.exec = os.path.join(self.wef, exec_name)

        if Path(embedded_wef).is_dir():
            self.wef = embedded_wef
        if not Path(self.wef).is_dir():
            self.ready = False
            loop = download_wef(self.wef, self.wef_ready)
            loop()

    def wef_ready(self, *_):
        ''' executes after finishing installing wef '''
        if Path(self.exec).is_file():
            self.ready = True
            self.start()
        elif self.wef_retry:
            self.wef_retry = False
            pick_wef(self.wef, self.wef_ready)
        else:
            complain()
    def close(self):
        ''' closes ui'''
        print("closing UI...")
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
    def start(self):
        ''' show webview '''
        if self.ready is False:
            return
        proc_flags = []
        url = 'http://localhost:49347'
        proc_flags.append(self.exec) # executable
        proc_flags.extend(["--title", self.title])
        proc_flags.extend(["--url", url])
        if self.fullscreen:
            proc_flags.extend(["--fullscreen"])
        os.environ["BACKEND_PATH"] = self.environ["app_path"]
        os.environ["WEF_ICON_PATH"] = os.path.join(self.environ["app_path"], "ui", "mukkuru.ico")
        os.environ["WEF_DISABLE_CONTEXT_MENU"] = "1"
        os.environ["WEF_HIDE_CURSOR"] = "1"
        #os.environ["BACKEND_URL_BIND"] = url + '/alive'
        os.environ["BACKEND_PID_BIND"] = url + '/alive'
        os.environ["BACKEND_PID"] = str( os.getpid())
        # os.environ["WEF_EXIT_URL"]  overrides exit url
        # os.environ["WEF_CONFIG_URL"] overrides config url
        if platform.system() != "Windows":
            current_permissions = os.stat(self.exec).st_mode
            os.chmod(self.exec, current_permissions | stat.S_IXUSR)
        self.ready = False
        self.proc = subprocess.Popen(proc_flags)
        atexit.register(self.close)
