def set_vertical(**kwargs):
    input_video_file_clip = kwargs["input_video_file_clip"]
    width, height = input_video_file_clip.size
    if width > height:
        new_size = (height, width)
        input_video_file_clip = input_video_file_clip.resize(new_size)
    kwargs["shape"] = input_video_file_clip.size
    kwargs["input_video_file_clip"] = input_video_file_clip
    return kwargs


def set_horizontal(**kwargs):
    input_video_file_clip = kwargs["input_video_file_clip"]
    width, height = input_video_file_clip.size
    if width < height:
        new_size = (height, width)
        input_video_file_clip = input_video_file_clip.resize(new_size)
    kwargs["shape"] = input_video_file_clip.size
    kwargs["input_video_file_clip"] = input_video_file_clip
    return kwargs
