#!/usr/bin/env python3
"""
This script provides a command line interface for various video processing tasks.
"""
import subprocess
import sys
import os


def separate_video(video):
    """
    Separates the video using the 'trim_by_silence' pipeline.
    Command:
    python main.py video_edit {video} --pipeline \
        trim_by_silence save_separated_video -c 0.25 -s 0.01 -d False
    """
    command = f"python main.py video_edit {video} --pipeline \
        trim_by_silence save_separated_video -c 0.25 -s 0.01 -d False"
    subprocess.run(command, shell=True, check=True)


def generate_avatar(video):
    """
    Generates the video avatar.
    Command:
    python main.py avatar_video_generation {video} config/config.json
    """
    command = f"python main.py avatar_video_generation {video} config/config.json"
    subprocess.run(command, shell=True, check=True)


def generate_short_base(video):
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

    command = (
        f"python main.py video_edit {video} --pipeline transcript_divided && "
        f"mv {base_name}_transcript.srt output_{base_name}_transcript.srt && "
        f"python main.py generator {video} base && "
        f"python main.py video_edit {video} --pipeline subtitles save_join"
    )
    subprocess.run(command, shell=True, check=True)


def main():
    """
    Main function to handle command line arguments and execute the appropriate function.
    """
    if len(sys.argv) < 3:
        print("Usage: python recipes.py <command> <video>")
        print(
            "Available commands: separate_video, generate_avatar, generate_short_base"
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
    else:
        print("Command not recognized.")
        sys.exit(1)


if __name__ == "__main__":
    main()
