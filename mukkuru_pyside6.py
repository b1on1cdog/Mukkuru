#!/usr/bin/env python3
""" Using PySide6 for webview """
import sys
import os
#import time
import json
import threading

import requests
from PySide6.QtWidgets import QApplication # pylint: disable=E0611
from PySide6.QtWebEngineWidgets import QWebEngineView # pylint: disable=E0611
from PySide6.QtCore import QUrl, Qt, QTimer, QObject# pylint: disable=E0611
from PySide6.QtWebEngineCore import QWebEngineSettings # pylint: disable=E0611
from PySide6.QtGui import QIcon # pylint: disable=E0611

class Frontend(QObject):
    ''' Frontend class '''
    def __init__(self, fullscreen, app_version):
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--autoplay-policy=no-user-gesture-required'
        self.app = QApplication(sys.argv)
        self.web = QWebEngineView()
        self.web.setWindowTitle(app_version)
        self.web.resize(1280, 800)
        self.web.setCursor(Qt.BlankCursor)
        self.web.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        self.web.setContextMenuPolicy(Qt.NoContextMenu)
        self.fullscreen_state = fullscreen
        self.user_config = None
        if self.fullscreen_state:
            self.web.showFullScreen()
        self.web.loadFinished.connect(self.on_load_finished)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_event)
        self.timer.start(2000)

    def update_event(self):
        ''' Code that will be executed periodically, this code might block UI '''
        threading.Thread(target=self.background_event).start()
        if self.user_config is None:
            return
        if self.fullscreen_state != self.user_config["fullScreen"]:
            self.fullscreen_state = not self.fullscreen_state
            if self.fullscreen_state:
                self.web.showFullScreen()
            else:
                self.web.showNormal()

    def background_event(self):
        ''' update_event code that will run in another thread '''
        self.update_user_config()

    def on_load_finished(self):
        ''' runs when web content fully loaded '''

    def close(self):
        ''' close mukkuru server '''
        self.timer.stop()
        try:
            requests.get("http://localhost:49347/app/exit", timeout=1)
        except (TimeoutError, requests.exceptions.RequestException) as e:
            print(f'request error {e}')

    def start(self):
        ''' show webview '''
        self.web.load(QUrl("http://localhost:49347/frontend/index.html"))
        self.web.show()
        # Execute the app
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "mukkuru.ico")
        self.app.setWindowIcon(QIcon(icon_path))
        self.app.exec()
        self.close()
        sys.exit()

    def update_user_config(self):
        """ Update userConfiguration """
        try:
            response = requests.get("http://localhost:49347/config/get", timeout=1)
            self.user_config = response.json()
        except (TimeoutError, requests.exceptions.RequestException,
                json.decoder.JSONDecodeError, TypeError) as e:
            print(f'request error {e}')
