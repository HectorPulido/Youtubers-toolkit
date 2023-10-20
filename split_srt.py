import argparse
from datetime import datetime, timedelta


def split_srt(file, words_per_subtitle):
    time_format = "%H:%M:%S,%f"

    with open(file, "r", encoding="utf-8") as file_data:
        content = file_data.read()
        subtitle_parts = content.split("\n\n")

        new_subtitles = []
        unique_id = 1
        for part in subtitle_parts:
            lines = part.split("\n")
            timestamps = lines[1]
            start_time, end_time = timestamps.split(" --> ")
            start_datetime = datetime.strptime(start_time, time_format)
            end_datetime = datetime.strptime(end_time, time_format)

            word_list = lines[2].split()
            number_of_subtitles = len(word_list) // words_per_subtitle
            if len(word_list) % words_per_subtitle != 0:
                number_of_subtitles += 1

            sec_per_subtitle = (
                end_datetime - start_datetime
            ).total_seconds() / number_of_subtitles

            for i in range(0, len(word_list), words_per_subtitle):
                display_start = start_datetime + timedelta(
                    seconds=sec_per_subtitle * (i // words_per_subtitle)
                )
                display_end = display_start + timedelta(seconds=sec_per_subtitle)
                words_to_display = " ".join(word_list[i : i + words_per_subtitle])
                new_subtitles.append(
                    f"{unique_id}\n{display_start.strftime(time_format)[:-3]} --> {display_end.strftime(time_format)[:-3]}\n{words_to_display}\n\n"
                )
                unique_id += 1

        return "".join(new_subtitles)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="The file to split")
    parser.add_argument(
        "words_per_subtitle", type=int, help="The number of words per subtitle"
    )
    args = parser.parse_args()

    splitted_srt = split_srt(args.file, args.words_per_subtitle)

    with open(f"{args.file[:-4]}_splitted.srt", "w", encoding="utf-8") as f:
        f.write(splitted_srt)
