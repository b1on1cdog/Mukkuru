#!/usr/bin/env python3
import sys
import os
import subprocess, time
import requests # type: ignore

from PySide6.QtWidgets import QApplication # type: ignore
from PySide6.QtWebEngineWidgets import QWebEngineView # type: ignore
from PySide6.QtCore import QUrl, Qt # type: ignore
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage# type: ignore
from PySide6.QtGui import QContextMenuEvent# type: ignore

def main():
    pid = os.getpid()
    try:
        r=requests.get("http://localhost:49347/ping")
        print("Mukkuru backend is already running, skipping execution...")
    except:
        p = subprocess.Popen([sys.executable, 'backend.py'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT)
        time.sleep(0.2)

    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--autoplay-policy=no-user-gesture-required'

    app = QApplication(sys.argv)
    # Create the QWebEngineView
    web = QWebEngineView()

    '''
    # Use this for persistent localStorage
    storage_path = os.path.join(QDir.homePath(), ".mukkuru")
    profile = QWebEngineProfile("Mukkuru", app)
    profile.setPersistentStoragePath(storage_path)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    page = QWebEnginePage(profile, web)
    web.setPage(page)
    '''
    web.setWindowTitle("Mukkuru v0.1.4")
    web.resize(1280, 800)
    web.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
    web.setContextMenuPolicy(Qt.NoContextMenu)

  #  web.showFullScreen()

    # Get URL
    web.load(QUrl(f"http://localhost:49347/frontend/index.html?pid={pid}"))
    web.show()
    # Execute the app
    app.exec()
    sys.exit()

if __name__ == "__main__":
    main()