from utils import get_audio, float_to_srt_time


def generate_transcript(**kwargs):
    try:
        import whisper
    except ImportError as e:
        raise ImportError("Please install the required libraries: whisper") from e

    input_video_file_clip, filename = (
        kwargs["input_video_file_clip"],
        kwargs["filename"],
    )
    audio_file_name = get_audio(input_video_file_clip, filename)
    model = whisper.load_model("large")
    results = model.transcribe(audio_file_name)
    transcript = ""
    for segment in results.get("segments", []):
        start_time = float_to_srt_time(segment["start"])
        end_time = float_to_srt_time(segment["end"])
        text_data = segment["text"].strip()
        transcript += (
            f"{segment['id'] + 1}\n{start_time} --> {end_time}\n{text_data}\n\n"
        )
    transcript_file_name = f"{filename}_transcript.srt"
    with open(transcript_file_name, "w", encoding="utf-8") as file:
        file.write(transcript)
    kwargs["transcript_file_name"] = transcript_file_name
    return kwargs
