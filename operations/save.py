"""
Module to save video clips using moviepy.
"""

from moviepy import editor


def save_video(**kwargs):
    """
    Save a video clip to a file.
    """
    filename = kwargs["filename"]
    input_video_file_clip = kwargs["input_video_file_clip"]
    clip_name = f"{filename}_EDITED.mp4"
    input_video_file_clip.write_videofile(
        clip_name,
        audio_codec="aac",
        threads=8,
        fps=24,
    )
    kwargs["clips_name"] = clip_name
    return kwargs


def save_joined_video(**kwargs):
    """
    Save a joined video clip to a file.
    """
    if "clips" not in kwargs:
        return save_video(**kwargs)
    filename = kwargs["filename"]
    clips = kwargs["clips"]
    clip_name = f"{filename}_EDITED.mp4"
    if isinstance(clips, list):
        concat_clip = editor.concatenate_videoclips(clips)
        concat_clip.write_videofile(
            clip_name,
            audio_codec="aac",
            threads=8,
            fps=24,
        )
        kwargs["clips_name"] = clip_name
        return kwargs
    clips.write_videofile(clip_name, audio_codec="aac")
    kwargs["clips_name"] = clip_name
    return kwargs


def save_separated_video(**kwargs):
    """
    Save separated video clips to files.
    """
    if "clips" not in kwargs:
        return save_video(**kwargs)
    filename = kwargs["filename"]
    clips = kwargs["clips"]
    clips_format = f"{filename}_EDITED_{{i}}.mp4"
    for i, clip in enumerate(clips):
        pad_i = str(i).zfill(5)
        clip.write_videofile(clips_format.format(i=pad_i), audio_codec="aac")
    kwargs["clips_name"] = clips_format.format(i="{i}")
    return kwargs
