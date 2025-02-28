import os
import json
import logging
from pathlib import Path

import librosa
import scipy
import whisper
from bark import SAMPLE_RATE, generate_audio, preload_models
from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoFileClip
from pydub import AudioSegment

from utils import get_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def change_audio_speed(audio_file: str, speed: float) -> str:
    base = Path(audio_file).stem
    output_file = f"{base}_edited.wav"
    logger.info("Changing speed to: %s of file: %s", speed, audio_file)
    if speed > 1:
        sound = AudioSegment.from_file(audio_file)
        so = sound.speedup(speed, 150, 25)
        so.export(output_file, format="wav")
    else:
        song, fs = librosa.load(audio_file)
        audio_stretched = librosa.effects.time_stretch(song, rate=speed)
        scipy.io.wavfile.write(output_file, fs, audio_stretched)
    return output_file


def video_translation(video_path: str, translate_data: bool = True):
    video_stem = Path(video_path).stem
    input_video_file_clip = VideoFileClip(video_path)
    audio_path = get_audio(input_video_file_clip, video_stem)
    whisper_model = whisper.load_model("large")
    transcribe_params = {"audio": audio_path, "task": "translate"}
    if not translate_data:
        logger.info("Just transcribing in the same language")
        transcribe_params.pop("task", None)
    results = whisper_model.transcribe(**transcribe_params)
    audio_info = []
    for segment in results.get("segments", []):
        audio_info.append(
            {
                "id": segment["id"],
                "text": segment["text"].strip(),
                "audio_file": "",
                "start": segment["start"],
                "end": segment["end"],
            }
        )
    json_file = f"{video_stem}_audio_info.json"
    with open(json_file, "w", encoding="utf-8") as outfile:
        json.dump(audio_info, outfile, indent=2)
    logger.info("Audio info saved in: %s. Check it before generating audio.", json_file)


def audio_generator(
    video_path: str, voice_info: str = "v2/en_speaker_2", low_profile: bool = True
):
    if low_profile:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["SUNO_USE_SMALL_MODELS"] = "1"
    preload_models()
    video_stem = Path(video_path).stem
    json_file = f"{video_stem}_audio_info.json"
    with open(json_file, "r", encoding="utf-8") as openfile:
        audio_clips = json.load(openfile)
    for segment in audio_clips:
        if segment["audio_file"]:
            continue
        audio_file = f"{video_stem}_generated_audio_{segment['id']}.wav"
        logger.info("Generating audio for: %s in %s", segment["text"], audio_file)
        audio_array = generate_audio(segment["text"], history_prompt=voice_info)
        scipy.io.wavfile.write(audio_file, rate=SAMPLE_RATE, data=audio_array)
        segment["audio_file"] = audio_file
    with open(json_file, "w", encoding="utf-8") as outfile:
        json.dump(audio_clips, outfile, indent=2)
    input_video_file_clip_no_audio = VideoFileClip(video_path).without_audio()
    clips = []
    for item in audio_clips:
        audio = AudioFileClip(item["audio_file"])
        duration = item["end"] - item["start"]
        target_speed = audio.duration / duration
        edited_audio_file = change_audio_speed(item["audio_file"], target_speed)
        audio = AudioFileClip(edited_audio_file).set_start(item["start"])
        clips.append(audio)
    composite_audio = CompositeAudioClip(clips).subclip(
        0, input_video_file_clip_no_audio.duration
    )
    final_video = input_video_file_clip_no_audio.set_audio(composite_audio)
    final_video_name = f"{video_stem}_final_video.mp4"
    final_video.write_videofile(final_video_name, audio_codec="aac")
    logger.info("Final video saved in: %s", final_video_name)
