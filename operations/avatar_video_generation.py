"""
Module for video generation with an avatar from audio
"""

import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
import numpy as np

from openai import OpenAI
from faster_whisper import WhisperModel
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip

from utils import apply_shake, get_subclip_volume_segment


CACHE_SUFFIX = "_segments.json"
DEFAULT_FPS = 24  # fallback framerate if clip.fps is missing

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "GPT-4.1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3")  # can be adjusted

# Validate essential environment variables early
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in environment variables.")

# Initialize OpenAI client
_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SegmentData:
    """
    Simple container for a single transcript segment's metadata.
    """

    def __init__(self, start: float, end: float, emotion: str, volume: float):
        self.start = start
        self.end = end
        self.emotion = emotion
        self.volume = volume

    def to_dict(self) -> Dict[str, Any]:
        """
        Transform SegmentData to Dict
        """
        return {
            "start": self.start,
            "end": self.end,
            "emotion": self.emotion,
            "volume": self.volume,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SegmentData":
        """
        Transform dict to SegmentData
        """
        return SegmentData(
            start=data["start"],
            end=data["end"],
            emotion=data["emotion"],
            volume=data["volume"],
        )


def build_emotion_system_prompt(emotion_keys: List[str]) -> str:
    """
    Construct the system prompt for ChatGPT to classify emotions.
    """
    labels = ", ".join(emotion_keys)
    return (
        "You are an emotion classifier. "
        "Given a short phrase in any language, reply with exactly one of the following labels: "
        f"{labels}. "
        "Respond with just the label, no extra text. Try to be expressive."
    )


def classify_emotion(text: str, emotion_map: Dict[str, str]) -> str:
    """
    Use ChatGPT to classify the given text into one of the keys in emotion_map.
    If anything goes wrong or the returned label is unexpected, fallback to the first emotion key.

    Args:
        text (str): The text segment to classify.
        emotion_map (Dict[str, str]): Mapping from emotion label -> avatar path.

    Returns:
        str: One of the keys from emotion_map (lowercased match).
    """
    emotion_keys = list(emotion_map.keys())
    default_emotion = emotion_keys[0]

    prompt = build_emotion_system_prompt(emotion_keys)
    logger.debug("Emotion classification prompt: %s", prompt)
    logger.debug("User text for classification: %s", text)

    try:
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        raw_label = response.choices[0].message.content.strip().lower()
        logger.debug("Raw emotion label from GPT: %s", raw_label)
        # Attempt to match one of the known keys
        for key in emotion_keys:
            if key.lower() in raw_label:
                logger.info("Classified emotion '%s' for text segment.", key)
                return key
        # No direct match: fallback
        logger.warning(
            "Unexpected label '%s'. Falling back to default '%s'.",
            raw_label,
            default_emotion,
        )
        return default_emotion

    except Exception as e:
        logger.error(
            "Error calling ChatGPT for emotion classification: %s. Using default '%s'.",
            e,
            default_emotion,
        )
        return default_emotion


def compute_segment_volume(audio: AudioSegment, start: float, end: float) -> float:
    """
    Compute the average loudness/volume of a subclip using pydub.
    Delegates to get_subclip_volume_segment helper.

    Args:
        audio (AudioSegment): Full audio loaded via pydub.
        start (float): Start time in seconds.
        end (float): End time in seconds.

    Returns:
        float: A volume metric (higher means louder).
    """
    duration = end - start
    try:
        volume_value = get_subclip_volume_segment(audio, start, duration)
        logger.debug(
            "Computed volume %.4f for segment [%.2f, %.2f].", volume_value, start, end
        )
        return volume_value
    except Exception as e:
        logger.error(
            "Error computing volume for segment [%.2f, %.2f]: %s. Defaulting to 0.0.",
            start,
            end,
            e,
        )
        return 0.0


def process_transcript_segment(
    seg: Any, pydub_audio: AudioSegment, emotion_map: Dict[str, str]
) -> SegmentData:
    """
    Given a Whisper transcript segment (with .start, .end, .text),
    classify emotion and measure volume.

    Args:
        seg (Any): A segment object returned by Whisper, expected to have .start, .end, .text.
        pydub_audio (AudioSegment): The full audio loaded so we can measure volume.
        emotion_map (Dict[str, str]): Mapping of emotion label -> avatar file path.

    Returns:
        SegmentData: A container with start, end, chosen emotion, and volume.
    """
    start = seg.start
    end = seg.end
    text = seg.text.strip()

    logger.debug("Processing segment from %.2f to %.2f: '%s'.", start, end, text)

    # Classify the emotion using ChatGPT
    chosen_emotion = classify_emotion(text, emotion_map)

    # Measure volume for this segment
    volume = compute_segment_volume(pydub_audio, start, end)

    logger.info(
        "Segment [%.2f-%.2f] | Text: '%s' | Emotion: '%s' | Volume: %.4f",
        start,
        end,
        text,
        chosen_emotion,
        volume,
    )

    return SegmentData(start=start, end=end, emotion=chosen_emotion, volume=volume)


def get_cache_path(audio_path: Path) -> Path:
    """
    Given an audio file path, return the corresponding JSON cache path.
    """
    return audio_path.with_name(audio_path.stem + CACHE_SUFFIX)


def load_cached_segments(cache_path: Path) -> Optional[Tuple[List[SegmentData], float]]:
    """
    If the cache JSON exists, load and return the segments list and global average volume.

    Returns:
        Tuple[List[SegmentData], float] or None if cache is missing or invalid.
    """
    if not cache_path.exists():
        logger.info("No cache file found at '%s'. Will generate segments.", cache_path)
        return None

    try:
        with cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        raw_segments = data.get("segments", [])
        avg_volume = float(data.get("global_avg_volume", 0.0))
        segments = [SegmentData.from_dict(item) for item in raw_segments]
        logger.info(
            "Loaded %d segments and global_avg_volume=%.4f from cache.",
            len(segments),
            avg_volume,
        )
        return segments, avg_volume
    except Exception as e:
        logger.error(
            "Failed to load cache from '%s': %s. Ignoring cache.", cache_path, e
        )
        return None


def save_cached_segments(
    cache_path: Path, segments: List[SegmentData], global_avg_volume: float
) -> None:
    """
    Save the list of segments (converted to dicts) and global_avg_volume to the JSON cache.

    Args:
        cache_path (Path): Where to write the cache file.
        segments (List[SegmentData]): The computed segments data.
        global_avg_volume (float): The average volume across segments.
    """
    try:
        cache_data = {
            "segments": [seg.to_dict() for seg in segments],
            "global_avg_volume": global_avg_volume,
        }
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info("Saved segments to cache at '%s'.", cache_path)
    except Exception as e:
        logger.error("Failed to save cache to '%s': %s", cache_path, e)


def transcribe_audio_whisper(audio_path: Path, model_size: str) -> List[Any]:
    """
    Use faster_whisper.WhisperModel to transcribe the audio file into a list of segments.

    Args:
        audio_path (Path): Path to the audio or video file.
        model_size (str): Model size for Whisper (e.g. "tiny", "base", "small", etc.).

    Returns:
        List[Any]: A list of transcript segment objects (each having .start, .end, .text).
    """
    logger.info("Loading Whisper model (size='%s') for transcription...", model_size)
    whisper_model = WhisperModel(model_size, num_workers=4, compute_type="int8")
    try:
        result, _ = whisper_model.transcribe(str(audio_path), multilingual=True)
        logger.info("Transcription complete. Obtained segments.")
        return result
    finally:
        # Ensure we free WhisperModel resources immediately
        del whisper_model


def classify_and_measure_all(
    transcript_segments: List[Any],
    pydub_audio: AudioSegment,
    emotion_map: Dict[str, str],
    max_workers: Optional[int] = None,
) -> List[SegmentData]:
    """
    In parallel, classify emotion and measure volume for each Whisper transcript segment.

    Args:
        transcript_segments (List[Any]): List of Whisper transcript objects.
        pydub_audio (AudioSegment): Full audio for volume computation.
        emotion_map (Dict[str, str]): Mapping from emotion key -> avatar path.
        max_workers (Optional[int]): Number of threads for parallel execution.

    Returns:
        List[SegmentData]: Ordered list of computed SegmentData.
    """
    logger.info("Starting parallel processing transcript segments...")
    segments: List[SegmentData] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_transcript_segment, seg, pydub_audio, emotion_map
            ): seg
            for seg in transcript_segments
        }
        for future in as_completed(futures):
            try:
                seg_data = future.result()
                segments.append(seg_data)
            except Exception as e:
                # If one segment fails, log the error but continue
                seg_obj = futures[future]
                logger.error(
                    "Segment [%.2f-%.2f] processing failed: %s",
                    seg_obj.start,
                    seg_obj.end,
                    e,
                )

    # Sort by start time, just in case
    segments.sort(key=lambda s: s.start)
    logger.info("Completed classification & volume measurement for all segments.")
    return segments


def append_tail_segment_if_needed(
    segments: List[SegmentData],
    total_duration: float,
    default_emotion: str,
    global_avg_volume: float,
) -> List[SegmentData]:
    """
    If there is a gap at the end of the audio not covered by any segment,
    append a "tail" segment from the last segment end to total_duration,
    using default_emotion and the global average volume.

    Args:
        segments (List[SegmentData]): Current list of processed segments (sorted).
        total_duration (float): Total length of the audio in seconds.
        default_emotion (str): The fallback emotion key.
        global_avg_volume (float): Average volume across all existing segments.

    Returns:
        List[SegmentData]: The new list with an extra tail segment if needed.
    """
    if not segments:
        # No segments at all: create a single segment from 0 to total_duration
        logger.warning(
            "No transcript segments found. Generating single tail segment "
            "from 0 to %.2f with emotion '%s'.",
            total_duration,
            default_emotion,
        )
        return [
            SegmentData(
                start=0.0,
                end=total_duration,
                emotion=default_emotion,
                volume=global_avg_volume,
            )
        ]

    last_end = segments[-1].end
    if last_end < total_duration:
        logger.info(
            "Audio extends from %.2f to %.2f beyond last segment end. "
            "Adding tail segment with default emotion '%s'.",
            last_end,
            total_duration,
            default_emotion,
        )
        tail_segment = SegmentData(
            start=last_end,
            end=total_duration,
            emotion=default_emotion,
            volume=global_avg_volume,
        )
        return segments + [tail_segment]

    logger.debug("No tail segment needed; segments already cover full audio.")
    return segments


def generate_segment_data(
    audio_path: Path,
    emotion_map: Dict[str, str],
    max_workers: Optional[int] = None,
) -> Tuple[List[SegmentData], float]:
    """
    Main orchestration function: generate (or load from cache) the list of SegmentData
    dictionaries, each containing start, end, emotion, and volume.
    Also return the global average volume.

    Steps:
      1. Check if cache exists. If so, load and return cached data.
      2. Otherwise:
         a. Load audio via pydub for volume measurement.
         b. Transcribe via WhisperModel.
         c. In parallel, process each segment to classify emotion and measure volume.
         d. Compute global average volume.
         e. Append a tail segment if total segment durations < full audio duration.
         f. Save everything to cache JSON and return.

    Args:
        audio_path (Path): Path to the audio file (or video file with audio).
        emotion_map (Dict[str, str]): Mapping from emotion key -> avatar path.
        max_workers (Optional[int]): Number of parallel threads.

    Returns:
        Tuple[List[SegmentData], float]: (List of SegmentData, global average volume).
    """
    cache_path = get_cache_path(audio_path)
    cached = load_cached_segments(cache_path)
    if cached:
        return cached  # (segments, global_avg_volume)

    # 2.a. Load full audio via pydub for volume measurement
    logger.info("Loading full audio via pydub from '%s'...", audio_path)
    try:
        pydub_audio = AudioSegment.from_file(str(audio_path))
    except Exception as e:
        logger.error(
            "Failed to load audio with pydub: %s. Aborting segment generation.", e
        )
        return [], 0.0

    # 2.b. Transcribe via Whisper
    transcript_segments = transcribe_audio_whisper(audio_path, WHISPER_MODEL_SIZE)

    # 2.c. Parallel classification + volume
    segments = classify_and_measure_all(
        transcript_segments, pydub_audio, emotion_map, max_workers
    )

    # 2.d. Compute global average volume
    volumes = [seg.volume for seg in segments]
    global_avg_volume = float(np.mean(volumes)) if volumes else 0.0
    logger.info("Global average volume computed: %.4f", global_avg_volume)

    # 2.e. If the transcription times do not cover the entire audio, append a tail
    # First we need total audio duration; we can get it from pydub_audio.duration_seconds
    total_duration = pydub_audio.duration_seconds
    default_emotion = list(emotion_map.keys())[0]
    segments = append_tail_segment_if_needed(
        segments, total_duration, default_emotion, global_avg_volume
    )

    # 2.f. Save to cache
    save_cached_segments(cache_path, segments, global_avg_volume)

    return segments, global_avg_volume


def load_avatar_clips(avatar_map: Dict[str, str]) -> Dict[str, VideoFileClip]:
    """
    Given a mapping from emotion key -> avatar file path, load each avatar as a
    VideoFileClip (without audio).
    If a path does not exist, log a warning and skip that key.

    Args:
        avatar_map (Dict[str, str]): Mapping of emotion key -> avatar file path.

    Returns:
        Dict[str, VideoFileClip]: Only keys whose path existed and loaded successfully.
    """
    loaded_clips: Dict[str, VideoFileClip] = {}
    for emotion, path_str in avatar_map.items():
        path_obj = Path(path_str)
        if not path_obj.exists():
            logger.warning(
                "Avatar file for emotion '%s' not found at '%s'. Skipping.",
                emotion,
                path_str,
            )
            continue
        try:
            clip = VideoFileClip(str(path_obj)).without_audio()
            loaded_clips[emotion] = clip
            logger.info(
                "Preloaded avatar clip for emotion '%s' from '%s'.", emotion, path_str
            )
        except Exception as e:
            logger.error(
                "Failed to load avatar '%s' at '%s': %s. Skipping.",
                emotion,
                path_str,
                e,
            )
    return loaded_clips


def build_avatar_subclips(
    segments: List[SegmentData],
    default_clip: VideoFileClip,
    preloaded_clips: Dict[str, VideoFileClip],
    global_avg_volume: float,
    shake_factor: float,
) -> List[VideoFileClip]:
    """
    For each segment, create a looped (and shaken) avatar subclip at the correct timestamp.
    Also fill any gaps with the default avatar loop.

    Args:
        segments (List[SegmentData]): Sorted list of segment data.
        default_clip (VideoFileClip): The fallback avatar clip (first emotion).
        preloaded_clips (Dict[str, VideoFileClip]): Mapping of emotion key -> VideoFileClip.
        global_avg_volume (float): Average volume across all segments.
        shake_factor (float): Factor controlling shake intensity relative to volume.

    Returns:
        List[VideoFileClip]: All prepared subclips positioned in time.
    """
    subclips: List[VideoFileClip] = []
    prev_end = 0.0

    # Precompute default_fps and store it
    default_fps = getattr(default_clip, "fps", DEFAULT_FPS) or DEFAULT_FPS

    for seg in segments:
        start, end, emotion, volume = seg.start, seg.end, seg.emotion, seg.volume
        duration = end - start

        # 1) If there is a gap between prev_end and this segment's start, fill with default avatar
        if start > prev_end:
            gap_duration = start - prev_end
            logger.debug(
                "Filling gap [%.2f-%.2f] with default avatar clip.", prev_end, start
            )
            looped_default = (
                default_clip.loop(duration=gap_duration)
                .set_duration(gap_duration)
                .set_fps(default_fps)
                .set_start(prev_end)
            )
            subclips.append(looped_default)

        # 2) For this segment, pick the correct avatar (or fallback to default if missing)
        if emotion not in preloaded_clips:
            logger.warning(
                "No preloaded avatar for emotion '%s'. Using default instead.", emotion
            )
            base_clip = default_clip
        else:
            base_clip = preloaded_clips[emotion]

        # Precompute fps for this base clip
        base_fps = getattr(base_clip, "fps", DEFAULT_FPS) or DEFAULT_FPS

        # Loop the avatar clip to exactly match segment duration
        avatar_loop = (
            base_clip.loop(duration=duration).set_duration(duration).set_fps(base_fps)
        )

        # Compute shake intensity (0 if global_avg_volume is zero)
        if global_avg_volume > 0:
            intensity = (volume / global_avg_volume) * shake_factor
        else:
            intensity = 0.0

        logger.debug(
            "Applying shake to emotion '%s' clip. Volume=%.4f, GlobalAvg=%.4f, ShakeIntensity=%.4f",
            emotion,
            volume,
            global_avg_volume,
            intensity,
        )
        shaken_clip = (
            apply_shake(avatar_loop, intensity)
            .set_duration(duration)
            .set_fps(base_fps)
            .set_start(start)
        )

        subclips.append(shaken_clip)
        prev_end = end

    # 3) After all segments, if there's leftover audio, fill with default avatar
    total_audio_duration = segments[-1].end if segments else 0.0
    if segments and total_audio_duration < default_clip.duration:
        # If default_clip.duration is actually longer than needed, skip.
        # We need real full audio duration
        pass  # We'll set final composition duration from the audio track itself
    # Instead, let main function add a final default clip by checking audio duration there

    return subclips


def create_avatar_video_from_audio(
    audio_path_str: str,
    config: Dict[str, Any],
    max_workers: Optional[int] = None,
) -> None:
    """
    High-level function to generate the avatar video:
      1. Load audio (video or audio file).
      2. Generate or load segment data (transcription, emotion, volume).
      3. Preload avatar clips.
      4. Build a list of timed subclips (avatar loops and default gaps).
      5. Composite all subclips and attach the original audio.
      6. Export the final video as 'output_video.mp4'.

    Args:
        audio_path_str (str): Path to the input audio or video file.
        config (Dict[str, Any]): A configuration dictionary that must contain:
            - 'avatars': Dict[str, str] mapping emotion keys -> avatar file paths.
            - 'shake_factor': float representing maximum shake intensity scale.
        max_workers (Optional[int]): Number of threads to use for segment processing.
    """
    audio_path = Path(audio_path_str)
    logger.info("Starting avatar video generation for '%s'.", audio_path)

    # 1. Load the audio clip (attempt VideoFileClip first, else AudioFileClip)
    try:
        video_reader = VideoFileClip(str(audio_path))
        audio_clip = video_reader.audio
        logger.info(
            "Extracted audio from video '%s'. Duration=%.2f sec.",
            audio_path,
            audio_clip.duration,
        )
    except Exception:
        logger.info("Input is not a video or failed to extract. Loading as pure audio.")
        try:
            audio_clip = AudioFileClip(str(audio_path))
            logger.info(
                "Loaded audio-only file '%s'. Duration=%.2f sec.",
                audio_path,
                audio_clip.duration,
            )
        except Exception as e:
            logger.error("Failed to load '%s' as audio: %s. Aborting.", audio_path, e)
            return

    total_duration = audio_clip.duration

    # 2. Build segments (load from cache or generate new)
    emotion_map: Dict[str, str] = config.get("avatars", {})
    if not emotion_map:
        logger.error("No 'avatars' mapping provided in config. Cannot proceed.")
        return

    segments, global_avg_volume = generate_segment_data(
        audio_path, emotion_map, max_workers
    )
    if not segments:
        logger.error("No segments generated. Aborting video creation.")
        return

    # 3. Preload avatar clips
    preloaded_clips = load_avatar_clips(emotion_map)
    default_emotion = list(emotion_map.keys())[0]
    if default_emotion not in preloaded_clips:
        logger.error(
            "Default emotion '%s' avatar not preloaded. Aborting video creation.",
            default_emotion,
        )
        return

    default_clip = preloaded_clips[default_emotion]
    shake_factor = config.get("shake_factor", 0.1)

    # 4. Build all subclips
    logger.info("Building avatar subclips for %d segments...")
    subclips = build_avatar_subclips(
        segments, default_clip, preloaded_clips, global_avg_volume, shake_factor
    )

    # 4.a. Check if final tail clip needed (if last segment end < total_duration)
    last_end_time = segments[-1].end
    if last_end_time < total_duration:
        gap = total_duration - last_end_time
        default_fps = getattr(default_clip, "fps", DEFAULT_FPS) or DEFAULT_FPS
        logger.info(
            "Adding final default avatar loop to cover gap [%.2f-%.2f].",
            last_end_time,
            total_duration,
        )
        final_tail = (
            default_clip.loop(duration=gap)
            .set_duration(gap)
            .set_fps(default_fps)
            .set_start(last_end_time)
        )
        subclips.append(final_tail)

    # 5. Composite all subclips into one video, sized as the default clip
    width, height = default_clip.w, default_clip.h
    logger.info(
        "Compositing %d subclips into final video of size (%d x %d).",
        len(subclips),
        width,
        height,
    )
    final_video = CompositeVideoClip(subclips, size=(width, height))
    final_video = final_video.set_audio(audio_clip).set_duration(total_duration)

    # 6. Export the final video
    output_path = Path("output_video.mp4")
    try:
        logger.info("Writing final video to '%s'...", output_path)
        final_video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=DEFAULT_FPS,
            preset="medium",
            verbose=False,
            logger=None,
        )
        logger.info("Successfully saved avatar video as '%s'.", output_path)
    except Exception as e:
        logger.error("Failed to write final video '%s': %s", output_path, e)
    finally:
        # 7. Release resources: close all loaded clips
        logger.info("Releasing resources for avatar clips and final video.")
        for clip in preloaded_clips.values():
            try:
                clip.close()
            except Exception as e:
                logger.warning("Error closing avatar clip: %s", e)
        try:
            final_video.close()
        except Exception:
            pass
        try:
            audio_clip.close()
        except Exception:
            pass
        if "video_reader" in locals():
            try:
                video_reader.close()
            except Exception:
                pass
