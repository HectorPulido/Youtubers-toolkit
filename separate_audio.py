import argparse
from moviepy.editor import VideoFileClip
from toolkit import VideoProcessor as vp

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=str, nargs="+", help="The files to separate")

    args = parser.parse_args()

    files = args.files

    for file in files:
        input_video_file_clip = VideoFileClip(file)
        audio_path = vp.get_audio(input_video_file_clip, file[:-4])
