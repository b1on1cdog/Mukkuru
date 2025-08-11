# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
'''
Mukkuru module for file conversions\n
Imports utils.bootstrap\n
'''
import os
import subprocess
from pathlib import Path

from utils.core import backend_log
from utils.bootstrap import get_ffmpeg

OPTION_VIDEO = 1 << 0
OPTION_AUDIO = 1 << 1
OPTION_SUBTITLES = 1 << 2
OPTION_DATA = 1 << 3
OPTION_ATTACHMENT = 1 << 4

OPTION_ALL = OPTION_VIDEO | OPTION_AUDIO | OPTION_SUBTITLES
OPTION_ALL = OPTION_ALL | OPTION_DATA | OPTION_ATTACHMENT

def check_remux_possible(input_file: str, options:int = OPTION_ALL):
    ''' do a dry run for testing video encoding '''
    ffmpeg = [get_ffmpeg(),
              "-v", "error",
              "-i", input_file]
    if options & OPTION_ALL:
        ffmpeg.extend(["-map", "0"])
    else:
        if options & OPTION_VIDEO:
            ffmpeg.extend(["-map", "0:v"])
        if options & OPTION_AUDIO:
            ffmpeg.extend(["-map", "0:a"])
        if options & OPTION_SUBTITLES:
            ffmpeg.extend(["-map", "0:s"])
        if options & OPTION_DATA:
            ffmpeg.extend(["-map", "0:d"])
    ffmpeg.extend(["-c", "copy"])
    ffmpeg.extend(["-f", "mp4",
        "-t", "1",
        "-y",
        os.devnull])

    result = subprocess.run(ffmpeg, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        backend_log(f"FFmpeg error: {result.stderr}")
        return False

    if result.stderr.strip():
        backend_log(f"FFmpeg error output:{result.stderr}")
        return False

    return True

def remux_video(input_file: str, output_file: str):
    ''' copy video stream without re-encoding '''
    cmd = [
        get_ffmpeg(),
        "-v", "error",
        "-i", input_file,
        "-map", "0",
        "-c", "copy",
        "-f", "mp4",
        "-y",
        output_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        backend_log(f"FFmpeg error: {result.stderr}")
        return False

    if result.stderr.strip():
        backend_log(f"FFmpeg error output:{result.stderr}" )
        return False
    return True

def encode_video(input_file: str, output_file: str):
    ''' encode videos '''
    ffmpeg = []
    ffmpeg.append(get_ffmpeg())
    ffmpeg.extend(["-v", "error"])
    ffmpeg.extend(["-i", input_file])
    ffmpeg.extend(["-f", "mp4"])
    ffmpeg.append("-y")
    ffmpeg.append(output_file)

    result = subprocess.run(ffmpeg, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        backend_log(f"FFmpeg error: {result.stderr}")
        return False

    if result.stderr.strip():
        backend_log(f"FFmpeg error output:{result.stderr}" )
        return False
    return True

def auto_conversion(input_file: str, output_dir: str):
    ''' detects what conversion file needs '''
    video_ext = ["mp4", "m4v", "mov", "mkv", "ts", "flv", "avi", "mpg"]
    music_ext = ["mp3", "wav", "ogg"]
    image_ext = ["jpg", "png", "webp"]
    extension = Path(input_file).suffix.replace(".", "")
    if extension in video_ext:
        remuxable = check_remux_possible(input_file)
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        if remuxable:
            remux_video(input_file, output_file)
        else:
            encode_video(input_file, output_file)
    elif extension in music_ext:
        pass
    elif extension in image_ext:
        pass
    return True
