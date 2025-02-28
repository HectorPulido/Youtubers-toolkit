#!/usr/bin/env python
import argparse
import logging

from moviepy.editor import VideoFileClip
from operations import (
    add_subtitles,
    add_titles,
    audio_generator,
    denoise_video,
    generate_transcript,
    generate_video_base,
    save_joined_video,
    save_separated_video,
    save_video,
    set_horizontal,
    set_vertical,
    split_srt,
    trim_by_silence,
    video_translation,
)
from config_loader import config_data
from utils import get_audio, get_video_data, str2bool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary for functions in the "video_edit" command
functions_dict = {
    "trim_by_silence": trim_by_silence,
    "denoise": denoise_video,
    "transcript": generate_transcript,
    "subtitles": add_subtitles,
    "save_separated_video": save_separated_video,
    "save_join": save_joined_video,
    "save_video": save_video,
    "set_vertical": set_vertical,
    "set_horizontal": set_horizontal,
}


def video_edit_command(args):
    """Executes a sequence of operations for video editing."""
    for input_file in args.input_file:
        kwargs = {
            "video_path": input_file,
            "clip_interval": args.clip_interval,
            "sound_threshold": args.sound_threshold,
            "discard_silence": args.discard_silence,
            "config_data": config_data,
        }
        kwargs = get_video_data(**kwargs)
        for step in args.pipeline:
            if step not in functions_dict:
                raise ValueError(
                    f"Function {step} not found. \
                        Available options: {', '.join(functions_dict.keys())}"
                )
            logger.info("Applying %s to %s", step, input_file)
            kwargs = functions_dict[step](**kwargs)


def separate_audio_command(args):
    """Separates audio from video files."""
    for file in args.files:
        clip = VideoFileClip(file)
        audio_path = get_audio(clip, file[:-4])
        logger.info("Audio saved to: %s", audio_path)


def split_str_command(args):
    """Splits SRT files into parts based on the specified number of words."""
    for file in args.files:
        output_file = f"{file[:-4]}_splitted.srt"
        with open(output_file, "w", encoding="utf-8") as file_data:
            file_data.write(split_srt(file, args.words_per_subtitle))
        logger.info("Split file saved to: %s", output_file)


def voice_command(args):
    """Performs voice operations: video translation or audio generation."""
    if args.operation == "video_translation":
        logger.info("Starting video translation...")
        video_translation(args.video_path, args.translate)
    elif args.operation == "audio_generator":
        logger.info("Starting audio generation...")
        audio_generator(args.video_path, args.voice, args.low_profile_mode)
    else:
        logger.error("Invalid operation. Use --help for more information.")


def generator_command(args):
    """Generates a base video or adds titles to a short video."""
    tools = {
        "base": generate_video_base,
        "add_titles": add_titles,
    }
    for file in args.files:
        if args.tool not in tools:
            logger.error(
                "Tool %s not found, available options: %s",
                args.tool,
                ", ".join(tools.keys()),
            )
            continue
        tools[args.tool](file)


def main():
    parser = argparse.ArgumentParser(
        description="Combined program for video editing and processing"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand for video editing
    parser_edit = subparsers.add_parser(
        "video_edit", help="Multiple tools for video editing"
    )
    parser_edit.add_argument(
        "input_file", type=str, nargs="+", help="Video file(s) to process"
    )
    parser_edit.add_argument(
        "--pipeline",
        type=str,
        nargs="+",
        help=f"Functions to apply to the video: {', '.join(functions_dict.keys())}",
    )
    parser_edit.add_argument(
        "-c", "--clip_interval", type=float, default=2, help="Clipping precision"
    )
    parser_edit.add_argument(
        "-s",
        "--sound_threshold",
        type=float,
        default=0.01,
        help="Maximum volume threshold to consider silence",
    )
    parser_edit.add_argument(
        "-d",
        "--discard_silence",
        const=True,
        default=False,
        type=str2bool,
        nargs="?",
        help="Discard silent clips",
    )
    parser_edit.set_defaults(func=video_edit_command)

    # Subcommand for separate_audio
    parser_separate = subparsers.add_parser(
        "separate_audio", help="Separate audio from video"
    )
    parser_separate.add_argument("files", type=str, nargs="+", help="Video file(s)")
    parser_separate.set_defaults(func=separate_audio_command)

    # Subcommand for split_str
    parser_split = subparsers.add_parser("split_str", help="Split SRT files")
    parser_split.add_argument("files", type=str, nargs="+", help="SRT file(s) to split")
    parser_split.add_argument(
        "words_per_subtitle",
        type=int,
        help="Number of words per subtitle",
    )
    parser_split.set_defaults(func=split_str_command)

    # Subcommand for voice operations
    parser_voice = subparsers.add_parser(
        "voice", help="Voice operations: translation or audio generation"
    )
    parser_voice.add_argument(
        "operation",
        type=str,
        help="Operation to perform: video_translation or audio_generator",
    )
    parser_voice.add_argument(
        "video_path", type=str, help="Path to the video file to process"
    )
    parser_voice.add_argument(
        "-t",
        "--translate",
        const=True,
        default=True,
        type=str2bool,
        nargs="?",
        help="Translate the video to English or transcribe in the same language",
    )
    parser_voice.add_argument(
        "--voice",
        type=str,
        default="v2/en_speaker_2",
        help="Voice to use for translation",
    )
    parser_voice.add_argument(
        "--low_profile_mode",
        type=bool,
        default=True,
        help="Low profile mode for less powerful systems",
    )
    parser_voice.set_defaults(func=voice_command)

    # Subcommand for generator (short video)
    parser_generator = subparsers.add_parser("generator", help="Short video generator")
    parser_generator.add_argument(
        "files", type=str, nargs="+", help="File(s) to process"
    )
    parser_generator.add_argument(
        "tool",
        type=str,
        help="Tool to use: base, add_titles",
    )
    parser_generator.set_defaults(func=generator_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
