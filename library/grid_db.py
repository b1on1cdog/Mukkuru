# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' Download art from steamgriddb '''
import os
import re
import unicodedata
import requests
from PIL import Image

API_KEY = ""
# API_URL = "https://www.steamgriddb.com/api/v2/"
API_URL = "https://api.panyolsoft.com/steamgriddb/"

class GameIdentifier(object):
    ''' This object will have the required information to identify a game '''
    def __init__(self, title, app_id, platform):
        self.title = title
        self.app_id = app_id
        self.platform = platform

def search_game(term):
    ''' search for game using a title term '''
    url = f'{API_URL}search/autocomplete/{term}'
    try:
        r=requests.get(url, headers={"Authorization":f'Bearer {API_KEY}'}, timeout=20)
        data = r.json()
        if data["success"]:
            games = data["data"]
            return games
        else:
            return 0
    except (requests.exceptions.JSONDecodeError, IndexError, KeyError):
        return 0
def get_game_id(term):
    ''' find game id using a title name '''
    game = search_game(term)
    if game == 0:
        return 0
    try:
        return game[0]["id"]
    except (IndexError, KeyError):
        return 0

def get_id_from_platform(platform_id, platform_name):
    ''' find game id using a title name '''
    url = f'{API_URL}games/{platform_name}/{platform_id}'
    r=requests.get(url, headers={"Authorization":f'Bearer {API_KEY}'}, timeout=20)
    try:
        data = r.json()
        if data["success"]:
            return data["data"]["id"]
        else:
            return 0
    except KeyError:
        return 0
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON")
        return 0

def find_image_url(game_id, image_format):
    ''' find square picture '''
    if image_format == "1:1":
        dimensions = "512x512,1024x1024"
        url = f'{API_URL}grids/game/{game_id}?dimensions={dimensions}'
    elif image_format == "hero":
        mimes = "image/png"
        url = f'{API_URL}heroes/game/{game_id}?mimes={mimes}'
    elif image_format == "logo":
        mimes = "image/png"
        url = f'{API_URL}logos/game/{game_id}?mimes={mimes}'
    else:
        return 0
    r=requests.get(url, headers={"Authorization":f'Bearer {API_KEY}'}, timeout=20)
    data = r.json()
    if data["success"]:
        try:
            games = data["data"]
            return games[0]["url"]
        except (KeyError, IndexError):
            return 0
    else:
        return 0

def download_file(url, path):
    ''' download file from url '''
    with open(path, 'wb') as out_file:
        content = requests.get(url, stream=True, timeout=20).content
        out_file.write(content)
        #r=requests.get(url, headers={"Authorization":f'Bearer {API_KEY}'}, timeout=20)

def sanitize_filename_ascii(name, max_length=255):
    ''' removes characters so string become suitable for filename use '''
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    name = name.replace('.', '')
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
    name = name.rstrip(' ')
    name = re.sub(r'_+', '_', name)
    return name[:max_length]

def download_square_image(game_identifier, s_path):
    ''' download a 1:1 image '''
    return download_image(game_identifier, s_path, "1:1")

def download_image(game_identifier, s_path, image_format):
    ''' find and download image from SteamGridDb '''  
    game_id = 0
    game_title = game_identifier.title
    if game_identifier.app_id != 0 and game_identifier.platform != "non-steam":
        game_id = get_id_from_platform(game_identifier.app_id, game_identifier.platform)
    else:
        game_id = get_game_id(game_title)
    if game_id == 0:
        print(f"Failed to find game {game_title}")
        return False
    file_url = find_image_url(game_id, image_format)
    if file_url == 0:
        print(f"Failed to find game asset : {game_title} [{image_format}]")
        return "Missing"
    extension = "jpg"
    if file_url.endswith(".png"):
        extension = "png"
    elif file_url.endswith(".webp"):
        extension = "webp"
    if s_path.endswith('.png') or s_path.endswith('.jpg') or s_path.endswith('.webp'):
        output_file = s_path
        output_extension = output_file[-3:]
        if {extension} != output_extension:
            output_file = output_file.replace(f'.{output_extension}', f'.{extension}')
    else:
        output_file = os.path.join(s_path, f'{sanitize_filename_ascii(game_title)}.{extension}')
    download_file(file_url, output_file)
    if extension != "jpg" and image_format == "1:1":
        new_file = output_file.replace(f".{extension}", ".jpg")
        print(f'{output_file} > {new_file}')
        im = Image.open(output_file)
        im.convert('RGB').save(new_file,"JPEG")
        os.remove(output_file)
        return new_file
    return output_file
