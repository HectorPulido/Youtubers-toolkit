import argparse
from config import config_data
from utils import str2bool
from toolkit import VideoProcessor


functions_dict = {
    "trim_by_silence": VideoProcessor.trim_by_silence,
    "denoise": VideoProcessor.denoise_video,
    "transcript": VideoProcessor.generate_transcript,
    "subtitles": VideoProcessor.add_subtitles,
    "save_separated_video": VideoProcessor.save_separated_video,
    "save_join": VideoProcessor.save_joined_video,
    "save_video": VideoProcessor.save_video,
    "set_vertical": VideoProcessor.set_vertical,
    "set_horizontal": VideoProcessor.set_horizontal,
}


parser = argparse.ArgumentParser(description="Multiples tools for video editing")
parser.add_argument(
    "input_file", type=str, nargs="+", help="The video file you want modified"
)

parser.add_argument(
    "--pipeline",
    type=str,
    nargs="+",
    help=f"Functions to be applied to the video, {', '.join(functions_dict.keys())}",
)

parser.add_argument(
    "-c", "--clip_interval", type=float, default=2, help="The precision of the trimming"
)
parser.add_argument(
    "-s",
    "--sound_threshold",
    type=float,
    default=0.01,
    help="Maximun amout of volume to be considerer as silence",
)
parser.add_argument(
    "-d",
    "--discard_silence",
    const=True,
    default=False,
    type=str2bool,
    nargs="?",
    help="Discard silence clips",
)


args = parser.parse_args()

if __name__ == "__main__":
    input_files = args.input_file
    pipeline = args.pipeline
    clip_interval = args.clip_interval
    sound_threshold = args.sound_threshold
    discard_silence = args.discard_silence

    video_processor = VideoProcessor()
    for input_file in input_files:
        kwargs = {
            "video_path": input_file,
            "clip_interval": clip_interval,
            "sound_threshold": sound_threshold,
            "discard_silence": discard_silence,
            "config_data": config_data,
        }

        kwargs = video_processor.get_video_data(**kwargs)

        for step_in_pipeline in pipeline:
            if step_in_pipeline not in functions_dict:
                raise ValueError(
                    f"Function {step_in_pipeline} not found. Available functions: {', '.join(functions_dict.keys())}"
                )

            print(f"Applying {step_in_pipeline} to {input_file}")
            kwargs = functions_dict[step_in_pipeline](**kwargs)
