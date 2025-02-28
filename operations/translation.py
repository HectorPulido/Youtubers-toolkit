import json
import logging
from pathlib import Path
from faster_whisper import WhisperModel
from kokoro import KPipeline
from transformers import pipeline
import soundfile as sf
from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoFileClip
from pydub import AudioSegment

from utils import get_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_SIZE = "turbo"


def change_audio_speed(audio_file: str, speed: float) -> str:
    base = Path(audio_file).stem
    output_file = f"{base}_edited.wav"
    speed = min(max(speed, 1), 1.4)
    logger.info("Changing speed to: %s of file: %s", speed, audio_file)
    if speed == 1:
        return audio_file

    sound = AudioSegment.from_file(audio_file)
    new_sound = sound.speedup(playback_speed=speed)
    new_sound.export(output_file, format="wav")

    return output_file


def video_translation(
    video_path: str,
    translate_data: str = "Helsinki-NLP/opus-mt-es-en",
    language: str = "en",
):
    translator = None
    if translate_data:
        translator = pipeline("translation", translate_data)

    video_stem = Path(video_path).stem
    input_video_file_clip = VideoFileClip(video_path)
    audio_path = get_audio(input_video_file_clip, video_stem)
    whisper_model = WhisperModel(MODEL_SIZE)
    transcribe_params = {
        "audio": audio_path,
        "language": language,
        "multilingual": True,
    }
    results, _ = whisper_model.transcribe(**transcribe_params)
    audio_info = []
    for segment in results:
        if translator:
            segment.text = translator(segment.text)[0]["translation_text"]

        audio_info.append(
            {
                "id": segment.id,
                "text": segment.text.strip(),
                "audio_file": "",
                "start": segment.start,
                "end": segment.end,
            }
        )
    json_file = f"{video_stem}_audio_info.json"
    with open(json_file, "w", encoding="utf-8") as outfile:
        json.dump(audio_info, outfile, indent=2)
    logger.info("Audio info saved in: %s. Check it before generating audio.", json_file)


def audio_generator(video_path: str, voice_info: str = "en-us/af_heart"):
    lang_code = voice_info.split("/")[0]
    voice = voice_info.split("/")[1]
    vpipeline = KPipeline(lang_code=lang_code)

    video_stem = Path(video_path).stem
    json_file = f"{video_stem}_audio_info.json"
    with open(json_file, "r", encoding="utf-8") as openfile:
        audio_clips = json.load(openfile)
    for segment in audio_clips:
        if segment["audio_file"]:
            continue
        audio_file = f"{video_stem}_generated_audio_{segment['id']}.wav"
        logger.info("Generating audio for: %s in %s", segment["text"], audio_file)
        generator = vpipeline(
            segment["text"].replace("\n", ""),
            voice=voice,
            speed=1,
            split_pattern=r"\n+",
        )
        for _, (__, ___, audio) in enumerate(generator):
            sf.write(audio_file, audio, 24000)
            break
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
