import os
import argparse
from pathlib import Path

import numpy as np
from moviepy.editor import VideoFileClip


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def get_subclip_volume(subclip, start: float, interval: float) -> float:
    audio_array = subclip.subclip(start, start + interval).audio.to_soundarray(
        fps=44100
    )
    return np.sqrt((audio_array**2).mean())


def float_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{sec:02d},{milliseconds:03d}"


def get_audio(input_video_file_clip, filename: str) -> str:
    base = Path(filename)
    audio_file_name = f"{base}_audio.wav"
    audio_path = Path(audio_file_name)
    if audio_path.exists():
        audio_path.unlink()
    input_video_file_clip.audio.write_audiofile(str(audio_path), codec="pcm_s16le")
    return str(audio_path)


def get_video_data(**kwargs):
    video_path = kwargs["video_path"]
    filename = os.path.splitext(os.path.basename(video_path))[0]
    input_video_file_clip = VideoFileClip(video_path)
    kwargs["shape"] = input_video_file_clip.size
    kwargs["filename"] = filename
    kwargs["input_video_file_clip"] = input_video_file_clip
    return kwargs
