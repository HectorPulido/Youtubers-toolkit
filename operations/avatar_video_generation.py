import logging
import os
import subprocess

from dotenv import load_dotenv
import moviepy.editor as mpe
import numpy as np
from openai import OpenAI

from utils import apply_shake, get_subclip_volume_segment


SYSTEM_PROMPT = (
    "You are an emotion classifier. "
    "Given a short phrase in any language, reply with exactly one of the following labels: "
    "{emotions}"
    "Respond with just the label, no extra text."
)

load_dotenv()
MODEL = os.getenv("MODEL", "gpt-4.1-2025-04-14")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "turbo")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _classify_emotion(text: str, config: dict) -> str:
    """
    Use ChatGPT to classify the emotion of a given text.
    """
    emotion = config.get("avatars", {})

    try:
        prompt = SYSTEM_PROMPT.replace("{emotions}", ", ".join(emotion.keys()))

        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )

        label = response.choices[0].message.content.strip().lower()
        # Ensure label is one of the dynamic keys
        if label not in emotion:
            logger.warning(
                "Received unexpected label '%s', defaulting to neutral", label
            )
            return list(emotion.keys())[0]
        return label
    except Exception as e:
        logger.error("ChatGPT API error: %s", e)
        return "neutral"


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
    subprocess.run(
        [
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
        ],
        check=True,
    )

    subprocess.run(
        [
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
        ],
        check=True,
    )

    # Cleanup temporary files
    os.remove(list_filename)
    os.remove(temp_video)
    for path in segment_paths:
        os.remove(path)
    logger.info("Final video exported to %s", final_output)


def generate_segment(audio_path, audio_clip, config: dict):
    """
    Generate segments based on audio input.
    Each segment is classified with a dynamic set of emotions via ChatGPT.
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore
        from pydub import AudioSegment  # type: ignore
    except ImportError as e:
        logger.error("Error importing required libraries: %s", e)
        return [], 0

    emotion: dict = config.get("avatars", {})

    logger.info("Load audio (pydub)...")
    pydub_audio = AudioSegment.from_file(audio_path)
    logger.info("Transcribing audio...")
    whisper_model = WhisperModel(WHISPER_MODEL_SIZE)
    result, _ = whisper_model.transcribe(audio_path, multilingual=True)

    segments = []
    volumes = []
    for seg in result:
        start, end = seg.start, seg.end
        text = seg.text.strip()
        duration = end - start

        # Classify emotion using ChatGPT
        label = _classify_emotion(text, config)
        emotion = emotion.get(label, list(emotion.keys())[0])

        volume = get_subclip_volume_segment(pydub_audio, start, duration)
        segments.append(
            {
                "start": start,
                "end": end,
                "emotion": emotion,
                "volume": volume,
            }
        )
        volumes.append(volume)
        logger.info(
            "Segment %f-%fs, Text: '%s', Emotion: %s, Volume: %f",
            start,
            end,
            text,
            emotion,
            volume,
        )

    global_avg_volume = np.mean(volumes) if volumes else 0
    logger.info("General average volume: %f", global_avg_volume)

    total_duration = sum(s["end"] - s["start"] for s in segments)
    if total_duration < audio_clip.duration:
        segments.append(
            {
                "start": total_duration,
                "end": audio_clip.duration,
                "emotion": "avatar_calm",
                "volume": global_avg_volume,
            }
        )

    del whisper_model
    return segments, global_avg_volume


def generate_avatar_video(audio_path: str, config: dict):
    """
    Process audio to generate a video with avatars based on dynamically classified emotions.
    """
    avatars = config.get("avatars", {})
    shake_factor = config.get("shake_factor", 0.1)

    try:
        clip = mpe.VideoFileClip(audio_path)
        audio_clip = clip.audio
    except Exception:
        audio_clip = mpe.AudioFileClip(audio_path)
        clip = None

    segments, global_avg_volume = generate_segment(audio_path, audio_clip, config)

    avatar_clips = []
    for i, seg in enumerate(segments):
        emotion, volume = seg["emotion"], seg["volume"]
        intensity = (
            (volume / global_avg_volume) * shake_factor if global_avg_volume > 0 else 0
        )

        avatar_path = avatars.get(emotion)
        if not avatar_path:
            logger.warning("No avatar for emotion '%s'. Skipping.", emotion)
            continue

        avatar_video = mpe.VideoFileClip(avatar_path).without_audio()
        avatar_segment = avatar_video.loop(duration=seg["end"] - seg["start"])
        avatar_segment = apply_shake(avatar_segment, intensity)

        out_name = f"temp_{i:03d}_{emotion}.mp4"
        avatar_segment.write_videofile(
            out_name, codec="libx264", audio=False, verbose=False, logger=None
        )
        avatar_clips.append(out_name)

    if not avatar_clips:
        logger.error("No clips generated. Exiting.")
        return

    final_output = "output_video.mp4"
    concatenate_segments_ffmpeg(avatar_clips, final_output, audio_path)

    # Cleanup individual segments
    for path in avatar_clips:
        os.remove(path)
