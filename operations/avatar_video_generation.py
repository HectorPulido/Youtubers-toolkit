import logging
import numpy as np
from pydub import AudioSegment
import moviepy.editor as mpe

from faster_whisper import WhisperModel
from transformers import pipeline

from utils import get_subclip_volume_segment, apply_shake

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


def generate_avatar_video(audio_path: str, config: dict):
    """
    Process audio to video with avatars based on emotions.
    Args:
        audio_path (str): Path to the audio file.
        config (dict): Configuration dictionary containing avatars and shake factor.
    """
    avatars = config.get("avatars", {})
    shake_factor = config.get("shake_factor", 0.1)

    logger.info("Loaing audio (using pydub)...")
    pydub_audio = AudioSegment.from_file(audio_path)

    try:
        logger.info("Loading audio/video for final audio extraction (moviepy)...")
        clip = mpe.VideoFileClip(audio_path)
        audio_clip = clip.audio
    except Exception:
        logger.info("Can not load as video, loading as audio with moviepy...")
        audio_clip = mpe.AudioFileClip(audio_path)
        clip = None

    logger.info("Transcribe audio...")
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

        result = emotion_classifier(text)[0][0]
        emotion = EMOTION.get(result["label"], "avatar_calm")

        volume = get_subclip_volume_segment(pydub_audio, start, duration)
        segments.append(
            {"start": start, "end": end, "emotion": emotion, "volume": volume}
        )
        volumes.append(volume)
        logger.info(
            "Segment: %f-%fs, emotion: %s, volume (RMS): %f",
            start,
            end,
            emotion,
            volume,
        )

    global_avg_volume = np.mean(volumes)
    logger.info("Average global volume: %f", global_avg_volume)

    total_duration = sum(seg["end"] - seg["start"] for seg in segments)
    if total_duration < audio_clip.duration:
        logger.info("Total duration of segments is less than audio duration.")
        segments.append(
            {
                "start": total_duration,
                "end": audio_clip.duration,
                "emotion": "avatar_calm",
                "volume": global_avg_volume,
            }
        )

    avatar_clips = []
    for seg in segments:
        emotion = seg["emotion"]
        volume = seg["volume"]
        intensity = volume / global_avg_volume * shake_factor

        avatar_path = avatars.get(emotion)
        if not avatar_path:
            logger.warning(
                "Could not find avatar for emotion '%s'. Skipping segment.",
            )
            continue

        logger.info(
            "Processing segment with %s and shake intensity %.2f",
        )
        avatar_video = mpe.VideoFileClip(avatar_path).without_audio()
        segment_duration = seg["end"] - seg["start"]
        avatar_segment = avatar_video.loop(duration=segment_duration)
        avatar_segment = apply_shake(avatar_segment, intensity)
        avatar_clips.append(avatar_segment)

    if not avatar_clips:
        logger.error("Clips didn't generate. Exiting.")
        return

    final_video = mpe.concatenate_videoclips(avatar_clips)
    final_video = final_video.set_audio(audio_clip)

    output_filename = "output_video.mp4"
    logger.info("Exporting final video to %s...", output_filename)
    final_video.write_videofile(output_filename, codec="libx264", audio_codec="aac")
