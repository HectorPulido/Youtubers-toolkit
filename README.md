# Youtubers toolkit

This Tool allows you to cut a video easily by silences with an intuitive command line interface.

## How to use 
First you must to install all the dependences with the command ">pip install -r requirements.txt" <br>
Then you can use the software using the command from the command line

## Arguments
positional arguments: <br>
&nbsp;&nbsp;&nbsp;&nbsp;input_file&nbsp;&nbsp;&nbsp;The video file you want modified <b> can be more than one </b><br><br>

optional arguments:<br>
&nbsp;&nbsp;&nbsp;&nbsp;-h,&nbsp;--help            show this help message and exit<br>
&nbsp;&nbsp;&nbsp;&nbsp;--clip_interval CLIP_INTERVAL The precision of the trimming<br>
&nbsp;&nbsp;&nbsp;&nbsp;--sound_threshold SOUND_THRESHOLD Maximun amout of volume to be considerer as silence <br>
&nbsp;&nbsp;&nbsp;&nbsp;-j [JOIN], --join [JOIN] Join all the clips together <br>
&nbsp;&nbsp;&nbsp;&nbsp;-s [STATISTICS], --statistics [STATISTICS] Show statistics of the volumen <br>
&nbsp;&nbsp;&nbsp;&nbsp;-d [DISCARD_SILENCE], --discard_silence [DISCARD_SILENCE] Discard silence clips <br>

## Example
"python main.py vid_1.mp4 vid_2.mp4 -d -j" <b>This will result in a merge of every non-silence part </b>
