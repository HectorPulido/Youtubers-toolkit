# Youtubers toolkit

This project is a comprehensive command-line toolkit designed for video editing and processing tasks. It provides a modular framework to perform operations such as trimming by silence, adding subtitles, denoising audio, generating transcripts and translations, and even creating short videos with dynamic titles.

## Features

- **Configuration Loader:** Loads settings from a JSON file (`config.json`) to configure various operations.
- **Video Editing Pipeline:** Supports a sequence of operations (e.g., trim by silence, add subtitles, set orientation) to edit videos.
- **Audio Processing:** Extracts, separates, and denoises audio from video files.
- **Voice Operations:** Utilizes AI models (e.g., Whisper, Bark) for video translation and audio generation.
- **Short Video Generation:** Creates a video base with a blurred background and overlays content or titles.
- **Utility Functions:** Includes tools to concatenate source files and handle subtitle splitting.

## Installation

### Prerequisites

- **Python 3.10+**  
- Required libraries (installable via `pip`):
  - `moviepy`
  - `numpy`
  - `scipy`
  - `whisper`
  - `torch`
  - `torchaudio`
  - `pydub`
  - `librosa`
  - `bark` (for audio generation)
  - _...and any additional dependencies as noted in individual modules._

### Setup

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure your `requirements.txt` lists all necessary dependencies.)*

4. Configure the project by editing the `config.json` file to adjust settings such as subtitle and title clip configurations.

## Usage

The main entry point is `main.py`, which provides several subcommands for different tasks. Run the following command to see available options:

```bash
python main.py --help
```

## Subcommands Overview

The CLI tool uses subcommands to select the desired functionality. You invoke the tool using one of the following subcommands:

1. **video_edit** – For processing video files with a customizable pipeline of functions.
2. **separate_audio** – To extract audio from video files.
3. **split_str** – To split SRT subtitle files based on a specified number of words per subtitle.
4. **voice** – To perform voice operations such as video translation or audio generation.
5. **generator** – To generate a base video or add titles for short video production.

Each subcommand has its own required and optional arguments. Use the `--help` flag with any subcommand to see detailed usage information.

---

## 1. Video Editing (`video_edit`)

**Description:**  
This subcommand processes video files by applying a sequence (pipeline) of editing functions.

### Usage
```bash
python main.py video_edit <input_file1> [<input_file2> ...] --pipeline <function1> [<function2> ...] [options]
```

### Arguments

- **input_file** (required):  
  One or more video file paths to process.

- **--pipeline** (required):  
  List of functions to apply to each video file.  
  **Available functions:**
  - `trim_by_silence`
  - `denoise`
  - `transcript`
  - `subtitles`
  - `save_separated_video`
  - `save_join`
  - `save_video`
  - `set_vertical`
  - `set_horizontal`

### Options

- **-c, --clip_interval**:  
  *Type:* float, *Default:* 2  
  *Description:* Clipping precision.

- **-s, --sound_threshold**:  
  *Type:* float, *Default:* 0.01  
  *Description:* Maximum volume threshold to consider silence.

- **-d, --discard_silence**:  
  *Type:* boolean flag (uses a string-to-boolean converter), *Default:* False  
  *Description:* Discard silent clips.

### Example
```bash
python main.py video_edit video1.mp4 video2.mp4 --pipeline trim_by_silence subtitles -c 3 -s 0.02 -d True
```
*This applies the `trim_by_silence` and `subtitles` functions to `video1.mp4` and `video2.mp4` with a clip interval of 3 seconds and a sound threshold of 0.02, discarding silent clips.*

---

## 2. Separate Audio (`separate_audio`)

**Description:**  
Extracts audio from the given video files.

### Usage
```bash
python main.py separate_audio <video_file1> [<video_file2> ...]
```

### Arguments

- **files** (required):  
  One or more video files from which to extract audio.

### Example
```bash
python main.py separate_audio video1.mp4 video2.mp4
```
*This command will extract the audio from `video1.mp4` and `video2.mp4` and save them accordingly.*

---

## 3. Split SRT (`split_str`)

**Description:**  
Splits SRT subtitle files into smaller segments based on a specified number of words per subtitle.

### Usage
```bash
python main.py split_str <srt_file1> [<srt_file2> ...] <words_per_subtitle>
```

### Arguments

- **files** (required):  
  One or more SRT files to split.

- **words_per_subtitle** (required):  
  *Type:* integer  
  *Description:* The number of words per subtitle segment.

### Example
```bash
python main.py split_str subtitles.srt 5
```
*This will split the subtitles in `subtitles.srt` so that each subtitle contains approximately 5 words.*

---

## 4. Voice Operations (`voice`)

**Description:**  
Performs voice operations such as video translation or audio generation.

### Usage
```bash
python main.py voice <operation> <video_path> [options]
```

### Arguments

- **operation** (required):  
  Operation to perform. Choose between:
  - `video_translation`
  - `audio_generator`

- **video_path** (required):  
  The path to the video file to process.

### Options

- **-t, --translate**:  
  *Type:* boolean flag (using a string-to-boolean converter), *Default:* True  
  *Description:* Translate the video to English or transcribe in the same language.

- **--voice**:  
  *Type:* string, *Default:* `"v2/en_speaker_2"`  
  *Description:* Voice model to use for translation.

- **--low_profile_mode**:  
  *Type:* boolean, *Default:* True  
  *Description:* Low profile mode for systems with less processing power.

### Example
```bash
python main.py voice video_translation video1.mp4 -t False --voice v2/en_speaker_2
```
*This translates `video1.mp4` using the specified voice model, with translation turned off (if you only want transcription).*

---

## 5. Short Video Generator (`generator`)

**Description:**  
Generates a base video or adds titles to a short video.

### Usage
```bash
python main.py generator <file1> [<file2> ...] <tool>
```

### Arguments

- **files** (required):  
  One or more files to process.

- **tool** (required):  
  The tool to use. Available options:
  - `base` – to generate a base video.
  - `add_titles` – to add titles to the video.

### Example
```bash
python main.py generator video1.mp4 base
```
*This command uses the `base` tool on `video1.mp4` to generate a base video.*

---

## General Help

To display the help information for the CLI tool or a specific subcommand, use the `--help` flag. For example:
```bash
python main.py --help
python main.py video_edit --help
```

This will display all available options and arguments for that command.


## Project Structure

- **config_loader.py:** Loads configuration from `config.json` and makes it available throughout the project.
- **main.py:** The central entry point that defines and handles multiple subcommands for video processing.
- **automatic_short_generator.py:** A script to generate short videos using predefined tools.
- **get_data.py:** A utility to traverse directories and concatenate files.
- **utils/**
  - **utils.py:** Contains helper functions (e.g., converting strings to booleans, audio extraction, video metadata extraction).
- **operations/**
  - **save.py:** Functions to save edited or joined video clips.
  - **set_orientation.py:** Adjusts video orientation (vertical/horizontal).
  - **subtitles.py:** Adds subtitles to videos.
  - **shorts.py:** Generates base videos with effects (e.g., blurred background) and adds title clips.
  - **transcript.py:** Generates transcripts using the Whisper model.
  - **trim.py:** Implements silence detection and video trimming.
  - **translation.py:** Handles video translation and audio generation.
  - **denoise.py:** Applies denoising filters using deep learning models.
  - **split_srt.py:** Splits SRT files based on word count per subtitle.

## Configuration

The toolkit uses a JSON configuration file (`config.json`) to define parameters such as:
- Subtitle and title clip settings (e.g., font, size, position).
- Other customizable options for processing operations.

Adjust these settings according to your needs before running any commands.

## Contributing

Contributions are welcome! If you have suggestions or improvements, feel free to open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


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
