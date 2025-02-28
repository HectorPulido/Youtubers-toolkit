from faster_whisper import WhisperModel
from utils import get_audio, float_to_srt_time


MODEL_SIZE = "turbo"


def generate_transcript(**kwargs):
    input_video_file_clip, filename = (
        kwargs["input_video_file_clip"],
        kwargs["filename"],
    )
    audio_file_name = get_audio(input_video_file_clip, filename)
    model = WhisperModel(MODEL_SIZE)
    segments, _ = model.transcribe(audio_file_name, multilingual=True)
    transcript = ""
    for segment in segments:
        start_time = float_to_srt_time(segment.start)
        end_time = float_to_srt_time(segment.end)
        text_data = segment.text.strip()
        transcript += f"{segment.id + 1}\n{start_time} --> {end_time}\n{text_data}\n\n"
    transcript_file_name = f"{filename}_transcript.srt"
    with open(transcript_file_name, "w", encoding="utf-8") as file:
        file.write(transcript)
    kwargs["transcript_file_name"] = transcript_file_name
    return kwargs
