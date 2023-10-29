import os
import json
import argparse
import scipy
import whisper
import librosa
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
)
from bark import generate_audio, preload_models, SAMPLE_RATE
from pydub import AudioSegment
from toolkit import VideoProcessor as vp


def change_audio_speed(audio_file, speed):
    name = f"{audio_file}_edited.wav"

    print("Changing speed to: ", speed, " of audio file: ", audio_file)
    if speed > 1:
        sound = AudioSegment.from_file(audio_file)
        so = sound.speedup(speed, 150, 25)
        so.export(name)
    else:
        song, fs = librosa.load(audio_file)
        audio_stretched = librosa.effects.time_stretch(y=song, rate=speed)
        scipy.io.wavfile.write(name, fs, audio_stretched)
    return name


def video_translation(video_path_data):
    input_video_file_clip = VideoFileClip(video_path_data)
    audio_path = vp.get_audio(input_video_file_clip, video_path_data[:-4])

    whisper_model = whisper.load_model("large")
    results = whisper_model.transcribe(audio_path, task="translate")

    audio_info = []

    for segment in results["segments"]:
        audio_info.append(
            {
                "id": segment["id"],
                "text": segment["text"].strip(),
                "audio_file": "",
                "start": segment["start"],
                "end": segment["end"],
            }
        )

    json_file = f"{video_path_data[:-4]}_audio_info.json"
    with open(json_file, "w", encoding="utf-8") as outfile:
        json.dump(audio_info, outfile)

    print(
        "Audio info saved to: ",
        json_file,
        " check it before generating audio with audio_generator",
    )


def audio_generator(video_path_data, voice_info="v2/en_speaker_2", low_profile=True):
    if low_profile:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["SUNO_USE_SMALL_MODELS"] = "1"

    preload_models()

    json_file = f"{video_path_data[:-4]}_audio_info.json"
    audio_clips = []
    with open(json_file, "r", encoding="utf-8") as openfile:
        audio_clips = json.load(openfile)

    for segment in audio_clips:
        if segment["audio_file"] != "":
            continue

        audio_file = f"{video_path_data[:-4]}_generated_audio_{segment['id']}.wav"
        print("Writing: ", segment["text"], " to ", audio_file)
        audio_array = generate_audio(segment["text"], history_prompt=voice_info)
        scipy.io.wavfile.write(audio_file, rate=SAMPLE_RATE, data=audio_array)
        segment["audio_file"] = audio_file

    with open(json_file, "w", encoding="utf-8") as outfile:
        json.dump(audio_clips, outfile)

    input_video_file_clip_no_audio = VideoFileClip(video_path_data).without_audio()

    clips = []
    for item in audio_clips:
        audio = AudioFileClip(item["audio_file"])
        duration = item["end"] - item["start"]
        target_speed = audio.duration / duration

        audio_file = change_audio_speed(item["audio_file"], target_speed)

        audio = AudioFileClip(audio_file)
        audio = audio.set_start(item["start"])
        clips.append(audio)

    audio = CompositeAudioClip(clips)
    audio = audio.subclip(0, input_video_file_clip_no_audio.duration)
    input_video_file_clip_no_audio = input_video_file_clip_no_audio.set_audio(audio)

    final_video_name = f"{video_path_data[:-4]}_final_video.mp4"
    input_video_file_clip_no_audio.write_videofile(final_video_name, audio_codec="aac")
    print("Final video saved to: ", final_video_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        type=str,
        help="The operation to be performed, can be video_translation or audio_generator",
    )
    parser.add_argument("video_path", type=str, help="The video file to be translated")
    parser.add_argument(
        "--voice",
        type=str,
        default="v2/en_speaker_2",
        help="The voice to be used in the translation",
    )
    parser.add_argument(
        "--low_profile_mode",
        type=bool,
        default=True,
        help="Use low profile mode for less powerful computers",
    )

    args = parser.parse_args()

    operation = args.operation
    video_path = args.video_path
    voice = args.voice
    low_profile_mode = args.low_profile_mode

    if operation == "video_translation":
        print("Starting video translation...")
        video_translation(video_path)
    elif operation == "audio_generator":
        print("Starting audio generation...")
        audio_generator(video_path, voice, low_profile_mode)
    else:
        print("Invalid operation, use --help for more info")
