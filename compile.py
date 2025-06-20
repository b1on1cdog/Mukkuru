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
system = platform.system()

parser = argparse.ArgumentParser()
parser.add_argument("--docker", action="store_true")
parser.add_argument("--clean", action="store_true")
parser.add_argument("--wipe", action="store_true")
parser.add_argument("--run", action="store_true")

args = parser.parse_args()

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def unix_path(path):
    ''' return a path with unix separator '''
    return str(path).replace('\\', '/')

docker = {
    "ubuntu-x86_64" : f'run --rm -v {unix_path(APP_DIR)}:/app -w /app ubuntu-python python3',
}

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

requirements = ["flask", "waitress",
                "requests", "pillow",
                "distro", "psutil",
                "nuitka"]

#if system == "Darwin":
requirements = requirements + ["imageio", "pywebview"]

#if system == "Linux":
#    requirements = requirements + ["pyside6"]

#if system == "Windows":
#    requirements = requirements + ["setuptools", "pywebview"]

AARCH = {'x86_64': 'x86_64',
         'AMD64': 'x86_64',
         'aarch64': 'arm64'}.get(platform.machine(), platform.machine())
SRC_FILE = "mukkuru.py"
SRC_OUT = f"mukkuru-{system.lower()}-{AARCH}.py"
OUTPUT_DIR = "build"
OUTPUT_FILE = f"mukkuru-{system.lower()}-{AARCH}"
ICON_PATH = os.path.join("ui", "mukkuru.ico")
PNG_PATH = os.path.join("mukkuru.png")
VENV = os.path.join(".venv", f"{system.lower()}-{AARCH}")
SRC_CONTENT = None

with open(SRC_FILE, 'r', encoding='utf-8') as file:
    SRC_CONTENT = file.read()

if SRC_CONTENT is None:
    print("unable to read main file, exiting....")
    exit(0)

APP_VERSION = re.search(r'APP_VERSION\s*=\s*["\'](.*?)["\']', SRC_CONTENT).group(1)
OUTPUT_FILE = f"{OUTPUT_FILE}-{APP_VERSION}"

venv_python = os.path.join(VENV, 'bin', 'python')

if system == "Windows":
    OUTPUT_FILE = OUTPUT_FILE+".exe"
    venv_python = os.path.join(VENV, 'Scripts', 'python.exe')

UI_SOURCE = os.path.join("ui")
# CONSTANTS END

def create_venv(python_executable = sys.executable):
    ''' Create a virtual environment '''
    invoke(["-m", "venv", VENV])
    result = invoke(["-m", "pip", "install"] + requirements, python_executable)
    if result.returncode != 0:
        shutil.rmtree(VENV)
        print(f"failed to install deps {result}")
        exit(-1)
    #invoke(["-m", "pip", "install", "-r", "requirements.txt"], python_executable)

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
    if "flaskwebui" in requirements:
        frontend = "FLASKUI"
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

if args.clean:
    cleanup()
    exit(0)

if args.wipe:
    cleanup()
    shutil.rmtree(VENV)
    os.remove(os.path.join(OUTPUT_DIR, OUTPUT_FILE))
    exit(0)

if args.docker:
    invoke(docker["ubuntu-x86_64"].split() + [ f"/app/{os.path.basename(__file__)}"] ,"docker")
    exit(0)

print(f"using {sys.executable}, compiling {OUTPUT_FILE}")

if not Path(".venv").is_dir():
    os.mkdir(".venv")

if not Path(VENV).is_dir():
    create_venv(venv_python)

compiler_flags = [ "-m", "nuitka"]
compiler_flags.append("--follow-imports")
if system == "Windows":
    compiler_flags.append(f"--windows-icon-from-ico={ICON_PATH}")
    compiler_flags.append("--windows-console-mode=disable")
if system == "Darwin":
    compiler_flags.append("--macos-create-app-bundle")
    compiler_flags.append(f"--macos-app-icon={PNG_PATH}")
else:
    compiler_flags.append("--onefile")

if "pyside6" in requirements:
    compiler_flags.append("--enable-plugin=pyside6")

#if system == "Windows" and "pywebview" in requirements:
#    compiler_flags.append("--include-package-data=pywebview")

if system == "Linux":
    compiler_flags.append(f"--linux-icon={ICON_PATH}")

compiler_flags.append(f"--include-data-dir={UI_SOURCE}={UI_SOURCE}")
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
linux_packages = [
    "libglib2.0-0",
    "libx11-6"
    "libxcb1",
    "libxcomposite1"
    "libxrender1",
    "libxi6",
    "libdbus-1-3",
    "libfontconfig1",
    "libfreetype6",
    "libxext6",
    "libxfixes3",
    "libxcb-render0",
    "libxcb-shape0",
    "libxcb-xfixes0",
    "libxcb1-dev",
    "libglu1-mesa",
    "libegl1",
    "libopengl0"
]
