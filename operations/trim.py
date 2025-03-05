import logging
import numpy as np

from utils import get_subclip_volume


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def trim_by_silence(**kwargs):
    input_video_file_clip = kwargs["input_video_file_clip"]
    clip_interval = kwargs["clip_interval"]
    sound_threshold = kwargs["sound_threshold"]
    discard_silence = kwargs["discard_silence"]
    logger.info("Chunking video...")
    volumes = []
    for i in np.arange(0, input_video_file_clip.duration, clip_interval):
        if input_video_file_clip.duration <= i + clip_interval:
            continue
        logger.info("Processing chunk %s/%s", i, input_video_file_clip.duration)

        volumes.append(get_subclip_volume(input_video_file_clip, i, clip_interval))
    logger.info("Processing silences...")
    volumes = np.array(volumes)
    volumes_binary = volumes > sound_threshold
    change_times = [0]
    for i in range(1, len(volumes_binary)):
        if volumes_binary[i] != volumes_binary[i - 1]:
            change_times.append(i * clip_interval)
    change_times.append(input_video_file_clip.duration)
    logger.info("Subclipping...")
    first_piece_silence = 1 if volumes_binary[0] else 0
    clips = []
    for i in range(1, len(change_times)):
        if discard_silence and i % 2 != first_piece_silence:
            continue
        new_clip = input_video_file_clip.subclip(change_times[i - 1], change_times[i])
        clips.append(new_clip)
    kwargs["clips"] = clips
    return kwargs
