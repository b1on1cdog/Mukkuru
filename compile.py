''' compile script for Mukkuru, written by b1on1cdog '''
import sys
import platform
import os
import shutil
from pathlib import Path
from nuitka.__main__ import main as nuitka_main

def compile_inline(script_args):
    ''' Call nuitka for compilation '''
    sys.argv = ["nuitka"] + script_args
    nuitka_main()

system = platform.system()
OUTPUT_DIR = "build"
OUTPUT_FILE = f"{OUTPUT_DIR}/mukkuru-{system}"
ICON_PATH = os.path.join("ui", "mukkuru.ico")

if system == "Windows":
    OUTPUT_FILE = OUTPUT_FILE+".exe"

if not Path(OUTPUT_DIR).is_dir():
    os.mkdir(OUTPUT_DIR)

UI_DEST = os.path.join(OUTPUT_DIR, "ui")
UI_SOURCE = os.path.join("ui")

if os.path.exists(UI_DEST):
    shutil.rmtree(UI_DEST)
shutil.copytree(UI_SOURCE, UI_DEST)

compiler_flags = []
compiler_flags.append("--follow-imports")
compiler_flags.append("--windows-console-mode=disable")
compiler_flags.append(f"--windows-icon-from-ico={ICON_PATH}")
compiler_flags.append("mukkuru.py")
compiler_flags.append("-o")
compiler_flags.append(OUTPUT_FILE)

compile_inline(compiler_flags)
