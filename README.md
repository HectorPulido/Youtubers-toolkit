# Youtubers toolkit

This Tool allows you to cut a video easily by silences with an intuitive command line interface.

## How to use 
First you must to install all the dependences with the command 
~~~
pip install -r requirements.txt
~~~
Then you can use the software using the command from the command line

## Arguments
positional arguments: <br>
&nbsp;&nbsp;&nbsp;&nbsp;input_file&nbsp;&nbsp;&nbsp;The video file you want modified <b> can be more than one </b><br><br>

## Optional arguments 
&nbsp;&nbsp;&nbsp;&nbsp;-h,&nbsp;--help            show this help message and exit<br>
&nbsp;&nbsp;&nbsp;&nbsp;--clip_interval CLIP_INTERVAL The precision of the trimming<br>
&nbsp;&nbsp;&nbsp;&nbsp;--sound_threshold SOUND_THRESHOLD Maximun amout of volume to be considerer as silence <br>
&nbsp;&nbsp;&nbsp;&nbsp;-j [JOIN], --join [JOIN] Join all the clips together <br>
&nbsp;&nbsp;&nbsp;&nbsp;-s [STATISTICS], --statistics [STATISTICS] Show statistics of the volumen <br>
&nbsp;&nbsp;&nbsp;&nbsp;-d [DISCARD_SILENCE], --discard_silence [DISCARD_SILENCE] Discard silence clips <br>

## Example
This will result in a merge of every non-silence part 
~~~
python main.py vid_1.mp4 vid_2.mp4 -d -j
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
