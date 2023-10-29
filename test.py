from pydub import AudioSegment
from pydub import effects

root = r"vid_1_generated_audio_0.wav"
velocidad_X = 0.5  # No puede estar por debajo de 1.0

sound = AudioSegment.from_file(root)
so = sound.speedup(velocidad_X, 150, 25)
so.export("test3.wav")

breakpoint()

# import scipy
# import librosa
# from moviepy.editor import (
#     AudioFileClip,
# )


# import soundfile as s
# import pyrubberband as pyrb
# import soundfile as sf

# data, samplerate = sf.read("vid_1_generated_audio_0.wav")

# # Play back at 1.5X speed
# y_stretch = pyrb.time_stretch(data, samplerate, 1.5)
# # Play back two 1.5x tones
# y_shift = pyrb.pitch_shift(data, samplerate, 1.5)
# sf.write("test_2.wav", y_stretch, samplerate, format='wav')


# audio = AudioFileClip("vid_1_generated_audio_0.wav")

# song, fs = librosa.load("vid_1_generated_audio_0.wav")

# audio_stretched = librosa.effects.time_stretch(
#             y=song, rate=1.5
#         )

# scipy.io.wavfile.write(f"test.wav", fs, audio_stretched)
