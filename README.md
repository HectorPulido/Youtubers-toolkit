# Youtubers toolkit

This is a toolkit for easy video editing for youtubers, it uses the newest technologies in the field of machine learning to detect silences in a video and cut it in the most efficient way.
Also generate a transcript of the video and a subtitle file.

## How to use 
First you must to install all the dependences with the command 
~~~
pip install -r requirements.txt
~~~
Then you can use the software using the command from the command line

## Arguments
positional arguments:<br>
&nbsp;input_file&nbsp;&nbsp;&nbsp;The video file you want modified<br>

options:<br>
&nbsp;-h, --help&nbsp;&nbsp;&nbsp;show this help message and exit<br>
&nbsp;--pipeline PIPELINE [PIPELINE ...]<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Functions to be applied to the video, trim_by_silence, denoise, transcript,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;subtitles, save_separated_video, save_join, save_video<br>
&nbsp;-c CLIP_INTERVAL, --clip_interval CLIP_INTERVAL<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The precision of the trimming<br>
&nbsp;-s SOUND_THRESHOLD, --sound_threshold SOUND_THRESHOLD<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Maximun amout of volume to be considerer as silence<br>
&nbsp;-d [DISCARD_SILENCE], --discard_silence [DISCARD_SILENCE]<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Discard silence clips<br>

## Example

This will generate a transcript of the video
~~~
python main.py vid_1.mp4 vid_2.mp4 --pipeline transcript
~~~

This code splits an SRT subtitle file into shorter segments, with a predefined number of words per segment, adjusting start and end times evenly. It then generates a new file with the split subtitles.
~~~
python split_srt.py test.srt 5
~~~

This will result in a merge the video with the subtitles
~~~
python main.py vid_1.mp4 --pipeline subtitles save_join
~~~


This will result in a merge of every non-silence part 
~~~
python main.py vid_1.mp4 --pipeline denoise transcript subtitles trim_by_silence save_separated_video -c 1
~~~

This will generate a transcript of the video with the denoiser filter
~~~
python main.py vid_1.mp4 vid_2.mp4 --pipeline denoise transcript
~~~

This will add subtitles to the video and cut the video by silences, all of this with the denoiser filter
~~~
python main.py vid_1.mp4 --pipeline denoise subtitles trim_by_silence save_separated_video -c 1&nbsp;
~~~


<br>

<div align="center">
<h3 align="center">Let's connect 😋</h3>
</div>
<p align="center">
<a href="https://www.linkedin.com/in/hector-pulido-17547369/" target="blank">
<img align="center" width="30px" alt="Hector's LinkedIn" src="https://www.vectorlogo.zone/logos/linkedin/linkedin-icon.svg"/></a> &nbsp; &nbsp;
<a href="https://twitter.com/Hector_Pulido_" target="blank">
<img align="center" width="30px" alt="Hector's Twitter" src="https://www.vectorlogo.zone/logos/twitter/twitter-official.svg"/></a> &nbsp; &nbsp;
<a href="https://www.twitch.tv/hector_pulido_" target="blank">
<img align="center" width="30px" alt="Hector's Twitch" src="https://www.vectorlogo.zone/logos/twitch/twitch-icon.svg"/></a> &nbsp; &nbsp;
<a href="https://www.youtube.com/channel/UCS_iMeH0P0nsIDPvBaJckOw" target="blank">
<img align="center" width="30px" alt="Hector's Youtube" src="https://www.vectorlogo.zone/logos/youtube/youtube-icon.svg"/></a> &nbsp; &nbsp;

</p>
