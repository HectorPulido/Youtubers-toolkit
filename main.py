import time
import argparse
import numpy as np 
import moviepy.editor as editor 
import matplotlib.pyplot as plt
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='Trim the video by silences')
parser.add_argument('input_file', type=str,  help='The video file you want modified')
parser.add_argument('--clip_interval', type=float,  help='The precision of the trimming')
parser.add_argument('--sound_threshold', type=float,  help='Maximun amout of volume to be considerer as silence')
parser.add_argument('-j', '--join', const=True, default=False, type=str2bool, nargs='?',  help='Join all the clips together')
parser.add_argument('-s', '--statistics', const=True, default=False, type=str2bool, nargs='?',  help='Show statistics')
parser.add_argument('-d', '--discard_silence', const=True, default=False, type=str2bool, nargs='?',  help='Discard silence clips')

args = parser.parse_args()

input_file = args.input_file
clip_interval = args.clip_interval
sound_threshold = args.sound_threshold
join = args.join
statistics = args.statistics
discard_silence = args.discard_silence

if clip_interval != None:
    CLIP_INTERVAL = clip_interval
else:
    CLIP_INTERVAL = 2

if sound_threshold != None:
    SOUND_THRESHOLD = sound_threshold
else:
    SOUND_THRESHOLD = 0.01

if join != None:
    JOIN = join
else:
    JOIN = False

if statistics != None:
    STATISTICS = statistics
else:
    STATISTICS = False

if discard_silence != None:
    DISCARD_SILENCE = discard_silence
else:
    DISCARD_SILENCE = False

#get the name of the file
FILENAME = input_file.split("/")[-1].split(".")[0]

#Get the original video
INPUT_FILE = VideoFileClip(input_file)

#get the sound array of an specific segment of the clip
def get_cut(second, interval):
    return INPUT_FILE.subclip(second, second+interval).audio.to_soundarray(fps=22000)

#get the volume of an specific clip
def get_volume(subclip):
    return np.sqrt(((1.0*subclip)**2).mean())

volumes = []

#Get every silence
for i in np.arange(0, INPUT_FILE.duration, CLIP_INTERVAL):
    if(INPUT_FILE.duration > i + CLIP_INTERVAL):
        volumes.append(get_volume(get_cut(i, CLIP_INTERVAL)))

#Get changes of silence
volumes = np.array(volumes)
volumes_binary = volumes > SOUND_THRESHOLD

change_times = [0]
for i in range(1, len(volumes_binary)):
    if(volumes_binary[i] != volumes_binary[i-1]):
        change_times.append(i * CLIP_INTERVAL)
change_times.append(INPUT_FILE.duration)

#Split principal clip
first_piece_silence = 1 if volumes_binary[0] else 0 
clips = []
for i in range(1, len(change_times)):
    if DISCARD_SILENCE and i % 2 != first_piece_silence:
        continue
    new = INPUT_FILE.subclip(change_times[i-1], change_times[i])
    clips.append(new)
    

if JOIN:
    concat_clip = editor.concatenate_videoclips(clips)
    concat_clip.write_videofile(f"{FILENAME}_EDITED.mp4")
else:
    for i, clip in enumerate(clips):
        clip.write_videofile(f"{FILENAME}_cut_{i}.mp4", audio_codec='aac')

if STATISTICS:
    #VOLUME GRAPH
    plt.xlabel('Time')
    plt.ylabel('Volumen')
    x = np.linspace(0,clip.duration,len(volumes))
    sound_threshold_y = [SOUND_THRESHOLD for i in range(len(x))]
    plt.plot(x, volumes, color='b')
    plt.plot(x, sound_threshold_y, color='r')
    plt.show()
