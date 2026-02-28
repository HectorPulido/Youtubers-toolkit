"""
Module to trim a video by silence.
"""

import logging
import librosa
import numpy as np
from scipy.signal import butter, sosfilt

from utils import otsu_threshold


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def trim_by_silence(**kwargs):
    """
    Function to trim a video by silence.
    """
    input_video_file_clip = kwargs["input_video_file_clip"]
    video_path            = kwargs["video_path"]
    clip_interval         = kwargs["clip_interval"]
    sound_threshold       = kwargs["sound_threshold"]
    discard_silence       = kwargs["discard_silence"]
    voice_filter          = kwargs.get("voice_filter", False)

    # --- Step 1: load full audio once (fast, single decode) ---
    logger.info("Loading audio for RMS analysis...")
    y, sr = librosa.load(video_path, sr=None, mono=True)

    # --- Step 1b (optional): bandpass filter to isolate voice frequencies ---
    if voice_filter:
        logger.info("Applying voice bandpass filter (85-3400 Hz)...")
        sos = butter(5, [85, 3400], btype="band", fs=sr, output="sos")
        y = sosfilt(sos, y)
    hop_length = int(clip_interval * sr)

    # --- Step 2: vectorized RMS for every chunk ---
    rms_array = librosa.feature.rms(
        y=y, frame_length=hop_length, hop_length=hop_length
    )[0]

    # Keep only full chunks (mirrors original loop's skip-last-partial logic)
    n_chunks = int(input_video_file_clip.duration / clip_interval)
    rms_array = rms_array[:n_chunks]

    # --- Step 3: auto-threshold via Otsu if not supplied ---
    if sound_threshold is None:
        sound_threshold = otsu_threshold(rms_array)
        logger.info("Auto threshold (Otsu): %.5f", sound_threshold)

    # --- Step 4: same change-detection + subclip logic as before ---
    volumes_binary = rms_array > sound_threshold
    change_times = [0.0]
    for i in range(1, len(volumes_binary)):
        if volumes_binary[i] != volumes_binary[i - 1]:
            change_times.append(i * clip_interval)
    change_times.append(input_video_file_clip.duration)

    first_piece_silence = 1 if volumes_binary[0] else 0
    clips = []
    for i in range(1, len(change_times)):
        if discard_silence and i % 2 != first_piece_silence:
            continue
        clips.append(
            input_video_file_clip.subclip(change_times[i - 1], change_times[i])
        )
    kwargs["clips"] = clips
    return kwargs
