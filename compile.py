# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
'''
Compile script for Mukkuru\n
Supports both Nuitka and Pyinstaller\n
'''
import sys
import platform
import os
import subprocess
import shutil
from pathlib import Path
import argparse
import re
import zipfile
import json
system = platform.system()

parser = argparse.ArgumentParser()
parser.add_argument("--docker", action="store_true")
parser.add_argument("--clean", action="store_true")
parser.add_argument("--wipe", action="store_true")
parser.add_argument("--run", action="store_true")
parser.add_argument("--wef", action="store_true")
parser.add_argument("--add", nargs='+')
parser.add_argument("--debug", action="store_true")
parser.add_argument("--alt", action="store_true")
parser.add_argument("--onedir", action="store_true")

args = parser.parse_args()
compiler_config = {}

if not Path("compile.json").is_file():
    print("Fatal: missing compile.json")
    os._exit(-1)
with open('compile.json', encoding='utf-8') as main_conf:
    compiler_config = json.load(main_conf)

# to prevent contributors from commiting their env changes to github
# project, they will ideally do those changes in compile_user.json
if Path("compile_user.json").is_file():
    with open('compile_user.json', encoding='utf-8') as conf:
        compiler_config.update(json.load(conf))
APP_TITLE = compiler_config["APP_TITLE"]
APP_DIR = os.path.dirname(os.path.abspath(__file__))
USE_WEF = args.wef

def unix_path(path):
    ''' return a path with unix separator '''
    return str(path).replace('\\', '/')

docker = {
    "debian-x86_64" : f'run --rm -v {unix_path(APP_DIR)}:/app -w /app debian-python python3',
}

if "docker" in compiler_config:
    docker = compiler_config["docker"]
    for key, value in docker.items():
        docker[key] = value.replace("[APP_DIR]", unix_path(APP_DIR))

def invoke(script_args, python_executable = sys.executable):
    ''' Use subprocess to run python '''
    print(f'running {python_executable} {" ".join(script_args)}')
    return subprocess.run([python_executable] + script_args, check=False)

def cleanup():
    ''' delete residual files '''
    prefix = SRC_OUT.replace(".py", "")
    try:
        shutil.rmtree(os.path.join(OUTPUT_DIR, f"{prefix}.build"))
        shutil.rmtree(os.path.join(OUTPUT_DIR, f"{prefix}.dist"))
        shutil.rmtree(os.path.join(OUTPUT_DIR, f"{prefix}.onefile-build"))
    except FileNotFoundError:
        return

def wipe():
    ''' delete residual files, venv, and produced assemblies '''
    cleanup()
    try:
        shutil.rmtree(VENV)
        os.remove(os.path.join(OUTPUT_DIR, OUTPUT_FILE))
    except FileNotFoundError:
        return

def zip_dir_contents(src_dir, zip_path):
    ''' zip the content of a directory without including directory itself '''
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, src_dir)
                zf.write(full_path, rel_path)
def default_set(config: dict, prop:str, default=None, is_path = False):
    ''' Returns config[prop] if exists, otherwise returns default '''
    if prop in config:
        ret = config[prop]
        if is_path and os.path.exists(ret):
            return ret
        elif not is_path:
            return config[prop]
    return default

requirements = ["nuitka"] + compiler_config["REQUIREMENTS"]
requirements = requirements + ["setuptools"]

if system == "Linux":
    requirements = requirements + ["patchelf"]

if USE_WEF is False and "patchelf" not in requirements:
    requirements = requirements + ["pywebview"]

AARCH = {'x86_64': 'x86_64',
         'AMD64': 'x86_64',
         'aarch64': 'arm64'}.get(platform.machine(), platform.machine())
SRC_FILE = compiler_config["SOURCE_FILE"]
SRC_OUT = f"{APP_TITLE.lower()}-{system.lower()}-{AARCH}.py"
CORE_FILE = os.path.join("utils", "core.py")
OUTPUT_DIR = "build"
OUTPUT_FILE = f"{APP_TITLE.lower()}-{system.lower()}-{AARCH}"

UI_SOURCE:str = default_set(compiler_config, "UI_SOURCE", is_path=True)
LICENSE_SOURCE:str = default_set(compiler_config, "LICENSE_SOURCE", is_path=True)

PNG_PATH =  None
ICON_PATH = None

if UI_SOURCE is not None:
    ICON_PATH = os.path.join(UI_SOURCE, f"{APP_TITLE.lower()}.ico")
    PNG_PATH = os.path.join(UI_SOURCE, f"{APP_TITLE.lower()}.png")

VENV = os.path.join(".venv", f"{system.lower()}-{AARCH}")
SRC_CONTENT = None
CORE_CONTENT = None

with open(CORE_FILE, 'r', encoding='utf-8') as cr_file:
    CORE_CONTENT = cr_file.read()

if CORE_CONTENT is None:
    print("unable to read main file, exiting....")
    os._exit(0)

#APP_VERSION = re.search(r'APP_VERSION\s*=\s*["\'](.*?)["\']', CORE_CONTENT).group(1)
# Support type-hinted and non-type hinted APP_VERSION, ignore commmented ones
VERSION_REGEX = r'^(?!#)\s*APP_VERSION(?:\s*:\s*str)?\s*=\s*["\'](.*?)["\'](?:\s*#.*)?$'
version_match = re.search(VERSION_REGEX, CORE_CONTENT, re.MULTILINE)
if version_match is None:
    print("Unable to fetch app version")
    os._exit(-1)
APP_VERSION = version_match.group(1)

if system == "Darwin" and UI_SOURCE is not None:
    print("MacOS detected, adding --onedir")
    args.onedir = True

venv_python = os.path.join(VENV, 'bin', 'python')

if system == "Windows":
    OUTPUT_FILE = OUTPUT_FILE+".exe"
    venv_python = os.path.join(VENV, 'Scripts', 'python.exe')
# CONSTANTS END

def create_venv(python_executable = sys.executable, update = False):
    ''' Create a virtual environment '''
    if not update:
        invoke(["-m", "venv", VENV])
    # if a crash happen here files won't be cleaned
    result = invoke(["-m", "pip", "install"] + requirements, python_executable)
    if result.returncode != 0:
        if not update:
            shutil.rmtree(VENV)
        print(f"failed to install deps {result}")
        exit(-1)
    #invoke(["-m", "pip", "install", "-r", "requirements.txt"], python_executable)

def add_package(packages, python_executable = sys.executable):
    ''' install package with pip '''
    result = invoke(["-m", "pip", "install"] + packages, python_executable)
    if result.returncode != 0:
        print(f"failed to install dep {result}")
        exit(-1)
# FUNCTIONS END

if args.docker:
    arguments = sys.argv
    if len(arguments) == 2:
        arguments = []
    else:
        arguments = arguments[2:]
    COMPILE_SCRIPT = f"/app/{os.path.basename(__file__)}"
    for container, command in docker.items():
        if container.endswith(AARCH):
            invoke(command.split() + [ COMPILE_SCRIPT ] + arguments ,"docker")
        else:
            print(f"skipping {container} due to incompatible arch")
    exit(0)

if args.add:
    if Path(venv_python).is_file():
        add_package(args.add, venv_python)
    else:
        print("You must create a venv first")
    exit(0)

if args.clean:
    cleanup()
    exit(0)

if args.wipe:
    wipe()
    exit(0)

print(f"using {sys.executable}, compiling {OUTPUT_FILE}")

if not Path(".venv").is_dir():
    os.mkdir(".venv")

if not Path(VENV).is_dir():
    create_venv(venv_python)
if args.alt:
    add_package(["pyinstaller"], venv_python)
    compiler_flags = ['-m', "PyInstaller"]
    if args.onedir:
        compiler_flags.append("--onedir")
    else:
        compiler_flags.append("--onefile")
    if system != "Windows":
        compiler_flags.append("--strip")
    if not USE_WEF:
        compiler_flags.extend(["--exclude-module", "tkinter"])
    if UI_SOURCE is not None:
        compiler_flags.extend(["--add-data", f"{UI_SOURCE}:{UI_SOURCE}"])
    if LICENSE_SOURCE is not None:
        compiler_flags.extend(["--add-data", f"{LICENSE_SOURCE}:docs"])
    compiler_flags.extend(["--distpath", os.path.join(OUTPUT_DIR, "pack")])
    if ICON_PATH is not None:
        compiler_flags.extend(["-i", ICON_PATH])
    if not args.debug:
        compiler_flags.append("--noconsole")
    compiler_flags.append(SRC_OUT)
    shutil.copy(SRC_FILE, SRC_OUT)
    invoke(compiler_flags, venv_python)
    os.remove(SRC_OUT)
    os._exit(0)
compiler_flags = [ "-m", "nuitka"]
compiler_flags.append("--assume-yes-for-downloads")
#compiler_flags.append("--follow-imports")
if system == "Windows":
    if PNG_PATH is not None:
        compiler_flags.append(f"--windows-icon-from-ico={PNG_PATH}")
    if not args.debug and UI_SOURCE is not None:
        compiler_flags.append("--windows-console-mode=disable")
    compiler_flags.append("--windows-company-name=Josue Alonso Rodriguez")
    compiler_flags.append(f"--windows-product-name={APP_TITLE}")
    compiler_flags.append(f"--windows-product-version={APP_VERSION}")
    compiler_flags.append(f"--windows-file-version={APP_VERSION}")
if system == "Darwin":
    compiler_flags.append("--macos-create-app-bundle")
    if PNG_PATH is not None:
        compiler_flags.append(f"--macos-app-icon={PNG_PATH}")
    compiler_flags.append('--company-name=Josue Alonso Rodriguez')
    compiler_flags.append(f'--macos-app-version={APP_VERSION}')
elif args.debug:
    compiler_flags.append("--debug")

if args.onedir:
    compiler_flags.append("--standalone")
else:
    compiler_flags.append("--onefile")

if system == "Linux":
    if PNG_PATH is not None:
        compiler_flags.append(f"--linux-icon={PNG_PATH}")
if USE_WEF:
    compiler_flags.append("--enable-plugin=tk-inter")
if UI_SOURCE is not None:
    compiler_flags.append(f"--include-data-dir={UI_SOURCE}={UI_SOURCE}")
if LICENSE_SOURCE is not None:
    compiler_flags.append(f"--include-data-dir={LICENSE_SOURCE}=docs")
compiler_flags.append(SRC_OUT)
compiler_flags.append(f"--output-filename={OUTPUT_FILE}")

if True and not Path(OUTPUT_DIR).is_dir():
    os.mkdir(OUTPUT_DIR)
compiler_flags.append(f"--output-dir={OUTPUT_DIR}")
shutil.copy(SRC_FILE, SRC_OUT)
if args.run:
    invoke([SRC_OUT], venv_python)
else:
    invoke(compiler_flags, venv_python)
os.remove(SRC_OUT)

if system == "Darwin" and not args.run:
    APP_NAME = f"{OUTPUT_FILE}.app"
    app_input = os.path.join(OUTPUT_DIR, APP_NAME)
    app_dmg = app_input.replace(".app", ".dmg")

    layout_abs = os.path.abspath(os.path.join(OUTPUT_DIR, "layout"))
    os.makedirs(layout_abs, exist_ok=True)
    layout_app_abs = os.path.join(layout_abs, f"{APP_TITLE}.app")
    shutil.move(app_input, layout_app_abs)
    dmg_create_command = []

    DMG_UTIL = shutil.which("create-dmg")
    if DMG_UTIL is None:
        DMG_UTIL = "hdiutil"
        alias_create_command = ['-e']
        SCRIPT1 = 'tell application "Finder" to make alias file'
        SCRIPT2 = 'to (POSIX file "/Applications/")'
        SCRIPT3 = f'at (POSIX file "{layout_abs}")'
        alias_create_command.append(f'{SCRIPT1} {SCRIPT2} {SCRIPT3}")')
        invoke(alias_create_command, "osascript")
        dmg_create_command.extend(["create", "-volname", APP_TITLE])
        dmg_create_command.extend(["-srcfolder", layout_abs])
        dmg_create_command.extend(["-ov", "-format", "UDZO", app_dmg])
    else:
        dmg_create_command.extend(["--volname" ,APP_TITLE])
        dmg_create_command.extend(["--window-size", "500", "300"])
        dmg_create_command.extend(["--icon-size", "100"])
        dmg_create_command.extend(["--icon", f"{APP_TITLE}.app", "100", "100"])
        dmg_create_command.extend(["--app-drop-link", "350", "100"])
       # dmg_create_command.extend(["--icon", "Applications", "350", "100"])
        dmg_create_command.append("--no-internet-enable")
        dmg_create_command.append(app_dmg)
        dmg_create_command.append(layout_abs)
    invoke(dmg_create_command, DMG_UTIL)
# end compile.py
