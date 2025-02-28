import argparse
import logging
from operations import (
    generate_video_base,
    add_titles,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    tools = {
        "base": generate_video_base,
        "add_titles": add_titles,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=str, nargs="+", help="Archivo(s) a procesar")
    parser.add_argument(
        "tool", type=str, help=f"Herramienta a usar: {', '.join(tools.keys())}"
    )
    args = parser.parse_args()
    for file in args.files:
        if args.tool not in tools:
            logger.error(
                "Tool %s not found, options: %s", args.tool, ", ".join(tools.keys())
            )
            continue
        tools[args.tool](file)
