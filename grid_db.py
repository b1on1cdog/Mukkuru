import os, requests, re, unicodedata # type: ignore
from PIL import Image

api_key = "90b0bd6347884051541cd12b0ec7f73e"

def search_game(term):
    url = f'https://www.steamgriddb.com/api/v2/search/autocomplete/{term}'
    r=requests.get(url, headers={"Authorization":f'Bearer {api_key}'})
    data = r.json()
    if data["success"]:
        games = data["data"]
        return games
    else:
        return 0
    
def get_game_id(term):
    game = search_game(term)
    if game == 0:
        return 0
    else:
        return game[0]["id"]

def find_square_pic(gameId):
    dimensions = "512x512,1024x1024"
    url = f'https://www.steamgriddb.com/api/v2/grids/game/{gameId}?dimensions={dimensions}'
    r=requests.get(url, headers={"Authorization":f'Bearer {api_key}'})
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
    with open(path, 'wb') as out_file:
        content = requests.get(url, stream=True).content
        out_file.write(content)
        r=requests.get(url, headers={"Authorization":f'Bearer {api_key}'})

def sanitize_filename_ascii(name, max_length=255):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    name = name.replace('.', '')
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
    name = name.rstrip(' ')
    name = re.sub(r'_+', '_', name)
    return name[:max_length]

def download_square_image(term, savePath ="", gameId=0):
    if gameId == 0:
        gameId = get_game_id(term)
    if gameId == 0:
      #  print("Failed to find game")
        return False
    fileURL = find_square_pic(gameId)
    if fileURL == 0:
     #   print("Failed to find game assets")
        return False
    extension = "jpg"
    if fileURL.endswith(".png"):
        extension = "png"
    elif fileURL.endswith(".webp"):
        extension = "webp"
    outputFile = os.path.join( savePath, f'{sanitize_filename_ascii(term)}.{extension}')
    download_file(fileURL, outputFile)
    if extension != "jpg":
        newFile = outputFile.replace(f".{extension}", ".jpg")
        im = Image.open(outputFile)
        im.convert('RGB').save(newFile,"JPEG")
        os.remove(outputFile)
        return newFile
    return outputFile
