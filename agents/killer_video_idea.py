"""
This script generates unique and engaging YouTube video ideas for a specific channel
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .utils import try_to_load_json
except ImportError:
    from utils import try_to_load_json

load_dotenv()

MODEL = os.getenv("MODEL", "o3-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
)

WHATS_AN_IDEA = """
Concepts examples 
    ❌ THOSE ARE EXAMPLES, You should NOT use them, apply the concept to the user style:

    A video idea is NOT a topic IS THE HOOK. 

    Topic examples:
        > How to cook eggs
        > How to bake cookies
        > Best kitchen appliances in 2025
        > How to cook like a michelin star chef

    Angles of "How to cook like a michelin star chef":
        > How does a michelin star chef cook 200 meals per night?
        > The process, start to finish, of a michelin star dish

    Hook of "The process, start to finish, of a michelin star dish":
        > Breaking down the process of a michelin star dish from menu to ingredients to cook to table

    A good idea should:
    1. Create a sense of urgency and a need to watch the video NOW.
    2. Spark curiosity and make the viewer want to learn more.
    3. Open a loop of information.
"""


def chain_summarize_style(videos_string: str) -> str:
    """
    Take the description (videos_string) of the existing YouTuber videos
    and generate a brief summary about their style.
    """

    prompt = f"""
    You are an AI assistant that analyzes the given YouTuber's content description 
    and writes a concise overview of their style, common themes, and audience expectations.

    YouTuber videos description:
    <videos>
    {videos_string}
    </videos>
    
    TASK:
        Summarize the main themes, style, and audience interest found in the videos described above.
    """
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def chain_generate_ideas(summarized_style: str, num_ideas: int = 15) -> list:
    """
    Create a list of video ideas based on the summarized style of the YouTuber.
    """
    prompt = f"""
    You are an AI specialized in brainstorming extraordinary YouTube video ideas.

    SUMMARY OF THE YOUTUBER'S STYLE:
    <youtuber_style>
    {summarized_style}
    </youtuber_style>
    
    {WHATS_AN_IDEA}

    TASK:
    1. Propose at least {num_ideas} different video ideas (Topic -> Angle -> Hook).
    2. Make sure these ideas align with the YouTuber's direction and style.
    3. Keep them creative and unique.

    Return your response in a JSON format like this, do not return anything else:
    [
        {{
            "Topic": "How to cook like a michelin star chef",
            "Angle": "How does a michelin star chef cook 200 meals per night?",
            "Hook": "Breaking down the process of a michelin star dish from menu to ingredients to cook to table"
        }},
        {{
        ...
        }}
    ]
    """
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    response_final = response.choices[0].message.content.strip()
    return try_to_load_json(_client, MODEL, response_final)


def chain_criticize_and_refine(ideas: dict) -> dict:
    """
    This chain "critique" and refines the generated list of ideas.
    """

    prompt = f"""
    You are an AI harsh critic that wants to refine the video ideas to ensure 
    they are as unique and engaging as possible.

    {WHATS_AN_IDEA}

    BELOW ARE THE VIDEO IDEA (Topic -> Angle -> Hook):
    <ideas>
    {ideas}
    </ideas>
    
    TASK:
    1. Critique each idea concisely, pointing out any weak or cliché aspects.
    2. Suggest a refined or improved version if necessary.
    3. The goal is to transform each idea into a truly outstanding, fresh concept.

    Return the refined ideas, maintaining the (Topic, Angle, Hook) format but incorporating your improvements.

    And add if not existing a WOW FACTOR to each idea.

    Return your response in a JSON format like this, do not return anything else:
    {{
        "Feedback": "This is a great idea, but it could be improved by...",
        "Topic": "How to cook like a michelin star chef",
        "Angle": "How does a michelin star chef cook 200 meals per night?",
        "Hook": "Breaking down the process of a michelin star dish from menu to ingredients to cook to table",
        "WOW": "WOW, Do I really will know how to cook like a michelin star chef after this video??"
    }}
    """
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    response_final = response.choices[0].message.content.strip()
    return try_to_load_json(_client, MODEL, response_final)


def chain_select_best_ideas(
    refined_ideas: dict, summarized_style: str, n_ideas=10
) -> str:
    """
    Take the refined ideas and select the N best ones based on their uniqueness
    """

    prompt = f"""
    You are an AI assistant that selects the {n_ideas} most promising video ideas 
    from the refined list below.
    <ideas>
    {refined_ideas}
    </ideas>

    SUMMARY OF THE YOUTUBER'S STYLE:
    <youtuber_style>
    {summarized_style}
    </youtuber_style>
    
    {WHATS_AN_IDEA}

    TASK:
    1. From the ideas set, Calify them as the best ideas based on their uniqueness, engagement potential, and alignment with the YouTuber's style with a number from 1 to 10.
    2. Return the best {n_ideas} them in a clear format: (Topic, Angle, Hook, And WOW factor).

    Only the final {n_ideas} winning ideas.
    """
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def iterative_idea_generator(
    videos_string: str,
    iterations: int = 2,
    num_initial_ideas: int = 100,
    num_final_ideas: int = 10,
) -> str:
    """
    1. Summary of the style of the channel
    2. Generate several initial ideas
    3. Iterate the critique/refinement N times (iterations)
    4. Select the 10 best final ideas
    """

    style_summary = chain_summarize_style(videos_string)
    print(f"\n--- Style Summary ---\n{style_summary}")

    ideas_current = chain_generate_ideas(style_summary, num_ideas=num_initial_ideas)
    print(f"\n--- Initial Ideas ---\n{ideas_current}")

    for i in range(1, iterations + 1):
        with ThreadPoolExecutor() as executor:
            futures = {}
            for idx, idea in enumerate(ideas_current):
                idea_str = json.dumps(idea, ensure_ascii=False)
                # Lanzamos la tarea en paralelo
                future = executor.submit(chain_criticize_and_refine, idea_str)
                futures[future] = idx

            for future in as_completed(futures):
                idx = futures[future]
                feedback_idea = future.result()
                del feedback_idea["Feedback"]
                ideas_current[idx] = feedback_idea

        print(
            f"\n--- Iteration {i}: Critiquing and Refining Ideas ---\n{ideas_current}"
        )

    final_ideas = chain_select_best_ideas(ideas_current, style_summary, num_final_ideas)
    print(f"\n--- Final Ideas ---\n{final_ideas}")

    return final_ideas


if __name__ == "__main__":
    # Videos from a YouTube channel, just copy and paste the list of videos in a videos.txt file
    with open("videos.txt", "r", encoding="utf-8") as file:
        VIDEOS_STRING_EXAMPLE = file.read()

    _final_ideas = iterative_idea_generator(
        videos_string=VIDEOS_STRING_EXAMPLE,
        iterations=3,
        num_initial_ideas=25,
        num_final_ideas=5,
    )

    print("\n=== 10 FINAL VIDEO IDEAS (TOPIC -> ANGLE -> HOOK) ===")
    print(_final_ideas)

    with open("final_video_ideas.txt", "w", encoding="utf-8") as file:
        file.write(_final_ideas)
