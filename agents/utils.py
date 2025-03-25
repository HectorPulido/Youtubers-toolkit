"""
Utility functions for the agents
"""

import json
from openai import OpenAI


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
