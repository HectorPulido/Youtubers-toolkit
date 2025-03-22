"""
Module for video translation and audio generation.
"""

import os
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
MAX_PAUSE = 1.0


def process_transcript(segments):
    """
    Process the transcript results to group words into phrases based on pauses.
    """

    audio_info = []
    segment_id = 1
    max_pause = 1.0  # Umbral en segundos para determinar el fin de una frase

    # Variables para acumular la frase a lo largo de los segmentos
    current_phrase_words = []
    phrase_start = None
    phrase_end = None
    last_word_end = None

    for segment in segments:
        # Se verifica que el segmento tenga palabras con timestamps
        if not hasattr(segment, "words") or not segment.words:
            continue
        for word in segment.words:
            # Si es la primera palabra global, inicializamos la acumulación
            if phrase_start is None:
                phrase_start = word.start
                phrase_end = word.end
                current_phrase_words.append(word.word.strip())
                last_word_end = word.end
            else:
                # Comprobamos la pausa entre el inicio de la palabra actual y el final de la última palabra
                if (word.start - last_word_end) > max_pause:
                    # Si la pausa es mayor al umbral, se finaliza la frase actual
                    phrase_text = " ".join(current_phrase_words)
                    logger.info(
                        "Phrase: %s | Start: %s | End: %s",
                        phrase_text,
                        phrase_start,
                        phrase_end,
                    )
                    audio_info.append(
                        {
                            "id": segment_id,
                            "original_text": phrase_text,
                            "text": "",
                            "audio_file": "",
                            "start": phrase_start,
                            "end": phrase_end,
                        }
                    )
                    segment_id += 1
                    # Se reinicia la acumulación para la nueva frase
                    current_phrase_words = [word.word.strip()]
                    phrase_start = word.start
                    phrase_end = word.end
                else:
                    # Si la pausa es menor o igual, se continúa acumulando la palabra
                    current_phrase_words.append(word.word.strip())
                    phrase_end = word.end
                last_word_end = word.end

    # Al finalizar, se agrega la última frase acumulada si existe
    if current_phrase_words:
        phrase_text = " ".join(current_phrase_words)
        audio_info.append(
            {
                "id": segment_id,
                "original_text": phrase_text,
                "text": "",
                "audio_file": "",
                "start": phrase_start,
                "end": phrase_end,
            }
        )
        segment_id += 1

    return audio_info


def video_translation(
    video_path: str,
    translate_data: str = "Helsinki-NLP/opus-mt-es-en",
    language: str = "en",
):
    """
    Transcribe and translate the audio from a video file.
    """
    translator = None
    if translate_data:
        translator = pipeline("translation", translate_data)

    video_stem = Path(video_path).stem
    input_video_file_clip = VideoFileClip(video_path)
    audio_path = get_audio(input_video_file_clip, video_stem)
    whisper_model = WhisperModel(MODEL_SIZE, num_workers=4, compute_type="int8")
    transcribe_params = {
        "audio": audio_path,
        "language": language,
        "multilingual": True,
        "temperature": 0.2,
        "word_timestamps": True,
    }
    results, _ = whisper_model.transcribe(**transcribe_params)
    audio_info = process_transcript(results)

    if translator:
        for segment in audio_info:
            segment["text"] = translator(segment["original_text"])[0][
                "translation_text"
            ]
            logger.info(
                "Translating: %s | %s",
                segment["original_text"].strip(),
                segment["text"].strip(),
            )

    else:
        for segment in audio_info:
            segment["text"] = segment["original_text"]

    json_file = f"{video_stem}_audio_info.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(audio_info, f, ensure_ascii=False, indent=4)
    logger.info("Audio info saved in: %s. Check it before generating audio.", json_file)


def change_audio_speed(audio_file: str, speed: float) -> str:
    """
    Change the speed of an audio file and save it as a new file.
    """
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


def audio_generator(video_path: str, voice_info: str = "en-us/af_heart"):
    """
    Generate audio for a video using the specified voice.
    """
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
        if not segment["text"]:
            logger.info("Skipping empty text segment.")
            continue
        audio_file = f"{video_stem}_generated_audio_{segment['id']}.wav"
        logger.info("Generating audio for: %s in %s", segment["text"], audio_file)

        speed = len(segment["text"]) / len(segment["original_text"])

        generator = vpipeline(
            segment["text"].replace("\n", ""),
            voice=voice,
            speed=speed,
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
    # Aseguramos que el clip mantenga el tamaño original
    final_video = final_video.resize(input_video_file_clip_no_audio.size)
    final_video_name = f"{video_stem}_final_video.mp4"
    final_video.write_videofile(
        final_video_name,
        codec="libx264",  # Especificamos el codec de video
        audio_codec="aac",
        ffmpeg_params=["-vf", "scale=iw:ih"],
    )
    logger.info("Final video saved in: %s", final_video_name)

    # Eliminamos los archivos de audio generados
    for item in audio_clips:
        try:
            os.remove(item["audio_file"])
            os.remove(item["audio_file"].replace(".wav", "_edited.wav"))
        except Exception as e:
            logger.error("Error removing file: %s", e)
