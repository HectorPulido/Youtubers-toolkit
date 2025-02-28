from datetime import datetime, timedelta

TIME_FORMAT = "%H:%M:%S,%f"


def _process_file(file_info, words_subtitle):
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
        start_datetime = datetime.strptime(start_time, TIME_FORMAT)
        end_datetime = datetime.strptime(end_time, TIME_FORMAT)

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
                f"{unique_id}\n{display_start.strftime(TIME_FORMAT)[:-3]} --> \
                    {display_end.strftime(TIME_FORMAT)[:-3]}\n{words_to_display}\n\n"
            )
            unique_id += 1

    return "".join(new_subtitles)


def split_srt(file_path, words_subtitle):
    with open(file_path, "r", encoding="utf-8") as file_info:
        return _process_file(file_info, words_subtitle)
