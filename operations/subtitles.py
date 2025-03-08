"""
Module to add subtitles to a video using moviepy.
"""

import os
from moviepy.editor import TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip


def add_subtitles(**kwargs):
    """
    Add subtitles to a video clip.
    """

    def generator(txt):
        return TextClip(txt, **config_data["subtitles_clip_config"])

    filename = kwargs["filename"]
    input_video_file_clip = kwargs["input_video_file_clip"]
    subtitles_filename = kwargs.get(
        "transcript_file_name", f"{filename}_transcript.srt"
    )
    config_data = kwargs.get("config_data", {})
    if not os.path.exists(subtitles_filename):
        subtitles_filename = f"{filename}_transcript.srt"

    subtitles = SubtitlesClip(subtitles_filename, generator)
    video_list = [
        input_video_file_clip,
        subtitles.set_pos(
            (
                "center",
                input_video_file_clip.h
                + config_data["subtitles_position"]["text_position_y_offset"],
            )
        ),
    ]
    video_with_subs = CompositeVideoClip(video_list)
    kwargs["input_video_file_clip"] = video_with_subs
    return kwargs
