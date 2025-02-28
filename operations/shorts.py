import os
import logging
from pathlib import Path

from moviepy import editor
from moviepy.editor import ColorClip, CompositeVideoClip, VideoFileClip

from config_loader import config_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def blur_video(video_path: str) -> str:
    new_video_path = f"blurred_{Path(video_path).name}"
    with VideoFileClip(video_path) as video:
        video_wo_audio = video.without_audio()
        video_wo_audio.write_videofile(
            new_video_path,
            ffmpeg_params=["-vf", "boxblur=10:1"],
            preset="ultrafast",
            threads=8,
            fps=24,
            codec="libx264",
        )
    return new_video_path


def generate_video_base(video_path_data: str, video_size=(1080, 1920)):
    video_path_output = f"output_{Path(video_path_data).name}"
    blurred_video_name = blur_video(video_path_data)
    blurred_video = VideoFileClip(blurred_video_name).resize(height=video_size[1])
    video = VideoFileClip(video_path_data).resize(width=video_size[0])
    video_base = ColorClip(video_size, color=(0, 0, 0)).set_duration(video.duration)
    composite = CompositeVideoClip(
        [video_base, blurred_video.set_position("center"), video.set_position("center")]
    ).set_duration(video.duration)
    composite.write_videofile(
        video_path_output, preset="ultrafast", threads=8, fps=24, codec="libx264"
    )
    os.remove(blurred_video_name)
    logger.info("Base video generated on %s", video_path_output)


def add_titles(video_path: str):
    video = VideoFileClip(video_path)
    title_clips = []
    duration = 3  # Duración de cada título
    for title in config_data.get("titles", []):
        if not title or not title.strip():
            continue
        title_clip = editor.TextClip(
            title, **config_data["titles_clip_config"]
        ).set_duration(duration)
        pos = ("center", config_data["titles_position"]["text_position_y_offset"])
        title_clip = title_clip.set_position(pos)
        title_clips.append(title_clip)
    if not title_clips:
        logger.info("No titles to add.")
        return

    final_clip = editor.concatenate_videoclips(title_clips + [video])
    output_path = f"output_titles_{Path(video_path).name}"
    final_clip.write_videofile(
        output_path, preset="ultrafast", threads=8, fps=24, codec="libx264"
    )
    logger.info("Video with titles saved at: %s", output_path)
