"""
Generating an avatar video based on audio input.
"""

import logging
import os
import subprocess

import moviepy.editor as mpe
import numpy as np

from utils import apply_shake, get_subclip_volume_segment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

MODEL_SIZE = "turbo"

EMOTION = {
    "anger": "avatar_angry",
    "sadness": "avatar_sad",
    "joy": "avatar_wow",
    "fear": "avatar_angry",
    "disgust": "avatar_angry",
    "surprise": "avatar_wow",
    "neutral": "avatar_calm",
}


def render_segment(avatar_segment, segment_index):
    """
    Render a segment of the avatar video.
    """
    output_path = f"temp_segment_{segment_index:03d}.mp4"
    logger.info("Export segment %d to %s...", segment_index, output_path)
    avatar_segment.write_videofile(
        output_path, codec="libx264", audio=False, verbose=False, logger=None
    )
    return output_path


def concatenate_segments_ffmpeg(segment_paths, final_output, audio_path):
    """
    Use FFmpeg to concatenate segments and add the audio track.
    First concatenate the segments without audio and then incorporate the original audio.
    """
    list_filename = "segments.txt"
    with open(list_filename, "w", encoding="utf-8") as f:
        for path in segment_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")

    temp_video = "temp_video.mp4"
    logger.info("Merging segments...")
    concat_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_filename,
        "-c",
        "copy",
        temp_video,
    ]
    subprocess.run(concat_command, check=True)

    logger.info("Adding audio...")
    final_command = [
        "ffmpeg",
        "-i",
        temp_video,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        final_output,
    ]
    subprocess.run(final_command, check=True)

    # Limpieza de archivos temporales
    os.remove(list_filename)
    os.remove(temp_video)
    for path in segment_paths:
        os.remove(path)
    logger.info("Final video exported to %s", final_output)


def generate_segment(audio_path, audio_clip):
    """
    Generate segments based on audio input.
    """
    try:
        import torch
        from faster_whisper import WhisperModel
        from pydub import AudioSegment
        from transformers import pipeline
    except ImportError as e:
        logger.error("Error importing required libraries: %s", e)
        return [], 0

    logger.info("Load audio (pydub)...")
    pydub_audio = AudioSegment.from_file(audio_path)
    logger.info("Transcribing audio...")
    whisper_model = WhisperModel(MODEL_SIZE)
    result, _ = whisper_model.transcribe(audio_path, multilingual=True)

    logger.info("Starting emotion classifier...")
    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=1,
    )
    segments = []
    volumes = []
    for seg in result:
        start = seg.start
        end = seg.end
        text = seg.text.strip()
        duration = end - start

        classifier_result = emotion_classifier(text)[0][0]
        emotion = EMOTION.get(classifier_result["label"], "avatar_calm")

        volume = get_subclip_volume_segment(pydub_audio, start, duration)
        segments.append(
            {"start": start, "end": end, "emotion": emotion, "volume": volume}
        )
        volumes.append(volume)
        logger.info(
            "Segment %f-%fs, Emotion: %s, Volume (RMS): %f",
            start,
            end,
            emotion,
            volume,
        )

    global_avg_volume = np.mean(volumes)
    logger.info("General average volume: %f", global_avg_volume)

    total_duration = sum(seg["end"] - seg["start"] for seg in segments)
    if total_duration < audio_clip.duration:
        logger.info(
            "Adding calm segment to fill the gap between segments and audio duration."
        )
        segments.append(
            {
                "start": total_duration,
                "end": audio_clip.duration,
                "emotion": "avatar_calm",
                "volume": global_avg_volume,
            }
        )

    del whisper_model
    del emotion_classifier
    torch.cuda.empty_cache()

    return segments, global_avg_volume


def generate_avatar_video(audio_path: str, config: dict):
    """
    Process audio to generate a video with avatars based on emotions.
    """
    avatars = config.get("avatars", {})
    shake_factor = config.get("shake_factor", 0.1)

    try:
        logger.info("Load audio/video for final extraction (moviepy)...")
        clip = mpe.VideoFileClip(audio_path)
        audio_clip = clip.audio
    except Exception:
        logger.info("Cannot load as video; loading as audio with moviepy...")
        audio_clip = mpe.AudioFileClip(audio_path)
        clip = None

    segments, global_avg_volume = generate_segment(audio_path, audio_clip)

    avatar_clips = []
    for i, seg in enumerate(segments):
        emotion = seg["emotion"]
        volume = seg["volume"]
        intensity = (volume / global_avg_volume) * shake_factor

        avatar_path = avatars.get(emotion)
        if not avatar_path:
            logger.warning(
                "Did not find avatar for emotion '%s'. Skipping segment.",
                emotion,
            )
            continue

        logger.info(
            "Processing segment with %s and shake intensity %.2f", emotion, intensity
        )
        avatar_video = mpe.VideoFileClip(avatar_path).without_audio()
        segment_duration = seg["end"] - seg["start"]
        avatar_segment = avatar_video.loop(duration=segment_duration)
        avatar_segment = apply_shake(avatar_segment, intensity)

        title = f"temp_{i:03d}_{emotion}.mp4"
        logger.info("Exporting segment to %s", title)
        avatar_segment.write_videofile(
            title, codec="libx264", audio=False, verbose=False, logger=None
        )
        avatar_clips.append(title)

    if not avatar_clips:
        logger.error("Didn't generate any clips. Exiting.")
        return

    final_output = "output_video.mp4"
    concatenate_segments_ffmpeg(avatar_clips, final_output, audio_path)

    for path in avatar_clips:
        os.remove(path)
