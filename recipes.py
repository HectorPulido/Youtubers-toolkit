#!/usr/bin/env python3
"""
This script provides a command line interface for various video processing tasks.
"""
import subprocess
import sys
import os


def transcribe_video(video: str):
    """
    Transcribes the video using the 'video_transcription' pipeline.
    Command:
    python main.py video_edit {video} --pipeline transcript
    """

    command = f"python main.py video_edit {video} --pipeline transcript"
    subprocess.run(command, shell=True, check=True)


def separate_video(video: str):
    """
    Separates the video using the 'trim_by_silence' pipeline.
    Command:
    python main.py video_edit {video} --pipeline \
        trim_by_silence save_separated_video -c 0.25 -s 0.01 -d True
    """
    command = f"python main.py video_edit {video} --pipeline \
        trim_by_silence save_separated_video -c 0.25 -s 0.01 -d True"
    subprocess.run(command, shell=True, check=True)


def generate_avatar(video: str):
    """
    Generates the video avatar.
    Command:
    python main.py avatar_video_generation {video} avatar_config/config.json
    """
    command = (
        f"python main.py avatar_video_generation {video} avatar_config/config.json"
    )
    subprocess.run(command, shell=True, check=True)


def subtitle_video(video: str):
    """
    Generate subtitles and add them to the video
    """
    try:
        command = f"python main.py video_edit {video} --pipeline transcript_divided"
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        return

    command = f"python main.py video_edit {video} --pipeline subtitles save_join"
    subprocess.run(command, shell=True, check=True)


def generate_short_base(video: str):
    """
    Generates a short base from the video by chaining several commands:
    1. Divides the transcript:
       python main.py video_edit {video} --pipeline transcript_divided
    2. Renames the subtitle file:
       mv {base_name}_transcript.srt output_{base_name}_transcript.srt
    3. Generates the base:
       python main.py generator {video} base
    4. Joins the subtitles:
       python main.py video_edit {video} --pipeline subtitles save_join
    """
    # Get the base name of the video (without extension)
    base_name = os.path.splitext(video)[0]

    try:
        command = (
            f"python main.py video_edit {video} --pipeline transcript_divided &&"
            f"mv {base_name}_transcript.srt output_{base_name}_transcript.srt"
        )
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        command = f"python main.py generator {video} base && \
            python main.py video_edit output_{video} --pipeline save_join"
        subprocess.run(command, shell=True, check=True)
        return
    command = (
        f"python main.py generator {video} base && "
        f"python main.py video_edit output_{video} --pipeline subtitles save_join"
    )
    subprocess.run(command, shell=True, check=True)


def generate_video_ideas(youtube_username: str):
    """
    Generate video ideas from a youtube channel username
    """
    print("Remember to change the videos_to_compare.json")
    command = f"python agents/killer_video_idea.py {youtube_username}"
    subprocess.run(command, shell=True, check=True)


def generate_video_title(video: str):
    """
    Generate video title idea using the transcript
    1. Check if {video}_transcript.srt exists
    2 If exists, just return the response of:
        python agents/killer_video_title_gen.py {video}_transcript.srt
    3 If not
    4. Generate video transcript
    5. Generate titles with python agents/killer_video_title_gen.py {video}_transcript.srt
    """
    print("Remember to change the videos_to_compare.json")

    def killer_video_title(transcript_name):
        command = f"python agents/killer_video_title_gen.py {transcript_name}"
        subprocess.run(command, shell=True, check=True)
        print("Output saved on output.txt")

    base_name = os.path.splitext(video)[0]
    transcript_name = f"{base_name}_transcript.srt"

    if os.path.isfile(transcript_name):
        killer_video_title(transcript_name)
        return

    transcribe_video(video)
    killer_video_title(transcript_name)


def main():
    """
    Main function to handle command line arguments and execute the appropriate function.
    """
    if len(sys.argv) < 3:
        print("Usage: python recipes.py <command> <video>")
        print(
            "Available commands: "
            "separate_video, generate_avatar, generate_short_base, "
            "transcribe_video, subtitle_video, generate_video_ideas,"
            "generate_video_title"
        )
        sys.exit(1)

    command = sys.argv[1]
    video = sys.argv[2]

    if command == "separate_video":
        separate_video(video)
    elif command == "generate_avatar":
        generate_avatar(video)
    elif command == "generate_short_base":
        generate_short_base(video)
    elif command == "transcribe_video":
        transcribe_video(video)
    elif command == "subtitle_video":
        subtitle_video(video)
    elif command == "generate_video_ideas":
        username = video
        generate_video_ideas(username)
    elif command == "generate_video_title":
        generate_video_title(video)
    else:
        print("Command not recognized.")
        sys.exit(1)


if __name__ == "__main__":
    main()
