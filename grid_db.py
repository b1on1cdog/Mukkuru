''' re is imported for filename sanitization '''
import os
import re
import unicodedata
import requests
from PIL import Image

API_KEY = "90b0bd6347884051541cd12b0ec7f73e"

def search_game(term):
    ''' search for game using a title term '''
    url = f'https://www.steamgriddb.com/api/v2/search/autocomplete/{term}'
    r=requests.get(url, headers={"Authorization":f'Bearer {API_KEY}'}, timeout=20)
    data = r.json()
    if data["success"]:
        games = data["data"]
        return games
    else:
        return 0
def get_game_id(term):
    ''' find game id using a title name '''
    game = search_game(term)
    if game == 0:
        return 0
    else:
        return game[0]["id"]

def find_square_pic(game_id):
    ''' find square picture '''
    dimensions = "512x512,1024x1024"
    url = f'https://www.steamgriddb.com/api/v2/grids/game/{game_id}?dimensions={dimensions}'
    r=requests.get(url, headers={"Authorization":f'Bearer {API_KEY}'}, timeout=20)
    data = r.json()
    if data["success"]:
        try:
            games = data["data"]
            return games[0]["url"]
        except:
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

def download_square_image(term, save_path ="", game_id=0):
    ''' download a 1:1 image '''
    if game_id == 0:
        game_id = get_game_id(term)
    if game_id == 0:
      #  print("Failed to find game")
        return False
    file_url = find_square_pic(game_id)
    if file_url == 0:
     #   print("Failed to find game assets")
        return False
    extension = "jpg"
    if file_url.endswith(".png"):
        extension = "png"
    elif file_url.endswith(".webp"):
        extension = "webp"
    output_file = os.path.join( save_path, f'{sanitize_filename_ascii(term)}.{extension}')
    download_file(file_url, output_file)
    if extension != "jpg":
        new_file = output_file.replace(f".{extension}", ".jpg")
        im = Image.open(output_file)
        im.convert('RGB').save(new_file,"JPEG")
        os.remove(output_file)
        return new_file
    return output_file
