''' compile script for Mukkuru, written by b1on1cdog '''
import sys
import platform
import os
import subprocess
import hashlib
import shutil
from pathlib import Path

system = platform.system()

requirements = ["flask", "waitress",
                "requests", "pillow",
                "distro", "psutil",
                "nuitka"]

if system == "Darwin":
    requirements = requirements + ["imageio", "pywebview"]
else:
    requirements = requirements + ["pyside6"]

if system == "Windows":
    requirements = requirements + ["setuptools"]

AARCH = {'x86_64': 'x86_64',
         'AMD64': 'x86_64',
         'aarch64': 'arm64'}.get(platform.machine(), platform.machine())
SRC_FILE = "mukkuru.py"
SRC_OUT = "mukkuru_release.py"
OUTPUT_DIR = "build"
OUTPUT_FILE = f"mukkuru-{system.lower()}-{AARCH}"
ICON_PATH = os.path.join("ui", "mukkuru.ico")
PNG_PATH = os.path.join("mukkuru.png")

SRC_CONTENT = None

with open(SRC_FILE, 'r', encoding='utf-8') as file:
    SRC_CONTENT = file.read()

if SRC_CONTENT is None:
    print("unable to read main file, exiting....")
    exit(0)

def invoke(script_args, python_executable = sys.executable):
    ''' Use subprocess to run python '''
    print(f'running {python_executable} {" ".join(script_args)}')
    return subprocess.run([python_executable] + script_args, check=False)

def create_venv(python_executable = sys.executable):
    ''' Create a virtual environment '''
    invoke(["-m", "venv", ".venv"])
    result = invoke(["-m", "pip", "install"] + requirements, python_executable)
    if result.returncode != 0:
        shutil.rmtree(".venv")
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
    if system == "Darwin":
        mukkuru_src = mukkuru_src.replace("USE_PYWEBVIEW = False","USE_PYWEBVIEW = True")
    with open(SRC_OUT, "w", encoding='utf-8') as f:
        f.write(mukkuru_src)

def certifi_patch():
    ''' temporal patch due to Nuitka issue #3514'''
    python_name = f"python{sys.version_info.major}.{sys.version_info.minor}"
    certifi_core = os.path.join(".venv", "lib", python_name, "site-packages", "certifi", "core.py")
    if system == "Windows":
        certifi_core = os.path.join(".venv", "Lib", "site-packages", "certifi", "core.py")
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
def cleanup():
    ''' delete residual files '''
    prefix = SRC_OUT.replace(".py", "")
    try:
        shutil.rmtree(f"{prefix}.build")
        shutil.rmtree(f"{prefix}.dist")
    except FileNotFoundError:
        return

print(f"using {sys.executable}")

venv_python = os.path.join('.venv', 'bin', 'python')

if system == "Windows":
    OUTPUT_FILE = OUTPUT_FILE+".exe"
    venv_python = os.path.join('.venv', 'Scripts', 'python.exe')

if not Path(".venv").is_dir():
    create_venv(venv_python)

UI_DEST = os.path.join(OUTPUT_DIR, "ui")
UI_SOURCE = os.path.join("ui")

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
    compiler_flags.append("--enable-plugin=pyside6")

if system == "Linux":
    compiler_flags.append(f"--linux-icon={ICON_PATH}")

compiler_flags.append(f"--include-data-dir={UI_SOURCE}={UI_SOURCE}")
compiler_flags.append(SRC_OUT)
compiler_flags.append("-o")
compiler_flags.append(OUTPUT_FILE)

patch_source_code(SRC_CONTENT)
certifi_patch()
invoke(compiler_flags, venv_python)
os.remove(SRC_OUT)
#cleanup()
