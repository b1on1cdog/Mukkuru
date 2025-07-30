#pylint: disable=W0603
''' use a installed browser as ui '''
import os
import subprocess
import platform
from pathlib import Path
import shutil
import tempfile
import uuid
import time
from urllib.parse import urlparse
from utils.core import sanitized_env, backend_log

BROWSER_PROCESS = None

linux_browser_paths = [
    r"/usr/bin/google-chrome",
    r"/usr/bin/microsoft-edge",
    r"/usr/bin/brave-browser",
    r"/usr/bin/chromium",
    # Web browsers installed via flatpak portals
    r"/run/host/usr/bin/google-chrome",
    r"/run/host/usr/bin/microsoft-edge",
    r"/run/host/usr/bin/brave-browser",
    r"/run/host/usr/bin/chromium",
    # Web browsers installed via snap
    r"/snap/bin/chromium",
    r"/snap/bin/brave-browser",
    r"/snap/bin/google-chrome",
    r"/snap/bin/microsoft-edge",
]

windows_browser_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
]

def get_flatpak() -> str:
    ''' returns flatpak path '''
    return shutil.which("flatpak") or "/usr/bin/flatpak"

def is_flatpak_firefox_installed() -> bool:
    ''' [Linux] checks whether firefox is installed '''
    if platform.system() != "Linux":
        return False
    try:
        subprocess.check_output([get_flatpak(), "info", "org.mozilla.firefox"],
                                stderr=subprocess.DEVNULL, text=True, env=sanitized_env())
        return True
    except subprocess.CalledProcessError as e:
        backend_log(f"failed checking Flatpak {e.output}")
        return False
    except FileNotFoundError:
        backend_log("Flatpak is not installed")
        return False

def search_firefox() -> list:
    ''' Search for firefox install '''
    firefox_paths = ["/snap/bin/firefox", "/opt/firefox/firefox", "/usr/bin/firefox"]
    is_flatpak = is_flatpak_firefox_installed()
    if is_flatpak:
        return [get_flatpak(), "run", "org.mozilla.firefox"]
    if not is_flatpak:
        for firefox in firefox_paths:
            if Path(firefox).is_file():
                return [firefox]
    backend_log("Unable to find firefox bin")
    return [None]

def run_firefox(url, profile_dir = None) -> None:
    ''' run firefox as ui '''
    proc_flags = []
    firefox = search_firefox()
    proc_flags.extend(firefox)
    proc_flags.append("--no-remote")
    proc_flags.append("--kiosk")
    if profile_dir is not None:
        proc_flags.extend(["--profile", profile_dir])
    proc_flags.append("-private-window")
    proc_flags.append(url)
    global BROWSER_PROCESS
    BROWSER_PROCESS = subprocess.Popen(proc_flags, env=sanitized_env())

def find_browser_path() -> str:
    ''' look for an installed browser '''
    browser_paths = []
    if platform.system() == "Linux":
        browser_paths = linux_browser_paths
    elif platform.system() == "Windows":
        browser_paths = windows_browser_paths
    for browser_path in browser_paths:
        if Path(browser_path).is_file():
            return browser_path
    return None

class Frontend:
    ''' uses an installed browser as ui '''
    def __init__(self, fullscreen = True, app_version = "", environ = None):
        if environ is not None:
            pass
        self.use_firefox = search_firefox()[0] is not None
        self.url = 'http://localhost:49347/frontend/frame.html'
        self.fullscreen = fullscreen
        # override
        self.fullscreen = True
        #
        self.app_title = app_version
        self.app_port = urlparse(self.url).port
        self.browser_command = None
        #self.browser_pid = 0
        self.browser_path = find_browser_path()
        self.profile_dir_prefix: str = "mukkuru"
        self.profile_dir = os.path.join(
            tempfile.gettempdir(), self.profile_dir_prefix + uuid.uuid4().hex
        )
        os.mkdir(self.profile_dir)
        self.browser_command = [
            self.browser_path,
            f"--user-data-dir={self.profile_dir}",
            "--user-agent=Mukkuru/kioskMode",
            "--new-window",
            "--no-default-browser-check",
            "--allow-insecure-localhost",
            "--no-first-run",
            "--disable-sync",
            ]
        if self.fullscreen:
            self.browser_command.append("--kiosk")
        self.browser_command.extend(["--guest", self.url])

    def start(self) -> None:
        ''' starts frontend '''
        if self.use_firefox:
            return run_firefox(self.url)
        backend_log("using flaswebgui instead of firefox")
        if self.browser_path is None:
            backend_log("No browser available")
            os._exit(0)
        try:
            global BROWSER_PROCESS
            BROWSER_PROCESS = subprocess.Popen(self.browser_command)
            BROWSER_PROCESS.wait()
            backend_log("Browser exited, closing")
            self.close(True)
        except (ProcessLookupError, OSError):
            pass

    def close(self, should_kill = False) -> None:
        ''' close ui '''
        if self.use_firefox and search_firefox()[0] == get_flatpak():
            proc_flags = [get_flatpak()]
            proc_flags.extend(["kill", "org.mozilla.firefox"])
            backend_log("killing flatpak firefox")
            subprocess.run(proc_flags, check=False, env=sanitized_env())
        else:
            if BROWSER_PROCESS is not None:
                BROWSER_PROCESS.terminate()
                time.sleep(1)
                BROWSER_PROCESS.kill()
            shutil.rmtree(self.profile_dir)
        if should_kill:
            os._exit(0)
