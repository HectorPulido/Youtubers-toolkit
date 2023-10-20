import argparse
from datetime import datetime, timedelta


def split_srt(file_path, words_subtitle):
    time_format = "%H:%M:%S,%f"

    with open(file_path, "r", encoding="utf-8") as file_info:
        content = file_info.read()
        subtitle_parts = content.split("\n\n")

        new_subtitles = []
        unique_id = 1
        for part in subtitle_parts:
            lines = part.split("\n")
            if len(lines) != 3:
                break

            timestamps = lines[1]
            start_time, end_time = timestamps.split(" --> ")
            start_datetime = datetime.strptime(start_time, time_format)
            end_datetime = datetime.strptime(end_time, time_format)

            word_list = lines[2].split()
            number_of_subtitles = len(word_list) // words_subtitle
            if len(word_list) % words_subtitle != 0:
                number_of_subtitles += 1

            sec_per_subtitle = (
                end_datetime - start_datetime
            ).total_seconds() / number_of_subtitles

            for i in range(0, len(word_list), words_subtitle):
                display_start = start_datetime + timedelta(
                    seconds=sec_per_subtitle * (i // words_subtitle)
                )
                display_end = display_start + timedelta(seconds=sec_per_subtitle)
                words_to_display = " ".join(word_list[i : i + words_subtitle])
                new_subtitles.append(
                    f"{unique_id}\n{display_start.strftime(time_format)[:-3]} --> {display_end.strftime(time_format)[:-3]}\n{words_to_display}\n\n"
                )
                unique_id += 1

        return "".join(new_subtitles)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=str, nargs="+", help="The file to split")
    parser.add_argument(
        "words_per_subtitle", type=int, help="The number of words per subtitle"
    )

    args = parser.parse_args()

    files = args.files
    words_per_subtitle = args.words_per_subtitle

    for file in files:
        with open(f"{file[:-4]}_splitted.srt", "w", encoding="utf-8") as file_data:
            file_data.write(split_srt(file, words_per_subtitle))
