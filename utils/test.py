# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' This Mukkuru module will handle unit testing '''
from utils.updater import ver_compare, find_latest_release
from utils.bootstrap import get_7z, get_unrar, get_ffmpeg, get_userprofile_folder
from library.games import library_scan

def test_compare(ver1, ver2):
    '''test ver_compare'''
    test = ["lower", "equal", "bigger"]
    r = ver_compare(ver1, ver2)
    print(f"{ver1} is {test[r]} than {ver2}")
    return r

def test_scan():
    ''' test game scan '''
    games = library_scan(7)
    print(f"Found {len(games)} games")

def test_tools():
    ''' test tools paths '''
    zz = get_7z() or "None"
    unrar = get_unrar() or "None"
    ffmpeg = get_ffmpeg() or "None"
    print(f"7z path : {zz}")
    print(f"unrar path : {unrar}")
    print(f"ffmpeg path : {ffmpeg}")

def run_tests():
    ''' run multiple tests '''
    find_latest_release()
    #test_scan()
    #test_tools()
    #print(get_userprofile_folder("Downloads"))
    #print(get_userprofile_folder("Music"))
    #print(get_userprofile_folder("Videos"))
    #print(get_userprofile_folder("Pictures"))
