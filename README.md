# Youtubers toolkit

This Tool allows you to cut a video easily by silences with an intuitive command line interface.
It uses the newest technologies in the field of machine learning to detect silences in a video and cut it in the most efficient way.
Also generate a transcript of the video and a subtitle file.

## How to use 
First you must to install all the dependences with the command 
~~~
pip install -r requirements.txt
~~~
Then you can use the software using the command from the command line

## Arguments
positional arguments: <br>
&nbsp;input_file&nbsp;The video file you want modified <b> can be more than one </b><br><br>

## Optional arguments 
positional arguments:<br>
&nbsp;input_file&nbsp;&nbsp;The video file you want modified<br>

options:<br>
&nbsp;-h, --help&nbsp;&nbsp;show this help message and exit<br>
&nbsp;--clip_interval CLIP_INTERVAL<br>
&nbsp;&nbsp;&nbsp;The precision of the trimming<br>
&nbsp;--sound_threshold SOUND_THRESHOLD<br>
&nbsp;&nbsp;&nbsp;Maximun amout of volume to be considerer as silence<br>
&nbsp;-j [JOIN], --join [JOIN]<br>
&nbsp;&nbsp;&nbsp;Join all the clips together<br>
&nbsp;-t [TRANSCRIPT], --transcript [TRANSCRIPT]<br>
&nbsp;&nbsp;&nbsp;Transcript the video<br>
&nbsp;-s [STATISTICS], --statistics [STATISTICS]<br>
&nbsp;&nbsp;&nbsp;Show statistics<br>
&nbsp;-d [DISCARD_SILENCE], --discard_silence [DISCARD_SILENCE]<br>
&nbsp;&nbsp;&nbsp;Discard silence clips<br>
&nbsp;-n [DENOISE], --denoise [DENOISE]<br>
&nbsp;&nbsp;&nbsp;Remove background noise from the video<br>

## Example
This will result in a merge of every non-silence part 
~~~
python main.py vid_1.mp4 vid_2.mp4 -d -j
~~~

This will result in a merge of every non-silence part and generate a transcript of the video
~~~
python main.py vid_1.mp4 vid_2.mp4 -d -j -t
~~~

This will result will separate every non-silence part and will remove the background noise
~~~
python main.py vid_1.mp4 vid_2.mp4 -d -n
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
