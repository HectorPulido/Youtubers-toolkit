"""
This script generates unique and engaging YouTube video ideas for a specific channel
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .utils import get_youtube_data, try_to_load_json
    from .persona_testing import PersonaTester
except ImportError:
    from utils import get_youtube_data, try_to_load_json
    from persona_testing import PersonaTester

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
        Add also the language of the videos.
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
    3. Keep them creative and unique don't use the same ideas as the examples.
    4. Use the same language as the YouTuber's style.
    5. Focus on doable ideas, not impossible ones.

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


def chain_criticize_and_refine(ideas: dict, testing: dict) -> dict:
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

    AND BELOW is how the ideas performed on the testing, a good testing is >50%:
    <testing_results>
    {testing}
    </testing_results>
    
    TASK:
    1. Critique each idea concisely, pointing out any weak or cliché aspects.
    2. Suggest a refined or improved version if necessary.
    3. The goal is to transform each idea into a truly outstanding, fresh concept.
    4. Use the same language as the ideas.
    5. Make sure the ideas are doable, not impossible ones.
    
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


def iterative_idea_generator(
    videos_string: str,
    iterations: int = 2,
    num_initial_ideas: int = 100,
    persona: PersonaTester = None,
) -> str:
    """
    1. Summary of the style of the channel
    2. Generate several initial ideas
    3. Test the video ideas using the personas
    4. Remove the ideas with a testing result <10%
    5. Critique and refine the ideas
    6. Repeat the process N times
    7. Return the final ideas
    """

    # 1. Resumen de estilo
    style_summary = chain_summarize_style(videos_string)
    print(f"\n--- Style Summary ---\n{style_summary}")

    # 2. Generar ideas iniciales
    ideas_current = chain_generate_ideas(style_summary, num_ideas=num_initial_ideas)
    print(f"\n--- Initial Ideas ({len(ideas_current)}) ---\n{ideas_current}")

    for i in range(1, iterations + 1):
        # Extraer sólo los títulos
        idea_topics = [idea["Topic"] for idea in ideas_current]

        # 3. Testeo en lote (una sola llamada, devuelve lista ordenada según idea_topics)
        testing_results = persona.test_multiples_videos(titles=idea_topics, checks=20)
        print(f"\n--- Testing Results ({len(testing_results)}) ---\n{testing_results}")

        # 4. Filtrar ideas con percentage < 10%
        kept = [
            (idea, result)
            for idea, result in zip(ideas_current, testing_results)
            if result["percentage"] >= 10
        ]
        ideas_filtered, results_filtered = zip(*kept) if kept else ([], [])
        ideas_current = list(ideas_filtered)
        testing_results = list(results_filtered)

        # 5. Paralelizar crítica y refinamiento
        refined = [None] * len(ideas_current)
        with ThreadPoolExecutor(max_workers=len(ideas_current) or 1) as executor:
            # Lanzar tareas con su índice
            future_to_idx = {
                executor.submit(chain_criticize_and_refine, idea, result): idx
                for idx, (idea, result) in enumerate(
                    zip(ideas_current, testing_results)
                )
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                idea_refined = future.result()
                # Actualizar porcentaje y limpiar feedback
                idea_refined["Likeness_percentage"] = testing_results[idx]["percentage"]
                idea_refined.pop("Feedback", None)
                refined[idx] = idea_refined

        ideas_current = refined
        print(
            f"\n--- Iteration {i}: Critiquing and Refining Ideas ({len(ideas_current)}) ---"
        )

    return ideas_current


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 2:
        print("Usage: python killer_video_idea.py <channel_name>")
        sys.exit(1)

    channel_name = sys.argv[1]
    channel_data = get_youtube_data(channel_name)
    if not channel_data or len(channel_data) < 1:
        print("Error: Unable to retrieve channel data.")
        sys.exit(1)

    channel_data = channel_data[:25]

    persona_tester = PersonaTester(
        model=MODEL,
        client=_client,
        comparation_path="videos_to_compare.json",
    )

    _final_ideas = iterative_idea_generator(
        videos_string=channel_data,
        iterations=3,
        num_initial_ideas=25,
        persona=persona_tester,
    )

    print("\n=== 10 FINAL VIDEO IDEAS (TOPIC -> ANGLE -> HOOK) ===")
    print(_final_ideas)

    with open("ignore_video_ideas.txt", "w", encoding="utf-8") as file:
        file.write(_final_ideas)
