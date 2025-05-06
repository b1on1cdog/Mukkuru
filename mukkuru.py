#!/usr/bin/env python3
""" Using PySide6 for webview """
import sys
import os
import threading
import time

import requests
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtGui import QIcon

import backend

def main():
    '''Starts a webview'''
    #pid = os.getpid()
    try:
        requests.get("http://localhost:49347/ping", timeout=5)
        print("Mukkuru backend is already running, skipping execution...")
    except requests.exceptions.RequestException:
        threading.Thread(target=backend.main).start()

    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--autoplay-policy=no-user-gesture-required'

    app = QApplication(sys.argv)
    # Create the QWebEngineView
    web = QWebEngineView()
    time.sleep(0.1)
    web.setWindowTitle(backend.APP_VERSION)
    web.resize(1280, 800)
    web.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
    web.setContextMenuPolicy(Qt.NoContextMenu)
    if backend.is_fullscreen():
        web.showFullScreen()
    # Get URL
    web.load(QUrl("http://localhost:49347/frontend/index.html"))
    web.show()
    # Execute the app
    app.setWindowIcon(QIcon("mukkuru.ico"))
    app.exec()
    backend.quit_app()
    sys.exit()

if __name__ == "__main__":
    main()
