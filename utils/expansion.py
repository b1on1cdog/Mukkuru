''' Mukkuru module for addons handling\n
Imports library.(games, steam) utils.(bootstrap, hardware_info, updater)'''
import os
import sys
import shutil
import time
import json
import platform
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from functools import lru_cache
import requests
from utils.core import mukkuru_env, get_config, update_config, backend_log
from utils.core import APP_DIR, sanitized_env, ternary, format_executable
from utils import bootstrap, hardware_if, updater
from library import steam
from library.games import get_games, update_games, scan_games

def get_localization() -> dict:
    ''' Returns a localization dictionary '''
    user_config = get_config()
    language = user_config["language"]
    loc_path = f'{APP_DIR}/ui/translations.json'
    with open(Path(loc_path),encoding='utf-8') as f:
        localization = json.load(f)
        if language in localization:
            localization = localization[language]
            localization["available"] = True
            return localization
    localization = {"available" : False}
    return localization

def translate_str(loc_key: str, default_string = None):
    ''' returns a localized string, returns original if missing '''
    if default_string is None:
        default_string = loc_key
    localization = get_localization()
    if loc_key in localization:
        return localization[loc_key]
    return default_string

def copy_patch(source_dir: str, destination_dir: str) -> None:
    ''' copy/merge directories for patch install '''
    if source_dir.endswith(".exe/*"):
        print("extracting exe file")
        source_dir = source_dir.replace(".exe/*", ".exe")
        bootstrap.extract_archive(source_dir, destination_dir)
        return
    if source_dir.endswith("*"):
        filename = Path(urlparse(source_dir).path).name
        filename = filename.replace("*", "")
        source_dir = Path(source_dir).parent.absolute()
        for file in os.listdir(source_dir):
            if file.startswith(filename):
                copy_patch(os.path.join(source_dir, file), destination_dir)
        return
    elif Path(source_dir).is_file():
        print(f"copy {source_dir} -> {destination_dir}")
        shutil.copy2(source_dir, destination_dir)
    elif Path(source_dir).is_dir():
        print(f"copytree {source_dir} -> {destination_dir}")
        shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)
    elif not Path(source_dir).exists():
        print(f"{source_dir} do not exists")
    else:
        print(f"copy_patch {source_dir} -> {destination_dir} ignored")

def install_patch(game_id: str, patch: dict) -> None:
    ''' install patches in game '''
    games = get_games()
    if game_id not in games:
        print("failed to install patch : game not installed")
        return
    if "InstallDir" not in games[game_id]:
        print("failed to install patch : no install path")
        return
    install_dir = games[game_id]["InstallDir"]
    source_archive = patch["filename"]
    output_dir = os.path.join(mukkuru_env["root"], "misc", "patch_wd")
    source_archive = os.path.join(output_dir, source_archive)
    os.makedirs(output_dir, exist_ok=True)
    bootstrap.extract_archive(source_archive, output_dir)
    source = patch["source"]
    destination = patch["destination"]
    destination = destination.replace("$GAME_DIR", install_dir)
    source = os.path.join(output_dir, source)
    copy_patch_files_str = translate_str("CopyingPatchFiles", "Copying patch files....")
    bootstrap.set_global_progress_context(copy_patch_files_str)
    copy_patch(source, destination)
    shutil.rmtree(output_dir, ignore_errors=True)
    user_config = get_config()
    user_config["patches"].append(patch["id"])
    update_config(user_config)
    get_patches.cache_clear()
    bootstrap.clear_global_progress()

def download_patch(patch_url: str, filename=None) -> None:
    '''
    Downloads patch for game\n
    :param str patch_url: patch download url\n
    '''
    output_dir = os.path.join(mukkuru_env["root"], "misc", "patch_wd")
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)
    if filename is not None:
        bootstrap.set_global_progress_context(f'{translate_str("Downloading")} {filename}...')
        output_dir = os.path.join(output_dir, filename)
    bootstrap.download_file(patch_url, output_dir,
                            progress_callback=bootstrap.global_progress_callback)

@lru_cache(maxsize=1)
def get_patches() -> dict:
    ''' fetch patches from repo '''
    patches = {}
    user_config = get_config()
    repos = user_config["repos"]
    for repo in repos:
        if not repo.endswith("/"):
            repo = f"{repo}/"
        repo = f"{repo}mukkuru/patches.json"
        try:
            r = requests.get(repo, stream=True, timeout=20)
            content = r.json()
        except (requests.exceptions.RequestException,
                requests.exceptions.JSONDecodeError):
            return patches
        patches.update(content)
    for _, patch_list in patches.items():
        for i in reversed(range(len(patch_list))):
            patch = patch_list[i]
            if patch["id"] in user_config["patches"]:
                patch["installed"] = True
            else:
                patch["installed"] = False
            adult_patch = "adult" in patch and patch["adult"]
            if adult_patch and not user_config["adultContent"]:
                del patch_list[i]
    return patches

def get_packages() -> dict:
    ''' list installed and downloadable patches '''
    packages = {}
    user_config = get_config()
    repos = user_config["repos"]
    for repo in repos:
        if not repo.endswith("/"):
            repo = f"{repo}/"
        repo = f"{repo}mukkuru/packages.json"
        try:
            r = requests.get(repo, stream=True, timeout=20)
            content = r.json()
        except (requests.exceptions.RequestException,
                requests.exceptions.JSONDecodeError):
            return packages
        packages.update(content)
    return packages

def install_patch_from_index(app_id: str, patch_index: str) -> None:
    ''' downloads and install game patch '''
    backend_log(f"installing patch {patch_index} for {app_id}")
    bootstrap.set_global_progress_context(translate_str("Starting", "Starting..."))
    patch_index = int(patch_index)
    patches = get_patches()
    patch = patches[app_id][patch_index]
    download_url = patch["assets"]["universal"]
    patch_filename = patch["filename"]
    try:
        download_patch(download_url, patch_filename)
    except requests.exceptions.RequestException as e:
        backend_log(f"download failed due to {e}")
        bootstrap.set_global_progress_context("Download failed")
        time.sleep(3)
        bootstrap.clear_global_progress()
        return
    bootstrap.set_global_progress_context(f'{translate_str("Extracting")} {patch_filename}')
    install_patch(app_id, patch)

def install_decky_plugin(zip_path: str) -> bool:
    ''' Installs Decky plugin from Zip file '''
    decky_plugin_dir = os.path.expanduser("~/homebrew/plugins")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            temp_dir: str = "/tmp/decky_plugin_install"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            zip_ref.extractall(temp_dir)
            for root, _, files in os.walk(temp_dir):
                if "plugin.json" in files:
                    plugin_folder: str = root
                    plugin_name: str = os.path.basename(plugin_folder)
                    dest_dir: str = os.path.join(decky_plugin_dir, plugin_name)
                    if os.path.exists(dest_dir):
                        shutil.rmtree(dest_dir)
                    shutil.move(plugin_folder, dest_dir)
                    print(f"Installed plugin to: {dest_dir}")
                    return True
            backend_log("No valid Decky plugin found in ZIP.")
            return False
    except (OSError, PermissionError) as e:
        backend_log(f"Failed to install plugin: {e}")
        return False
# Not so related to addons >

def add_to_startup_macos() -> bool:
    ''' (MacOS) Set Mukkuru to open at user login, uses LaunchAgents'''
    mukkuru_service = []
    mukkuru_service.append('<plist version="1.0">')
    mukkuru_service.append('<dict>')
    mukkuru_service.append('<key>Label</key>')
    mukkuru_service.append('<string>com.panyolsoft.mukkuru</string>')
    mukkuru_service.append('<key>ProgramArguments</key>')
    mukkuru_service.append('<array>')
    mukkuru_service.append("\t<string>open</string>")
    mukkuru_service.append("\t<string>-a</string>")
    mukkuru_service.append("\t<string>/Applications/Mukkuru.app</string>")
    mukkuru_service.append('</array>')
    mukkuru_service.append('<key>RunAtLoad</key>')
    mukkuru_service.append('<true/>')
    mukkuru_service.append('</dict>')
    mukkuru_service.append('</plist>')
    mukkuru_service_path = os.path.expanduser("~/Library/LaunchAgents/")
    os.makedirs(mukkuru_service_path, exist_ok=True)
    mukkuru_service_path = os.path.join(mukkuru_service_path, "com.panyolsoft.mukkuru.plist")
    with open(mukkuru_service_path,"w", encoding="utf-8") as file:
        file.write("\n".join(mukkuru_service))
    os.chmod(mukkuru_service_path, 0o644)
    return subprocess.call(["launchctl", "load", mukkuru_service_path], env=sanitized_env()) == 0

def add_to_startup_linux(mukkuru_steam_id: str, is_gamescope : bool = False) -> bool:
    ''' (Linux) Set Mukkuru to open at user login, uses systemctl '''
    mukkuru_service = []
    mukkuru_service.append("[Unit]")
    mukkuru_service.append("Description=Open Mukkuru from Gamescope at startup")
    mukkuru_service.append("PartOf=graphical-session.target")
    mukkuru_service.append("After=graphical-session.target")
    mukkuru_service.append("[Service]")
    if is_gamescope:
        mukkuru_service.append(f"ExecStart=/usr/bin/steam steam://rungameid/{mukkuru_steam_id}")
    else:
        mukkuru_service.append(f"ExecStart={os.path.abspath(sys.argv[0])}")
    mukkuru_service.append("Restart=no")
    mukkuru_service.append("[Install]")
    mukkuru_service.append("WantedBy=graphical-session.target")
    mukkuru_service_path = os.path.expanduser("~/.config/systemd/user/mukkuru.service")
    with open(mukkuru_service_path,"w", encoding="utf-8") as file:
        file.write("\n".join(mukkuru_service))
    return subprocess.call(["systemctl", "--user", "enable", "mukkuru.service"]) == 0

def set_startup_flag(state: bool) -> None:
    ''' sets addedToStartup value '''
    backend_log(f"setting addedToStartup: {state}")
    user_config = get_config()
    user_config["addedToStartup"] = state
    update_config(user_config)

def add_to_startup() -> str:
    '''
    Handles os-specific add_startup calls and returns display message\n
    Windows: add current running app to CurrentVersion\\Run in registry\n
    Linux: uses systemctl --user\n
    MacOS: uses LaunchAgents\n
    '''
    sucess_message = translate_str("OperationSuccess", "Operation was completed successfully")
    fail_message = translate_str("OperationFailed", "Operation failed")
    user_config = get_config()
    if platform.system() == "Windows":
        import winreg#pylint: disable=C0415
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Mukkuru", 0, winreg.REG_SZ, f'"{os.path.abspath(sys.argv[0])}"')
        winreg.CloseKey(key)
        result = True
        set_startup_flag(result)
        return ternary(result, sucess_message, fail_message)
    device_info = hardware_if.get_info()
    if "SteamOS" in device_info["distro"]:
        if "mukkuru_steam_id" not in user_config:
            return translate_str("MustAddToSteam", "You must add Mukkuru to Steam first")
        result = add_to_startup_linux(user_config["mukkuru_steam_id"], is_gamescope=True)
        set_startup_flag(result)
        return ternary(result, sucess_message, fail_message)
    if platform.system() == "Linux":
        result = add_to_startup_linux(None, is_gamescope=False)
        set_startup_flag(result)
        return ternary(result, sucess_message, fail_message)
    if platform.system() == "Darwin":
        result = add_to_startup_macos()
        set_startup_flag(result)
        return ternary(result, sucess_message, fail_message)
    return translate_str("UnsupportedFunction", "This feature is not available for your setup")

def remove_from_startup() -> str:
    ''' Removes Mukkuru from user startup '''
    sucess_message: str = translate_str("OperationSuccess", "Operation was completed successfully")
    fail_message: str = translate_str("OperationFailed", "Operation failed")
    result: bool = False
    if platform.system() == "Linux":
        result = subprocess.call(["systemctl", "--user", "disable", "mukkuru.service"]) == 0
        mukkuru_service_path = os.path.expanduser("~/.config/systemd/user/mukkuru.service")
        if Path(mukkuru_service_path).exists():
            os.remove(mukkuru_service_path)
    if platform.system() == "Windows":
        import winreg#pylint: disable=C0415
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, "Mukkuru")
        winreg.CloseKey(key)
        #proc = subprocess.run(["schtasks", "/Delete", "/TN", "Mukkuru", "/F"], check=False)
        result = True
    if platform.system() == "Darwin":
        mukkuru_spath = os.path.expanduser("~/Library/LaunchAgents/com.panyolsoft.mukkuru.plist")
        result = subprocess.call(["launchctl", "unload", mukkuru_spath], env=sanitized_env()) == 0
        if Path(mukkuru_spath).exists():
            os.remove(mukkuru_spath)
    set_startup_flag(not result)
    return ternary(result, sucess_message, fail_message)

def get_capabilities() -> dict:
    ''' returns a dictionary with capabilities '''
    capabilities = {}
    capabilities["shutdown"] = can_shutdown(False)
    capabilities["reboot"] = can_shutdown(True)
    capabilities["desktop"] = False
    capabilities["lossless_scaling"] = is_lossless_scaling_available()
    return capabilities

def has_shutdown_privilege_enabled():
    """ (Windows) Check SeShutdownPrivilege to check whether shutdown is possible """
    if platform.system() != "Windows":
        return False
    import ctypes
    from ctypes import wintypes
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    SE_SHUTDOWN_NAME = "SeShutdownPrivilege"
    TOKEN_QUERY = 0x0008
    TokenPrivileges = 3
    SE_PRIVILEGE_ENABLED = 0x00000002
    class LUID(ctypes.Structure):
        _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]

    class LUID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
        ("Luid", LUID),
        ("Attributes", wintypes.DWORD),
    ]

    class TOKEN_PRIVILEGES(ctypes.Structure):
        _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Privileges", LUID_AND_ATTRIBUTES * 1),
    ]
    token = wintypes.HANDLE()
    process = kernel32.GetCurrentProcess()
    if not advapi32.OpenProcessToken(process, TOKEN_QUERY, ctypes.byref(token)):
        return False

    luid = LUID()
    if not advapi32.LookupPrivilegeValueW(None, SE_SHUTDOWN_NAME, ctypes.byref(luid)):
        return False

    # Query privileges
    size = wintypes.DWORD(0)
    advapi32.GetTokenInformation(token, TokenPrivileges, None, 0, ctypes.byref(size))
    buf = ctypes.create_string_buffer(size.value)
    if not advapi32.GetTokenInformation(token, TokenPrivileges, buf, size, ctypes.byref(size)):
        return False

    tp = ctypes.cast(buf, ctypes.POINTER(TOKEN_PRIVILEGES)).contents

    # Iterate privileges
    for i in range(tp.PrivilegeCount):
        priv = tp.Privileges[i]
        if priv.Luid.LowPart == luid.LowPart and priv.Luid.HighPart == luid.HighPart:
            is_enabled = bool(priv.Attributes & SE_PRIVILEGE_ENABLED)
            return is_enabled

    return False

def can_shutdown(reboot: bool = False) -> bool:
    ''' returns whether shutdown is possible, pass True for evaluating reboot instead '''
    system = platform.system()
    if system == "Windows":
        return has_shutdown_privilege_enabled()
    if system == "Linux":
        action = "org.freedesktop.login1.power-off"
        if reboot:
            action = "org.freedesktop.login1.reboot"
        return check_poolkit_status(action)
    return False

def is_rdp_session() -> bool:
    ''' (Windows only) returns whether user is inside an RDP Session '''
    return os.environ.get("SESSIONNAME", "").startswith("RDP-")

def can_disconnect_session() -> bool:
    ''' returns whether disconnecting from session is possible '''
    if platform.system() == "Windows":
        return is_rdp_session()

def disconnect_session() -> None:
    ''' Disconnect from remote session '''
    if platform.system() == "Windows":
        import win32ts
        win32ts.WTSDisconnectSession(None, win32ts.WTS_CURRENT_SESSION, False)

def shutdown(reboot: bool = False) -> None:
    ''' attempts shutdown, pass True for rebooting '''
    time.sleep(0.1)
    system = platform.system()
    if system == "Windows":
        power_flag =  "/r" if reboot else "/s"
        subprocess.run(["shutdown", power_flag, "/t", "0"], check=False)
    if system == "Linux":
        power_flag = "reboot" if reboot else "poweroff"
        subprocess.run(["systemctl", power_flag], check=False)

# Might enable later to allow shutdown/rebooting in more distros
def add_poolkit_rule() -> None:
    ''' (Linux) creates a poolkit rule '''
    raise NotImplementedError
    if platform.system() != "Linux":#pylint: disable=W0101
        return
    if os.geteuid() != 0:#pylint: disable = E1101
        subprocess.run(["pkexec", os.path.abspath(sys.argv[0]), "--add-poolkit-rules"], check=False)
        return
    poolkit_rules = []
    poolkit_rules.append('polkit.addRule(function(action, subject) {')
    poolkit_rules.append('if (')
    poolkit_rules.append('(action.id == "org.freedesktop.login1.reboot" ||')
    poolkit_rules.append('action.id == "org.freedesktop.login1.power-off")')
    poolkit_rules.append(') {')
    poolkit_rules.append('});')
    with open("/etc/polkit-1/rules.d/49-shutdown.rules","w", encoding="utf-8") as file:
        file.write("\n".join(poolkit_rules))
    return

def check_poolkit_status(action: str) -> bool:
    ''' (Linux) returns whether an action can be executed with available priviledges '''
    poolkit_cmd = []
    poolkit_cmd.append("pkcheck")
    poolkit_cmd.extend(["--action-id", action])
    poolkit_cmd.extend(["--process", str(os.getpid())])
    return subprocess.call(poolkit_cmd, env=sanitized_env()) == 0

def is_lossless_scaling_available():
    ''' (Linux/Windows) returns whether Lossless scaling is installed '''
    if platform.system() == "Windows" and "993090" in get_games():
        return True
    lossless_scaling_path = os.path.expanduser("~/lsfg")
    if Path(lossless_scaling_path).exists():
        return True
    return False
#To-do: add all operations that require terminating Steam to a queue, so
# they will be done together when users desire so
def lc_close_steam(avoid_gamescope: bool = True):
    ''' Terminate steam for local_config reload '''
    gamescope_flag = "Gaming Mode" in hardware_if.get_info()["distro"]
    procs = hardware_if.get_process_by_name(format_executable("steam"))
    if avoid_gamescope and not gamescope_flag:
        procs[0].kill()
    if not avoid_gamescope and gamescope_flag:
        from view.alternate_ui import Frontend#pylint: disable=C0415
        Frontend().close()
        procs[0].kill()

def format_launch_options(launch_options: str, prefix: str, apply:bool,exe:str="%command%") -> str:
    '''
    :param apply: format behaviour\n
                - False: removes ``prefix`` from ``launch_options``.
                - True: appends ``prefix`` to begin of ``launch_options``.
    :type apply: bool\n
    ``prefix`` will only be appended if it does not exists in ``launch_options``.\n
    If ``prefix`` is empty passing ``apply`` = False will remove ``exe`` from launch_options\n
    congratulation for reading this docstring, i did not expect anyone to use it\n
    '''
    if prefix == "" and not apply:
        launch_options = launch_options.replace(f"{exe} ", "")
        return launch_options
    if exe not in launch_options:
        launch_options = f"{exe} {launch_options}"
    if apply and prefix not in launch_options:
        launch_options = f"{prefix}{launch_options}"
    elif not apply:
        launch_options = launch_options.replace(prefix, "")
    return launch_options

def manage_all_games(manage = True):
    ''' Run all games under Mukkuru passthrough '''
    if platform.system() == "Darwin":
        return
    bootstrap.set_global_progress_context(translate_str("Updating", "Updating"))
    games = scan_games(dry=False)
    tmukk = f'~/{format_executable("mukkuru")}'
    prefix = f"{tmukk} "
    lc_close_steam(True)
    steam_env = steam.get_steam_env()
    current = 0
    # we'll use the same localconfig and shortcuts instance
    # to avoid I/O overhead, this will save us like 0.5s
    localconfig = steam.read_local_config(steam_env["localconfig.vdf"])
    shortcuts = steam.read_shortcuts(steam_env)
    mukkuru_exe = os.path.expanduser(prefix.rstrip())
    for app_id, game in games.items():
        current = current + 1
        bootstrap.global_progress_callback(current, len(games))
        game["Managed"] = manage
        if game["Source"] == "steam":
            launch_options = game["AppOptions"]
            launch_options = format_launch_options(launch_options, prefix=prefix, apply=manage)
            steam.set_launch_options(steam_env, app_id, launch_options, localconfig)
        elif game["Source"] == "non-steam" and shortcuts is not None:
            launch_options:str = game["AppOptions"]
            game_exe = game["AppExe"]
            if "%command%" in launch_options:
                #launch_options = format_launch_options(launch_options, prefix, manage)
                backend_log(f'Skipping {game["AppName"]} due to uncompatible launch options')
                continue
            else:
                launch_options = format_launch_options(launch_options, "", manage, game_exe)
                steam.set_shortcut_exe(shortcuts, game, ternary(manage, mukkuru_exe, game_exe))
            steam.set_shortcut_launch_options(steam_env, game, launch_options, shortcuts)
        else:
            game["Managed"] = False
    steam.save_local_config(steam_env, localconfig)
    steam.save_shortcuts(steam_env, shortcuts)
    update_games(games)
    bootstrap.clear_global_progress()
    # Using separate Mukkuru copy to help games to stay playable in case main executable breaks
    updater.update_external_instance(delete=not manage)
    lc_close_steam(False)
    return translate_str("OperationSuccess", "Operation was completed successfully")

def toggle_lossless_scaling_for_game(appid: str, state: bool = True):
    ''' Enables lossless scaling for steam game, returns message '''
    if platform.system() == "Windows":
        # ignore
        return
    games = scan_games(dry=True)
    if appid not in games:
        return
    game = games[appid]
    source = game["Source"]
    if "Managed" in game and game["Managed"]:
        return
    lc_close_steam(True)
    prefix = "~/lsfg "
    lsfg_exe = os.path.expanduser(prefix.rstrip())
    steam_env = steam.get_steam_env()
    if source == "steam":
        launch_options = game["AppOptions"]
        launch_options = format_launch_options(launch_options, prefix, state)
        steam.set_launch_options(steam_env, appid, launch_options)
    elif source == "non-steam":
        shortcuts = steam.read_shortcuts(steam_env)
        # THIS MIGHT BREAK SHORTCUT GAMES
        game_exe = game["AppExe"]
        launch_options = game["AppOptions"]
        launch_options = format_launch_options(launch_options, "", state, game_exe)
        steam.set_shortcut_launch_options(steam_env, game, launch_options, shortcuts)
        steam.set_shortcut_exe(shortcuts, game, ternary(state, lsfg_exe, game_exe))
        steam.save_shortcuts(steam_env, shortcuts)
    else:
        backend_log("Unsupported source, only steam games and shortcuts supported")
    lc_close_steam(False)
