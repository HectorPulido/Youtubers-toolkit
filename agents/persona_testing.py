"""
This module contains the TestingWithPersona class, which is used to test video titles
"""

import random
from concurrent.futures import ThreadPoolExecutor

try:
    from utils import try_to_load_json
except ImportError:
    from .utils import try_to_load_json


class PersonaTester:
    """
    Class to test video titles with different personas.
    """

    def __init__(self, client, model, comparation_path):
        """
        Initialize the TestingWithPersona class.
        """
        self._model = model
        self._client = client
        with open(comparation_path, "r", encoding="utf-8") as file:
            comparations = try_to_load_json(self._client, self._model, file.read())
        self.comparation = comparations

    def test_video(self, titles_to_compare, title_to_test, persona):
        """
        Test the title against a list of titles to compare.
        """
        videos = titles_to_compare.copy()
        videos.append(title_to_test)
        random.shuffle(videos)
        title_to_test_index = videos.index(title_to_test) + 1
        videos_str = "\n".join(
            [f"{idx + 1}. {video}" for idx, video in enumerate(videos)]
        )
        prompt = f"""
            You are {persona}
            You are on your youtube feed and some videos are showing
            <videos>
            {videos_str}
            </videos>
            Which video do you click? Respond only one number inside "", nothing else
            eg. "<my_selected_title_number_video>"
        """
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        selected = response.choices[0].message.content.strip()
        return f'"{title_to_test_index}"' in selected

    def test_multiples_videos(self, titles, checks=100, use_extra_titles=False):
        """
        Test multiple videos with different personas.
        """
        user_personas = self.comparation["user_personas"]
        titles_to_compare = self.comparation["titles"]

        if use_extra_titles:
            titles += self.comparation.get("extra_titles", [])

        personas_to_test = random.choices(user_personas, k=checks)

        results_by_title = {title: {"selected": 0, "shown": 0} for title in titles}
        tasks = []
        results = []

        with ThreadPoolExecutor() as executor:
            # Enviar todas las tareas concurrentemente.
            for title in titles:
                for persona in personas_to_test:
                    future = executor.submit(
                        self.test_video, titles_to_compare, title, persona
                    )
                    tasks.append((title, future))

            # Recopilar y agrupar los resultados por título.
            for title, future in tasks:
                try:
                    result = future.result()
                except Exception as e:
                    print(f"Error processing title {title}: {e}")
                    result = False
                results_by_title[title]["shown"] += 1
                if result:
                    results_by_title[title]["selected"] += 1

        for title, counts in results_by_title.items():
            percentage = (
                (counts["selected"] / counts["shown"] * 100)
                if counts["shown"] > 0
                else 0
            )

            print(
                "Result: ",
                {
                    "title": title,
                    "time_selected": counts["selected"],
                    "times_shown": counts["shown"],
                    "percentage": percentage,
                },
            )
            results.append(
                {
                    "title": title,
                    "time_selected": counts["selected"],
                    "times_shown": counts["shown"],
                    "percentage": percentage,
                }
            )
        return results
