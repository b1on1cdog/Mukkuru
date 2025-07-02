'''module for Mukkuru video handling'''
import re
import os
import hashlib
import json
import base64
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict

# To-do list
# Store playing video duration, user might want to resume it later
# there should be a list [] of user video sources in mukkuru config.json
SHOWS_PATTERN = re.compile(
    r"""
    ^(?P<title>.+?)
    (?:\s*[-_\s]+\s*)?
    [sS](?P<season>\d{1,2})
    [eE](?P<episode>\d{1,3})
    \b
    """,
    re.VERBOSE,
)

def group_by_show(paths):
    ''' organize whole series in a single collection '''
    shows = defaultdict(list)
    for p in map(Path, paths):
        m = SHOWS_PATTERN.match(p.stem)
        if m:
            title = re.sub(r'[\s_-]+', ' ', m.group('title')).strip().lower()
            shows[title].append(p)
        else:
            shows[None].append(p)
    return shows

#video_files = [f for f in source_dir.rglob("*") if f.suffix.lower() in extensions and f.is_file()]
def read_videos(source_dir, source_index = -1):
    ''' Fetch videos from disk '''
    videos = {}
    extensions = ["mp4", "m4v"]
    video_files = []
    for extension in extensions:
        video_files.extend([f for f in os.listdir(source_dir) if f.lower().endswith(extension)])
    #video_collections = group_by_show(video_files)
    for video in video_files:
        extension = Path(video).suffix.replace(".", "")
        if extension in extensions:
            video_path = os.path.join(source_dir, video)
            video_id = sha256_hash_text(video)
            if video_id not in videos:
                videos[video_id] = {}
            videos[video_id]["path"] = video_path
            videos[video_id]["file"] = video
            th_name = f"{os.path.splitext(video)[0]}-thumbnail.png"
            videos[video_id]["thumbnail"] = os.path.join(source_dir, th_name)
            if source_index > -1:
                videos[video_id]["url"] = f"video/{source_index}/{quote(video)}"
                videos[video_id]["thumbnail_url"] = f"video/{source_index}/{quote(th_name)}"
    return videos

def check_thumbnails(videos):
    ''' verify video thumbnails still exists '''
    for video_id, video in videos.items():
        thumbnail_path = video["thumbnail"]
        if Path(thumbnail_path).exists():
            videos[video_id]["thumbnail_exists"] = True
        else:
            videos[video_id]["thumbnail_exists"] = False
    return videos

def get_videos(source_dirs, video_manifest_path):
    ''' Get videos from all specified dirs '''
    videos = {}
    source_index = 0
    for source_dir in source_dirs:
        videos.update(read_videos(source_dir, source_index))
        source_index = source_index + 1
    if not Path(video_manifest_path).is_file():
        update_videos(video_manifest_path, videos)
    with open(video_manifest_path, encoding='utf-8') as f:
        videos.update(json.load(f))
    videos = check_thumbnails(videos)
    update_videos(video_manifest_path, videos)
    return videos

def update_thumbnail(video_manifest_path, video_id, thumbnail):
    ''' update thumbnail for specific video id '''
    videos = {}
    with open(video_manifest_path, encoding='utf-8') as f:
        videos = json.load(f)
    thumbnail_b64 = thumbnail.replace("data:image/png;base64,", "")
    image_data = base64.b64decode(thumbnail_b64)
    with open(videos[video_id]["thumbnail"], "wb") as f:
        f.write(image_data)

def update_videos(video_manifest_path, videos):
    ''' update videos json '''
    with open(video_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(videos, f)

def sha256_hash_text(text):
    ''' get sha256 of a string '''
    hash_object = hashlib.sha256(text.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig
