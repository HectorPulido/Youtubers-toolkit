"""
Utility functions for the agents
"""

import json
import re
from openai import OpenAI
import requests


def try_to_load_json(_client: OpenAI, model: str, json_string: str) -> dict | list:
    """
    Try to load a JSON string. If it fails, it will try to fix the JSON string
    """

    json_prompt = """
        This is a JSON string, but it is not well formatted. delete everything that is not JSON, fix any possible formatting issue and return only the JSON string. without text, without explanation, ``` or anything else.
    """

    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        # Si no se puede cargar como JSON, intenta corregirlo
        response = _client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": json_prompt + json_string}],
        )
        try:
            return json.loads(response.choices[0].message.content.strip())
        except json.JSONDecodeError:
            return {}


def get_youtube_data(youtube_username):
    """
    Get YouTube data from a user's channel.
    """
    regex = r'""([\sa-zA-Z0-9áéíóúÁÉÍÓÚ]+)""'
    replacement = r'"\1"'

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        )
    }

    url = f"https://www.youtube.com/{youtube_username}/videos"
    page = requests.get(url, timeout=5, headers=headers)
    html_str = page.content.decode("utf-8")

    json_string = html_str.split("var ytInitialData = ")[-1].split(";</script>")[0]
    cleaned_json_string = json_string.replace("\n", " ").replace("\r", " ")
    cleaned_json_string = re.sub(regex, replacement, cleaned_json_string)
    json_data = json.loads(cleaned_json_string, strict=False)

    video_list = []
    tabs = json_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
    for tab in tabs:
        if tab.get("tabRenderer", {}).get("title", "").lower() not in [
            "videos",
            "vídeos",
            "video",
        ]:
            continue
        for video in tab["tabRenderer"]["content"]["richGridRenderer"]["contents"]:
            video_data = {}
            if "richItemRenderer" not in video:
                continue
            video_data["title"] = video["richItemRenderer"]["content"]["videoRenderer"][
                "title"
            ]["runs"][0]["text"]
            video_data["id"] = video["richItemRenderer"]["content"]["videoRenderer"][
                "videoId"
            ]
            video_data["url"] = f"https://www.youtube.com/watch?v={video_data['id']}"
            video_data["thumbnail"] = (
                f"https://img.youtube.com/vi/{video_data['id']}/0.jpg"
            )
            video_data["published"] = video["richItemRenderer"]["content"][
                "videoRenderer"
            ]["publishedTimeText"]["simpleText"]
            video_data["viewCountText"] = video["richItemRenderer"]["content"][
                "videoRenderer"
            ]["viewCountText"]["simpleText"]
            video_list.append(video_data)
        break
    return video_list
