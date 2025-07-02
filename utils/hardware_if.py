# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Contains functions regarding hardware information, written by b1on1cdog '''
import socket
import platform
import subprocess
import os
import re
from functools import lru_cache
import math

import psutil
import distro

system = platform.system()

@lru_cache(maxsize=1)
def get_cpu_name():
    ''' get cpu name as string '''

    if system == "Windows":
        try:
            output = subprocess.check_output(["wmic", "cpu", "get", "Name"], shell=True)
            lines = output.decode().splitlines()
            # Remove empty lines and strip whitespace
            lines = [line.strip() for line in lines if line.strip()]
            if len(lines) > 1:
                return lines[1]
        except (subprocess.CalledProcessError, IndexError, UnicodeDecodeError):
            pass
        return platform.processor()
    if system == "Darwin":  # macOS
        try:
            return subprocess.check_output(["sysctl",
                                            "-n", "machdep.cpu.brand_string"]).decode().strip()
        except (subprocess.CalledProcessError, IndexError, UnicodeDecodeError):
            return platform.processor()

    if system == "Linux":
        try:
            with open("/proc/cpuinfo", encoding='utf-8') as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except (FileNotFoundError, PermissionError, IndexError):
            pass
        return platform.processor()
    return "Unknown CPU"

@lru_cache(maxsize=1)
def get_gpu_name():
    ''' get GPU name '''

    if system == "Windows":
        try:
            output = subprocess.check_output(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                shell=True
            )
            lines = output.decode().splitlines()
            lines = [line.strip() for line in lines if line.strip()]
            return lines[1] if len(lines) > 1 else "Unknown GPU"
        except (subprocess.CalledProcessError, IndexError, UnicodeDecodeError, PermissionError):
            return "Unknown GPU"

    elif system == "Linux":
        try:
            output = subprocess.check_output(
                ["lspci"], stderr=subprocess.DEVNULL
            ).decode()
            gpus = []
            for line in output.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    gpus.append(line)
            return gpus[0].split(":")[-1].strip() if gpus else "Unknown GPU"
        except (PermissionError, IndexError, subprocess.CalledProcessError):
            return "Unknown GPU"

    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"]
            ).decode()
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("Chipset Model:"):
                    return line.split(":", 1)[1].strip()
            return "Unknown GPU"
        except (IndexError, UnicodeDecodeError, PermissionError):
            return "Unknown GPU"

    return "Unknown GPU"

@lru_cache(maxsize=1)
def get_info():
    ''' gets a dictionary with most hardware info '''
    memory_info = psutil.virtual_memory()
    platform_info = platform.uname()

    hardware_info = {}

    hardware_info["total_ram"] = round(memory_info.total/(1024*1024*1024),1)
    hardware_info["used_ram"] = round(memory_info.used/(1024*1024*1024),1)

    hardware_info["computer_name"] = platform_info.node
    hardware_info["arch"] = platform_info.machine
    hardware_info["os"] = platform_info.system

    hardware_info["distro"] = hardware_info["os"]

    if hardware_info["os"] == "Linux":
        hardware_info["distro"] = distro.name(pretty=True)
        xdg = os.environ.get("XDG_SESSION_DESKTOP", "").lower()
        if "gamescope" in xdg:
            hardware_info["distro"] = hardware_info["distro"] + " (Gaming Mode)"
    elif hardware_info["os"] == "Windows":
        try:
            output = subprocess.check_output(['wmic', 'os', 'get', 'Caption'], shell=True)
            lines = output.decode().splitlines()
            # to-do: fix possible empty reply if lines[2] returns nothing
            hardware_info["distro"] = lines[2].strip() if len(lines) > 1 else "Microsoft Windows"
        except subprocess.CalledProcessError:
            hardware_info["distro"] = "Windows"

    disk_info = psutil.disk_usage('/')
    if hardware_info["os"] == "Linux":
        disk_info = psutil.disk_usage('/home')
    hardware_info["disk_total"] = math.ceil(disk_info.total/(1000*1000*1000))
    hardware_info["disk_used"] = round(disk_info.used/(1000*1000*1000),1)
    hardware_info["disk_free"] = round(disk_info.free/(1000*1000*1000),1)
    hardware_info["cpu"] = get_cpu_name()
    gpu = get_gpu_name()
    if "Custom GPU 0405" in gpu:
        gpu = "AMD Custom GPU 0405"

    gpu = gpu.replace("Advanced Micro Devices, Inc. ", "")
    gpu = gpu.replace("[AMD/ATI] ", "")
    hardware_info["gpu"] = gpu
    return hardware_info

def get_active_net_interfaces():
    ''' get net interfaces as an array'''
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    active = []
    for iface, info in stats.items():
        if info.isup and iface in addrs:
            active.append(iface)
    return active

def has_internet(host="8.8.8.8", port=53, timeout=0.3):
    ''' Ping servers to determine whether device has access to net '''
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except TimeoutError:
        return False

def get_current_interface(get_ip = False):
    ''' determine current network interface using a dummy socket'''
    # Step 1: Create a dummy socket connection to a public IP (Google DNS)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # doesn't actually send data
            local_ip = s.getsockname()[0]
            if get_ip:
                return local_ip
    except (TimeoutError) as e:
        print(f"Could not determine local IP: {e}")
        return None

    # Step 2: Match local IP to a network interface
    interfaces = psutil.net_if_addrs()
    for iface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == local_ip:
                return iface

    return None

def connection_status():
    ''' returns a json with connection status'''
    status = {}
    status["wifi"] = is_using_wireless()
    status["internet"] = has_internet() or has_internet()
    if status["internet"] is False:
        status["internet"] = has_internet(host="8.8.4.4") or has_internet(host="1.1.1.1")
    status["signal"] = wireless_signal()
    return status


def is_using_wireless():
    ''' return whether a Wireless connection is being used '''
    interface = get_current_interface()
    if system == "Darwin":
        try:
            hwports = subprocess.check_output(["networksetup", "-listallhardwareports"]).decode()
            blocks = hwports.strip().split("Hardware Port:")
            for block in blocks:
                if "Wi-Fi" in block or "AirPort" in block:
                    match = re.search(r"Device: (\w+)", block)
                    if match and match.group(1) == interface:
                        return True
            return False
        except (IndexError, PermissionError):
            return False
    if system == "Linux":
        return os.path.isdir(f"/sys/class/net/{interface}/wireless")
    if system == "Windows":
        try:
            output = subprocess.check_output("netsh wlan show interfaces",
                                             shell=True).decode(errors="ignore")
            return interface.lower() in output.lower()
        except (IndexError, subprocess.CalledProcessError, PermissionError):
            return False

def wireless_signal():
    '''Get the signal of Wi-Fi'''
    return 100

def get_battery():
    ''' returns battery'''
    battery = psutil.sensors_battery()
    if battery is None:
        return None
    return battery._asdict()

def kill_executable_by_path(target_path):
    """
    Hard-kill every running process whose executable exactly matches `target_path`.
    """
    target_path = os.path.abspath(target_path)
    killed = []

    for proc in psutil.process_iter(['pid', 'exe']):
        try:
            if proc.info['exe'] and os.path.abspath(proc.info['exe']) == target_path:
                proc.kill()
                killed.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Skip processes that vanished or we can't touch
            continue
    return killed
