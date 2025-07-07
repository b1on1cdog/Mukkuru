# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' compile script for Mukkuru, written by b1on1cdog '''
import sys
import platform
import os
import subprocess
import hashlib
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

# to prevent contributors from commiting their env changes to github
# project, they will ideally do those changes in compiler.json
if Path("compiler.json").is_file():
    with open('compiler.json', encoding='utf-8') as conf:
        compiler_config = json.load(conf)

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

requirements = ["flask", "waitress",
                "requests", "pillow",
                "distro", "psutil",
                "nuitka", "imageio", "qrcode"]

requirements = requirements + ["setuptools"]

if system == "Linux":
    requirements = requirements + ["patchelf", "flaskwebgui"]
#    USE_WEF = True

if USE_WEF is False and "flaskwebgui" not in requirements:
    requirements = requirements + ["pywebview"]

AARCH = {'x86_64': 'x86_64',
         'AMD64': 'x86_64',
         'aarch64': 'arm64'}.get(platform.machine(), platform.machine())
SRC_FILE = "mukkuru.py"
SRC_OUT = f"mukkuru-{system.lower()}-{AARCH}.py"
OUTPUT_DIR = "build"
OUTPUT_FILE = f"mukkuru-{system.lower()}-{AARCH}"
ICON_PATH = os.path.join("ui", "mukkuru.ico")
PNG_PATH = os.path.join("ui", "mukkuru.png")
VENV = os.path.join(".venv", f"{system.lower()}-{AARCH}")
SRC_CONTENT = None

with open(SRC_FILE, 'r', encoding='utf-8') as sr_file:
    SRC_CONTENT = sr_file.read()

if SRC_CONTENT is None:
    print("unable to read main file, exiting....")
    exit(0)

APP_VERSION = re.search(r'APP_VERSION\s*=\s*["\'](.*?)["\']', SRC_CONTENT).group(1)
#OUTPUT_FILE = f"{OUTPUT_FILE}-{APP_VERSION}"

venv_python = os.path.join(VENV, 'bin', 'python')

if system == "Windows":
    OUTPUT_FILE = OUTPUT_FILE+".exe"
    venv_python = os.path.join(VENV, 'Scripts', 'python.exe')

UI_SOURCE = os.path.join("ui")
LICENSE_SOURCE = os.path.join("docs")
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

def build_version():
    ''' generate 6 MD5 digits to use as build number '''
    hasher = hashlib.md5()
    with open(SRC_FILE, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
        return hasher.hexdigest()[-6:]

def patch_source_code(mukkuru_src):
    ''' Do temporal changes to source code  '''
    mukkuru_src = mukkuru_src.replace("COMPILER_FLAG = False", "COMPILER_FLAG = True")
    mukkuru_src = mukkuru_src.replace("BUILD_VERSION = None",f'BUILD_VERSION = "{build_version()}"')
    frontend = "Default"
    if "pywebview" in requirements:
        #mukkuru_src = mukkuru_src.replace("USE_PYWEBVIEW = False","USE_PYWEBVIEW = True")
        frontend = "PYWEBVIEW"
    if "flaskwebgui" in requirements:
        frontend = "FLASKUI"
    if USE_WEF:
        frontend = "WEF"
    if frontend != "Default":
        mukkuru_src = re.sub(r'(FRONTEND_MODE\s*=\s*)["\'].*?["\']', fr'\1"{frontend}"',mukkuru_src)
    with open(SRC_OUT, "w", encoding='utf-8') as f:
        f.write(mukkuru_src)

def certifi_patch():
    '''temporal patch due to Nuitka issue #3514, no longer used, kept for future reference'''
    python_name = f"python{sys.version_info.major}.{sys.version_info.minor}"
    certifi_core = os.path.join(VENV, "lib", python_name, "site-packages", "certifi", "core.py")
    if system == "Windows":
        certifi_core = os.path.join(VENV, "Lib", "site-packages", "certifi", "core.py")
    if not Path(certifi_core).is_file():
        print("certifi_core not found")
        return
    original = "if sys.version_info >= (3, 11):"
    replacement = f"if ({sys.version_info.major}, {sys.version_info.minor}):"
    with open(certifi_core, 'r', encoding='utf-8') as file_r:
        content = file_r.read()
        if original in content:
            content = content.replace(original, replacement)
            with open(certifi_core, 'w', encoding='utf-8') as ww:
                print("patching certifi/core.py...")
                ww.write(content)

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
    compiler_flags.extend(["--add-data", f"{UI_SOURCE}:{UI_SOURCE}"])
    compiler_flags.extend(["--add-data", f"{LICENSE_SOURCE}:docs"])
    compiler_flags.extend(["--distpath", os.path.join(OUTPUT_DIR, "pack")])
    compiler_flags.extend(["-i", ICON_PATH])
    if not args.debug:
        compiler_flags.append("--noconsole")
    compiler_flags.append(SRC_OUT)
    patch_source_code(SRC_CONTENT)
    invoke(compiler_flags, venv_python)
    os.remove(SRC_OUT)
    os._exit(0)
compiler_flags = [ "-m", "nuitka"]
#compiler_flags.append("--follow-imports")
if system == "Windows":
    compiler_flags.append(f"--windows-icon-from-ico={ICON_PATH}")
    if not args.debug:
        compiler_flags.append("--windows-console-mode=disable")
if system == "Darwin":
    compiler_flags.append("--macos-create-app-bundle")
    compiler_flags.append(f"--macos-app-icon={PNG_PATH}")
elif args.debug:
    compiler_flags.append("--standalone")
    compiler_flags.append("--debug")
    #compiler_flags.append("--experimental=allow-c-warnings")
    #os.environ["CFLAGS"] = "-Wall -Wextra -g -Wno-unused-but-set-variable"
else:
    compiler_flags.append("--onefile")

if system == "Linux":
    compiler_flags.append(f"--linux-icon={ICON_PATH}")
compiler_flags.append("--enable-plugin=tk-inter")
compiler_flags.append(f"--include-data-dir={UI_SOURCE}={UI_SOURCE}")
compiler_flags.append(f"--include-data-dir={LICENSE_SOURCE}=docs")
compiler_flags.append(SRC_OUT)
compiler_flags.append(f"--output-filename={OUTPUT_FILE}")
#compiler_flags.append("-o")
#compiler_flags.append(os.path.join(OUTPUT_DIR, OUTPUT_FILE))

if True and not Path(OUTPUT_DIR).is_dir():
    os.mkdir(OUTPUT_DIR)
compiler_flags.append(f"--output-dir={OUTPUT_DIR}")

patch_source_code(SRC_CONTENT)

if args.run:
    invoke([SRC_OUT], venv_python)
else:
    invoke(compiler_flags, venv_python)
os.remove(SRC_OUT)

# end compile.py
