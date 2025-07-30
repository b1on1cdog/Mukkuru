# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Common functions needed for library provider '''
import os
import sys
from pathlib import Path
from typing import Optional
import platform

from utils.core import backend_log
if platform.system() == 'Windows':
    import winreg

def read_registry_value(root, reg_key, reg_value) -> Optional[str]:
    ''' [Windows only] read key from System Registry'''
    if platform.system() == 'Windows':
        if 'winreg' in sys.modules:
            try:
                hroot = winreg.HKEY_LOCAL_MACHINE
                if root == 1:
                    hroot = winreg.HKEY_CURRENT_USER
                elif root == 2:
                    hroot = winreg.HKEY_CURRENT_CONFIG
                elif root == 3:
                    hroot = winreg.HKEY_CLASSES_ROOT
                key = winreg.OpenKey(hroot, reg_key)
                ret, _ = winreg.QueryValueEx(key, reg_value)
                return ret
            except (FileNotFoundError, PermissionError, OSError) as e:
                backend_log(f"Error occured when trying to read registry: {e}")
                return None
        else:
            backend_log("platform specific module not imported: winreg")
            return None
    else:
        backend_log('non-windows, ignoring registry read')
        return None

def find_path(paths) -> Optional[str]:
    ''' return which path exists of all the candidates '''
    for path in paths:
        if path is None:
            continue
        if "~" in path:
            path = os.path.expanduser(path)
        if Path(path).exists():
            return path
    return None
