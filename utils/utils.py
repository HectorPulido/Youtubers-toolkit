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


def get_subclip_volume(subclip, second, interval):
    cut = subclip.subclip(second, second + interval).audio.to_soundarray(fps=44100)
    return np.sqrt(((1.0 * cut) ** 2).mean())


def get_subclip_volume_segment(audio_segment, start: float, duration: float) -> float:
    start_ms = int(start * 1000)
    end_ms = int((start + duration) * 1000)
    segment = audio_segment[start_ms:end_ms]
    return segment.rms


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


def apply_shake(clip, shake_intensity: float):
    """
    Apply shake effect to a clip.
    The image is randomly shifted in x and y according to the intensity.
    """

    def shake_transform(get_frame, t):
        frame = get_frame(t)
        dx = int(np.random.uniform(-shake_intensity, shake_intensity))
        dy = int(np.random.uniform(-shake_intensity, shake_intensity))
        shaken_frame = np.roll(frame, dx, axis=1)
        shaken_frame = np.roll(shaken_frame, dy, axis=0)
        return shaken_frame

    return clip.fl(shake_transform)
