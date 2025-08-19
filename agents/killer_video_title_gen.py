"""
This script generates killer video titles for YouTube videos using OpenAI's API.
"""

import os
import sys
import json

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .utils import try_to_load_json
    from .persona_testing import PersonaTester
except ImportError:
    from utils import try_to_load_json
    from persona_testing import PersonaTester

load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o3-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
)


def gen_video_summary(videos_string: str) -> str:
    """
    Take the description (videos_string) of the existing YouTuber videos
    and generate a brief summary about their style.
    """
    prompt = f"""
    Your objective is to summarize this video on it's original language
    The summary must describe the video, give it's structure and extract interesting quotes 
    The summary must be on the video language
 
    <video_transcription>
    {videos_string}
    </video_transcription>  

    Return only a plain text with the summary and nothing else
    """.strip()
    response = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def gen_video_titles(videos_string: str, num_of_titles: int) -> str:
    """
    Generate N titles for the given title
    """
    prompt = f"""
    You are a world-famous YouTuber and copywritter, you master the creation of viral content, high-CTR YouTube video titles.  
    Your objective is to generate {str(num_of_titles)} PERFECT YouTube video titles for the following video description.  

    <guidelines>
    - Titles must be SHORT (ideal: 50 characters or less, maximum: 70).  
    - Use SIMPLE, powerful language (5th-grade reading level).  
    - Create **clear titles, not vague ones**. They must instantly communicate what the video is about.  
    - Optimize for **SEO keywords** relevant to the content.  
    - Place the most important words at the **beginning** of the title.  
    - Use proven high-performing formats when possible:  
    • “How to …”  
    • “Top 10 …” / “Best …”  
    • “The Truth About …”  
    • “I Tried … So You Don’t Have To”  
    • “What Happens If …”  
    • “The Secret to …”  
    - Avoid clickbait that deceives viewers. Generate **curiosity without confusion**.  
    - Titles should **work together with the thumbnail** to create intrigue and urgency.  
    - Always use the same language as the video description.  
    </guidelines>  

    <video_description>
    {videos_string}
    </video_description>  

    Return only a JSON list of {str(num_of_titles)} killer YouTube video titles:  

    [
        "My killer video title 1",
        "My killer video title 2",
        ...
    ]
    """.strip()
    response = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Usage: python killer_video_title_gen.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    with open(video_path, "r", encoding="utf-8") as file:
        video_transcription = file.read()

    summary = gen_video_summary(video_transcription)

    persona_tester = PersonaTester(
        model=OPENAI_MODEL,
        client=_client,
        comparation_path="videos_to_compare.json",
    )
    titles = gen_video_titles(summary, persona_tester.ideas_to_generate)
    titles = try_to_load_json(_client, OPENAI_MODEL, titles)
    print("\n=== INITIAL VIDEO TITLES ===")
    print(titles)

    titles_results = persona_tester.test_multiples_videos(
        titles,
        checks=100,
        use_extra_titles=True,
    )

    print(f"\n=== {persona_tester.ideas_to_generate} FINAL VIDEO TITLES ===")
    print(titles_results)

    with open("output.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(titles_results, ensure_ascii=False, indent=4))
