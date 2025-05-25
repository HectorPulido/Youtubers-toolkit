"""
Generating an avatar video based on audio input.
"""

import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "GPT-4.1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "turbo")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _classify_emotion(text: str, config: dict) -> str:
    """
    Use ChatGPT to classify the emotion of a given text.
    """
    emotion_map: dict = config.get("avatars", {})
    try:
        prompt = SYSTEM_PROMPT.replace("{emotions}", ", ".join(emotion_map.keys()))
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        label = response.choices[0].message.content.strip().lower()
        for key in emotion_map.keys():
            if key.lower() in label:
                return key
        logger.warning("Received unexpected label '%s', defaulting to neutral", label)
        return list(emotion_map.keys())[0]
    except Exception as e:
        logger.error("ChatGPT API error: %s", e)
        return list(emotion_map.keys())[0]


def _process_transcript_segment(seg, pydub_audio, config):
    """
    Classify emotion and calculate the volume for the audio segment.
    """
    start, end, text = seg.start, seg.end, seg.text.strip()
    label = _classify_emotion(text, config)
    duration = end - start
    volume = get_subclip_volume_segment(pydub_audio, start, duration)
    logger.info(
        "Segment %f-%fs, Text: '%s', Emotion: %s, Volume: %f",
        start,
        end,
        text,
        label,
        volume,
    )
    return {"start": start, "end": end, "emotion": label, "volume": volume}


def generate_segment(audio_path, audio_clip, config: dict, max_workers=None):
    """
    Generate segments based on audio input.
    Each segment is classified with a dynamic set of emotions via ChatGPT.
    """
    try:
        from faster_whisper import WhisperModel
        from pydub import AudioSegment
    except ImportError as e:
        logger.error("Error importing required libraries: %s", e)
        return [], 0

    emotion_map: dict = config.get("avatars", {})

    logger.info("Load audio (pydub)...")
    pydub_audio = AudioSegment.from_file(audio_path)
    logger.info("Transcribing audio...")
    whisper_model = WhisperModel(WHISPER_MODEL_SIZE)
    result, _ = whisper_model.transcribe(audio_path, multilingual=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_process_transcript_segment, seg, pydub_audio, config)
            for seg in result
        ]
        segments = [f.result() for f in as_completed(futures)]

    volumes = [s["volume"] for s in segments]
    global_avg_volume = np.mean(volumes) if volumes else 0
    logger.info("General average volume: %f", global_avg_volume)

    total_duration = sum(s["end"] - s["start"] for s in segments)
    if total_duration < audio_clip.duration:
        segments.append(
            {
                "start": total_duration,
                "end": audio_clip.duration,
                "emotion": list(emotion_map.keys())[0],
                "volume": global_avg_volume,
            }
        )

    del whisper_model
    return segments, global_avg_volume


def _render_avatar_segment(i, seg, avatar_path, shake_factor, global_avg_volume):
    """
    Load the avatar, apply the loop + shake and write the output file.
    """
    start, end = seg["start"], seg["end"]
    volume = seg["volume"]
    intensity = (
        (volume / global_avg_volume) * shake_factor if global_avg_volume > 0 else 0
    )

    avatar_video = mpe.VideoFileClip(avatar_path).without_audio()
    avatar_segment = avatar_video.loop(duration=end - start)
    avatar_segment = apply_shake(avatar_segment, intensity)

    out_name = f"temp_{i:03d}_{os.path.splitext(os.path.basename(avatar_path))[0]}.mp4"
    logger.info("Rendering segment %d (%s) → %s", i, seg["emotion"], out_name)
    avatar_segment.write_videofile(
        out_name, codec="libx264", audio=False, verbose=False, logger=None
    )
    return out_name


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


def generate_avatar_video(audio_path: str, config: dict, max_workers=None):
    """
    Process audio to generate a video with avatars based on emotions.
    """
    avatars = config.get("avatars", {})
    shake_factor = config.get("shake_factor", 0.1)

    try:
        clip = mpe.VideoFileClip(audio_path)
        audio_clip = clip.audio
    except Exception:
        audio_clip = mpe.AudioFileClip(audio_path)
        clip = None

    segments, global_avg_volume = generate_segment(
        audio_path, audio_clip, config, max_workers
    )

    tasks = []
    for i, seg in enumerate(segments):
        avatar_path = avatars.get(seg["emotion"])
        if not avatar_path:
            logger.warning("No avatar for emotion '%s'. Skipping.", seg["emotion"])
            continue
        tasks.append((i, seg, avatar_path))

    segment_paths = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _render_avatar_segment,
                i,
                seg,
                avatar_path,
                shake_factor,
                global_avg_volume,
            ): (i, avatar_path)
            for i, seg, avatar_path in tasks
        }
        for future in as_completed(futures):
            segment_paths.append(future.result())

    if not segment_paths:
        logger.error("No clips generated. Exiting.")
        return

    final_output = "output_video.mp4"
    concatenate_segments_ffmpeg(segment_paths, final_output, audio_path)
    logger.info("Final video saved on: %s", final_output)
