''' Mukkuru module for some windows specific functions '''
import winreg
import os
from typing import Optional
from utils import hardware_if
import subprocess
import shutil
import ctypes
import ctypes.wintypes as wt

netapi32 = ctypes.WinDLL("Netapi32.dll")

advapi = ctypes.WinDLL("advapi32", use_last_error=True)
RegLoadKeyW = advapi.RegLoadKeyW
RegLoadKeyW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p]
RegLoadKeyW.restype = ctypes.c_long

RegUnLoadKeyW = advapi.RegUnLoadKeyW
RegUnLoadKeyW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
RegUnLoadKeyW.restype = ctypes.c_long

class LOCALGROUP_MEMBERS_INFO_2(ctypes.Structure):
    _fields_ = [
        ("lgrmi2_sid", wt.PSID),
        ("lgrmi2_sidusage", wt.DWORD),
        ("lgrmi2_domainandname", wt.LPWSTR)
    ]

def get_group_users(group_name: str) -> Optional[list[str]]:
    ''' get users from group name '''
    bufptr = wt.LPVOID()
    entries_read = wt.DWORD()
    total_entries = wt.DWORD()

    res = netapi32.NetLocalGroupGetMembers(
        ctypes.c_wchar_p(None),
        wt.LPCWSTR(group_name),
        2,  # LOCALGROUP_MEMBERS_INFO_2
        ctypes.byref(bufptr),
        wt.DWORD(-1),  # MAX_PREFERRED_LENGTH
        ctypes.byref(entries_read),
        ctypes.byref(total_entries),
        None
    )
    if res != 0:
        print(f"NetLocalGroupGetMembers failed with error {res}")
        return None
    
    if entries_read == 0:
        print("No users to read")
        return []

    users = []

    array_type = LOCALGROUP_MEMBERS_INFO_2 * entries_read.value
    entries = ctypes.cast(bufptr, ctypes.POINTER(array_type)).contents

    for entry in entries:
        _, username = entry.lgrmi2_domainandname.split("\\", 1)
        users.append(username)

    netapi32.NetApiBufferFree(bufptr)

    return users

def username_to_sid(username: str) -> Optional[str]:
    ''' returns sid of specific username '''
    sid_size = wt.DWORD(0)
    domain_size = wt.DWORD(0)
    use = wt.DWORD()

    advapi.LookupAccountNameW(None, username, None, ctypes.byref(sid_size),
                              None, ctypes.byref(domain_size), ctypes.byref(use))

    if sid_size.value == 0:
        return None

    sid = ctypes.create_string_buffer(sid_size.value)
    domain = ctypes.create_unicode_buffer(domain_size.value)

    if not advapi.LookupAccountNameW(None, username, sid, ctypes.byref(sid_size),
                                     domain, ctypes.byref(domain_size), ctypes.byref(use)):
        return None

    sid_str = wt.LPWSTR()
    advapi.ConvertSidToStringSidW(sid, ctypes.byref(sid_str))
    result = sid_str.value
    ctypes.windll.kernel32.LocalFree(sid_str)
    return result

def sid_to_profile_path(sid: str) -> Optional[str]:
    ''' get profile path from sid '''
    if sid is None:
        print("No sid passed, unable to get profile path")
        return None
    reg_path = fr"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            value, _ = winreg.QueryValueEx(key, "ProfileImagePath")
            return value
    except FileNotFoundError:
        return None
    
def username_to_profile_path(username: str):
    ''' get profile path from username '''
    sid = username_to_sid(username)
    return sid_to_profile_path(sid)

def load_user_hive(sid: str, profile_path: str) -> Optional[str]:
    ''' load user hive from profile path '''
    hive_path = os.path.join(profile_path, "NTUSER.DAT")
    status = RegLoadKeyW(winreg.HKEY_USERS.handle, sid, hive_path)
    if status != 0:
        print(f"RegLoadKey failed with error {status}")
        return None
    return fr"HKEY_USERS\{sid}"

def unload_user_hive(sid: str):
    ''' unload user hive '''
    status = RegUnLoadKeyW(winreg.HKEY_USERS.handle, sid)
    if status != 0:
        print(f"RegUnLoadKey failed with error {status}")

def disable_user_features(hive_root: str):
    ''' disable user features that are not important for gaming (regedit, CMD, Task manager, Run) '''
    with winreg.CreateKey(winreg.HKEY_USERS, fr"{hive_root}\Software\Microsoft\Windows\CurrentVersion\Policies\System") as key:
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
    with winreg.CreateKey(winreg.HKEY_USERS, fr"{hive_root}\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer") as key:
        winreg.SetValueEx(key, "NoRun", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoFolderOptions", 0, winreg.REG_DWORD, 1)

def set_mukkuru_as_shell(hive_root: str):
    ''' Sets Mukkuru as user Shell '''
    mukkuru_shell_path = fr"C:\PanyolSoft\Mukkuru\Mukkuru.exe"
    if not os.path.exists(mukkuru_shell_path):
        print("Mukkuru shell is missing, unable to proceed....")
        return
    mukkuru_shell = f"{mukkuru_shell_path} --sandbox"
    with winreg.CreateKey(winreg.HKEY_USERS, fr"{hive_root}\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon") as key:
        winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, mukkuru_shell)
    with winreg.CreateKey(winreg.HKEY_USERS, fr"{hive_root}\Environment") as key:
        hw_info = hardware_if.get_info()
        winreg.SetValueEx(key, "HWINFO_GPU", 0, winreg.REG_SZ, hw_info["gpu"])
        winreg.SetValueEx(key, "HWINFO_CPU", 0, winreg.REG_SZ, hw_info["cpu"])
        winreg.SetValueEx(key, "HWINFO_RAM", 0, winreg.REG_SZ, hw_info["total_ram"])
        winreg.SetValueEx(key, "HWINFO_STR", 0, winreg.REG_SZ, hw_info["disk_total"])
        winreg.SetValueEx(key, "MUKKURU_FORCE_FULLSCREEN", 0, winreg.REG_SZ, "1")
        winreg.SetValueEx(key, "MUKKURU_NO_EXIT", 0, winreg.REG_SZ, "1")
        #winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "1")

def restrict_users(group_name:str):
    ''' restrict users from a specific group to minimize risks to your isolated setup ( ex: cloud gaming) '''
    users = get_group_users(group_name)
    if users is None:
        print("Failed to restrict users: No users found in group")
        return
    for user in users:
        user_path = username_to_profile_path(user)
        if user_path is None:
            print(f"Unable to get user path for user: {user}")
            continue
        user_sid = username_to_sid(user)
        if user_sid is None:
            print(f"Unable to get sid for user: {user}")
            continue
        print(f"Restricting user {user} - {user_sid} (location: {user_path})")
        continue
        # dry run
        hive_root = load_user_hive(user_sid, user_path)
        if hive_root is None:
            print(f"Unable to load hive_root for user: {user}")
            continue
        try:
            disable_user_features(hive_root)
            set_mukkuru_as_shell(hive_root)
            clone_sandbox_to_user("Mukkuru", user)
        except (PermissionError, OSError) as e:
            print(f"An error occured trying to restrict user {user}: {str(e)}")
        finally:
            unload_user_hive(user_sid)

# Sandboxie
def get_sandbox_path(username: str, box_name: str) -> str:
    ''' Returns Sandboxie box path '''
    return fr"C:\Sandbox\{username}\{box_name}"
    #return fr"{username_to_profile_path(username)}\AppData\Local\Sandbox\{box_name}"

def fix_permissions(path: str):
    """Fix ACLs so the target user has full access."""
    subprocess.run([
        "icacls", path,
        "/inheritance:e",
        "/reset", "/t"
    ], capture_output=True, text=True)

def update_sandboxie_ini(box_name: str, src_user: str, dst_user: str):
    """
    Adjust path references inside the global Sandboxie.ini file.
    IMPORTANT:
        - This modifies only the entries for `box_name`
        - Only replaces paths that point to src_user → dst_user
    """
    ini_path = r"C:\Windows\Sandboxie.ini"
    program_files = os.environ.get("ProgramFiles", None)
    if not os.path.exists(ini_path):
        ini_path = os.path.join(program_files, "Sandboxie-Plus", "Sandboxie.ini")
    if not os.path.exists(ini_path):
        print("Sandboxie.ini not found.")
        return

    with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    src_path = username_to_profile_path(src_user)
    dst_path = username_to_profile_path(dst_user)

    new_lines = []
    inside_box = False

    for line in lines:
        # detect box section
        if line.strip().lower() == f"[{box_name.lower()}]":
            inside_box = True
        elif line.startswith("[") and inside_box:
            inside_box = False

        if inside_box:
            # Replace only inside this box's section
            new_lines.append(line.replace(src_path, dst_path))
        else:
            new_lines.append(line)

    with open(ini_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def clone_sandbox_to_user(box_name: str, dst_user: str):
    """Clone a Sandboxie box from the current user to other users."""
    src_user = os.getlogin()
    src_path = get_sandbox_path(src_user, box_name)

    if not os.path.isdir(src_path):
        print(f"Source sandbox '{box_name}' not found for current user.")
        return

    dst_path = get_sandbox_path(dst_user, box_name)

    print(f"\n=== CLONING '{box_name}' FOR USER '{dst_user}' ===")

    if not os.path.isdir(username_to_profile_path(dst_user)):
        print(f"User profile for {dst_user} does not exist — skipping.")
        return

    # remove old clone if exists
    if os.path.isdir(dst_path):
        shutil.rmtree(dst_path, ignore_errors=True)

    try:
        shutil.copytree(src_path, dst_path)
    except Exception as e:
        print(f"Failed copying to {dst_user}: {e}")
        return

    print("Fixing ACL permissions...")
    fix_permissions(dst_path)

    print("Updating Sandboxie.ini paths...")
    update_sandboxie_ini(box_name, src_user, dst_user)

    print(f"Successfully cloned sandbox for {dst_user}.")
