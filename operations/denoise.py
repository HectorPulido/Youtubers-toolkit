"""
Module to denoise audio in a video file using the DNS64 model.
"""

from moviepy import editor
from utils import get_audio


def denoise_video(**kwargs):
    """
    Denoise the audio of a video file using the DNS64 model.
    """
    try:
        import torch
        import torchaudio
        from denoiser import pretrained
        from denoiser.dsp import convert_audio
    except ImportError as e:
        raise ImportError(
            "Please install the required libraries: torch, torchaudio, denoiser"
        ) from e

    input_video_file_clip, filename = (
        kwargs["input_video_file_clip"],
        kwargs["filename"],
    )
    audio_file_name = get_audio(input_video_file_clip, filename)
    if not audio_file_name:
        return kwargs
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = pretrained.dns64().to(device)
    wav, source = torchaudio.load(audio_file_name)
    wav = convert_audio(wav.to(device), source, model.sample_rate, model.chin)
    with torch.no_grad():
        denoised = model(wav[None])[0]
    denoised_file_name = f"{filename}_denoised.wav"
    torchaudio.save(denoised_file_name, denoised.cpu(), model.sample_rate)
    input_video_file_clip.audio = editor.AudioFileClip(denoised_file_name)
    kwargs["input_video_file_clip"] = input_video_file_clip
    return kwargs
