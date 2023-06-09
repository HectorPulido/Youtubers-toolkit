import numpy as np
import moviepy.editor as editor
from moviepy.editor import VideoFileClip


class VideoProcessor:
    def __init__(self, param_dict):
        self.clip_interval = param_dict["clip_interval"]
        self.sound_threshold = param_dict["sound_threshold"]
        self.discard_silence = param_dict["discard_silence"]
        self.join = param_dict["join"]
        self.transcript = param_dict["transcript"]
        self.statistics = param_dict["statistics"]
        self.denoise = param_dict["denoise"]

    # get the volume of an specific clip
    def get_subclip_volume(self, subclip, second, interval):
        cut = subclip.subclip(second, second + interval).audio.to_soundarray(fps=22000)
        return np.sqrt(((1.0 * cut) ** 2).mean())

    def save_joined_video(self, clips, file_name):
        concat_clip = editor.concatenate_videoclips(clips)
        concat_clip.write_videofile(f"{file_name}_EDITED.mp4")

    def save_separated_video(self, clips, file_name):
        for i, clip in enumerate(clips):
            clip.write_videofile(f"{file_name}_EDITED_{i}.mp4")

    def get_audio(self, input_video_file_clip, filename):
        audio_file_name = f"{filename}_audio.wav"

        import os

        if os.path.exists(audio_file_name):
            os.remove(audio_file_name)

        input_video_file_clip.audio.write_audiofile(audio_file_name, codec="pcm_s16le")
        return audio_file_name

    def generate_transcript(self, input_video_file_clip, filename):
        import whisper

        audio_file_name = self.get_audio(input_video_file_clip, filename)

        model = whisper.load_model("base")
        results = model.transcribe(audio_file_name)
        transcript = ""
        for result in results["segments"]:
            transcript += f"{result['id'] + 1}\n{result['start']} --> {result['end']}\n{result['text']}\n"

        transcript_file_name = f"{filename}_transcript.srt"
        with open(transcript_file_name, "w") as file:
            file.write(transcript)

    def denoise_video(self, input_video_file_clip, filename):
        import torch
        import torchaudio
        from denoiser import pretrained
        from denoiser.dsp import convert_audio

        audio_file_name = self.get_audio(input_video_file_clip, filename)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = pretrained.dns64().to(device)
        wav, source = torchaudio.load(audio_file_name)
        wav = convert_audio(wav.to(device), source, model.sample_rate, model.chin)
        with torch.no_grad():
            denoised = model(wav[None])[0]

        denoised_file_name = f"{filename}_denoised.wav"
        torchaudio.save(denoised_file_name, denoised.cpu(), model.sample_rate)

        # replace audio in video
        input_video_file_clip.audio = editor.AudioFileClip(denoised_file_name)
        return input_video_file_clip

    def process_video(self, video_path):
        print(f"Loading video {video_path}...")
        filename = video_path.split("/")[-1].split(".")[0]
        input_video_file_clip = VideoFileClip(video_path)

        # Fix rotation
        shape = input_video_file_clip.get_frame(0).shape
        input_video_file_clip = input_video_file_clip.resize([shape[0], shape[1]])

        if self.denoise:
            print("Denoising audio...")
            input_video_file_clip = self.denoise_video(input_video_file_clip, filename)

        if self.transcript:
            print("Generating transcript...")
            self.generate_transcript(input_video_file_clip, filename)

        print("Chunking video...")
        volumes = []
        for i in np.arange(0, input_video_file_clip.duration, self.clip_interval):
            if input_video_file_clip.duration <= i + self.clip_interval:
                continue
            volumes.append(
                self.get_subclip_volume(input_video_file_clip, i, self.clip_interval)
            )

        print("Processing silences...")
        volumes = np.array(volumes)
        volumes_binary = volumes > self.sound_threshold

        change_times = [0]
        for i in range(1, len(volumes_binary)):
            if volumes_binary[i] == volumes_binary[i - 1]:
                continue
            change_times.append(i * self.clip_interval)
        change_times.append(input_video_file_clip.duration)

        print("Subclipping...")
        first_piece_silence = 1 if volumes_binary[0] else 0
        clips = []
        for i in range(1, len(change_times)):
            if self.discard_silence and i % 2 != first_piece_silence:
                continue
            new = input_video_file_clip.subclip(change_times[i - 1], change_times[i])
            clips.append(new)

        print("Saving...")
        if self.join:
            self.save_joined_video(clips, filename)
        else:
            self.save_separated_video(clips, filename)
