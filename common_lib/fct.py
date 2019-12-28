import errno
import math
import os
import shutil
import time
import uuid

from common_lib.config import MEDIA_TYPE_UNKNOWN, MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV


def convert_media_type(media_type):
    if media_type == MEDIA_TYPE_UNKNOWN:
        return "Unknown"
    elif media_type == MEDIA_TYPE_MOVIE:
        return "Movie"
    elif media_type == MEDIA_TYPE_TV:
        return "Tv Show"


def ensure_dir(path):
    if not os.path.exists(path):
        print("Create ", path)
        os.mkdir(path)


def convert_size(size_bytes):
    if size_bytes == 0 or size_bytes is None:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def add_px(pixels):
    return "%s px" % (str(pixels),)


def convert_bit_stream(bit_stream):
    return convert_size(bit_stream)+"/s"


def convert_duration(millis):
    seconds = int(millis/1000)
    return time.strftime('%H:%M:%S', time.gmtime(seconds))


def move_file(src, dst):
    try:
        os.rename(src, dst)
    except OSError as err:

        if err.errno == errno.EXDEV:
            # Generate a unique ID, and copy `<src>` to the target directory
            # with a temporary name `<dst>.<ID>.tmp`.  Because we're copying
            # across a filesystem boundary, this initial copy may not be
            # atomic.  We intersperse a random UUID so if different processes
            # are copying into `<dst>`, they don't overlap in their tmp copies.
            copy_id = uuid.uuid4()
            tmp_dst = "%s.%s.tmp" % (dst, copy_id)
            shutil.copyfile(src, tmp_dst)

            # Then do an atomic rename onto the new name, and clean up the
            # source image.
            os.rename(tmp_dst, dst)
            os.unlink(src)
        else:
            raise