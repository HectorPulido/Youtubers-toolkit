import argparse
from moviepy import editor
from moviepy.editor import VideoFileClip
from toolkit import VideoProcessor as vp

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=str, nargs="+", help="The files to join with audio")

    args = parser.parse_args()

    files = args.files

    for file in files:
        clip_name = file[:-4]
        clip_edited_name = f"{clip_name}_EDITED.mp4"
        input_video_file_clip = VideoFileClip(file)
        input_video_file_clip.audio = editor.AudioFileClip(f"{clip_name}.wav")
        input_video_file_clip.write_videofile(clip_edited_name, audio_codec="aac")