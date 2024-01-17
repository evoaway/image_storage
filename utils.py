import os

from PIL import Image

def move_to_beginning(my_tuple, element_to_move):
    if element_to_move not in my_tuple:
        return my_tuple
    new_tuple = (element_to_move,) + tuple(item for item in my_tuple if item != element_to_move)
    return new_tuple

def get_metadata(filepath):
    image = Image.open(filepath)
    info_dict = {
        "Filename": image.filename,
        "Image Size": image.size,
        "Image Height": image.height,
        "Image Width": image.width,
        "Image Size in bytes": os.stat(filepath).st_size,
        "Image Format": image.format,
        "Image Mode": image.mode,
        "Image is Animated": getattr(image, "is_animated", False),
        "Frames in Image": getattr(image, "n_frames", 1)
    }
    return info_dict

def compress(filepath, quality):
    image = Image.open(filepath)
    image.save(filepath, optimize=True, quality=quality)
