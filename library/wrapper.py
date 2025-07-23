# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Compatibility layer module '''
import os
from pathlib import Path
from utils.core import sanitized_env

def get_crossover_env(bottle) -> dict:
    ''' get crossover environment variables '''
    crossenv = sanitized_env()
    crossover_app = os.path.expanduser("~/Applications/CrossOver.app/")
    if not Path(crossover_app).is_dir():
        crossover_app = "/Applications/CrossOver.app/"
        if Path(crossover_app).is_dir():
            print("Using Crossover system install")
        else:
            print("Crossover is not installed")
    else:
        print("Using Crossover user install")
    cxroot = os.path.join(crossover_app, "Contents", "SharedSupport", "CrossOver")
    cxbottlepath = os.path.expanduser("~/Library/Application Support/CrossOver/Bottles")
    crossenv["PYTHONPATH"] = os.path.join(cxroot, "lib", "python")
    crossenv["CX_MANAGED_BOTTLE_PATH"] = "/Library/Application Support/CrossOver/Bottles"
    crossenv["CX_BOTTLE"] = bottle
    crossenv["CX_BOTTLE_PATH"] = cxbottlepath
    crossenv["CX_APP_BUNDLE_PATH"] = crossover_app
    crossenv["CX_ROOT"] = cxroot
    crossenv["CX_DISK"] = os.path.join(cxbottlepath, crossenv["CX_BOTTLE"], "drive_c")
    crossenv["PATH"] = crossenv["PATH"] + os.pathsep + os.path.join(cxroot, "bin")
    return crossenv
