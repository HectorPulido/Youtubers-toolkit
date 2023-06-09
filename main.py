import argparse
from toolkit import VideoProcessor
from utils import str2bool


parser = argparse.ArgumentParser(description="Trim the video by silences")
parser.add_argument(
    "input_file", type=str, nargs="+", help="The video file you want modified"
)
parser.add_argument("--clip_interval", type=float, help="The precision of the trimming")
parser.add_argument(
    "--sound_threshold",
    type=float,
    help="Maximun amout of volume to be considerer as silence",
)
parser.add_argument(
    "-j",
    "--join",
    const=True,
    default=False,
    type=str2bool,
    nargs="?",
    help="Join all the clips together",
)
parser.add_argument(
    "-t",
    "--transcript",
    const=True,
    default=False,
    type=str2bool,
    nargs="?",
    help="Transcript the video",
)
parser.add_argument(
    "-s",
    "--statistics",
    const=True,
    default=False,
    type=str2bool,
    nargs="?",
    help="Show statistics",
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
parser.add_argument(
    "-n",
    "--denoise",
    const=True,
    default=False,
    type=str2bool,
    nargs="?",
    help="Remove background noise from the video",
)

args = parser.parse_args()

if __name__ == "__main__":
    param_dict_base = {
        "input_file": {"value": args.input_file, "default": None},
        "clip_interval": {"value": args.clip_interval, "default": 2},
        "sound_threshold": {"value": args.sound_threshold, "default": 0.01},
        "join": {"value": args.join, "default": False},
        "transcript": {"value": args.transcript, "default": False},
        "statistics": {"value": args.statistics, "default": False},
        "discard_silence": {"value": args.discard_silence, "default": False},
        "denoise": {"value": args.denoise, "default": False},
    }

    param_dict = {}

    for key, value in param_dict_base.items():
        if value["value"] is not None:
            param_dict[key] = value["value"]
        else:
            param_dict[key] = value["default"]

    input_files = param_dict["input_file"]

    video_processor = VideoProcessor(param_dict)

    for input_file in input_files:
        video_processor.process_video(input_file)

# TODO
#     if STATISTICS:
#         # VOLUME GRAPH
#         plt.figure(file_id)
#         plt.xlabel("Time")
#         plt.ylabel("Volumen")
#         x = np.linspace(0, clip.duration, len(volumes))
#         sound_threshold_y = [SOUND_THRESHOLD for i in range(len(x))]
#         plt.plot(x, volumes, color="b")
#         plt.plot(x, sound_threshold_y, color="r")

# if STATISTICS:
#     plt.show()
