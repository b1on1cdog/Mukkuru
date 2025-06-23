# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Using PyWebView for webview '''

import threading
import platform
import time
import json
import requests
import webview

class Frontend:
    ''' Frontend class '''
    def __init__(self, fullscreen, app_version, environ = None):
        self.window = webview.create_window(
            app_version,
            "http://localhost:49347/frontend/",
            fullscreen=fullscreen, width=1280, height=800
        )
        self.fullscreen_state = fullscreen
        self.user_config = None
        self.window.events.closing += self.close
        self.environ = environ

    def start(self):
        ''' start frontend '''
        threading.Thread(target=self.observer).start()
        web_gui = None
        #if self.environ is not None and "gui" in self.environ:
        #    web_gui = self.environ["gui"]
        #    wef_dir = os.path.join(self.environ["root"], "wef_bundle")
        #    sys.path.insert(0, wef_dir)
        #    import_wef(wef_dir)
        if platform.system() == "Windows" and web_gui is None:
            webview.start(icon="ui/mukkuru.ico", user_agent="Mukkuru/Frontend", gui='edgechromium')
        else:
            print(f"Creating weview with : {web_gui}")
            webview.start(icon="ui/mukkuru.ico", user_agent="Mukkuru/Frontend", gui=web_gui)
    def close(self):
        ''' close mukkuru server '''
        requests.get("http://localhost:49347/app/exit", timeout=1)
    def update_user_config(self):
        ''' update config from backend '''
        try:
            response = requests.get("http://localhost:49347/config/get", timeout=1)
            self.user_config = response.json()
        except (TimeoutError, requests.exceptions.RequestException,
                json.decoder.JSONDecodeError, TypeError) as e:
            print(f'request error {e}')

    def observer(self):
        ''' Monitor JS '''
        while True:
            time.sleep(2)
            self.update_user_config()
            user_config = self.user_config
            if user_config["fullScreen"] and not self.fullscreen_state:
                self.window.toggle_fullscreen()
                self.fullscreen_state = True
            elif not user_config["fullScreen"] and self.fullscreen_state:
                self.window.toggle_fullscreen()
                self.fullscreen_state = False
