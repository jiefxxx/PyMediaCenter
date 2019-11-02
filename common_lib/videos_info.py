import os
import tmdbsimple as tmdb
import magic
from alphabet_detector import AlphabetDetector
from pymediainfo import MediaInfo


def check_for_space(path, size):
    statvfs = os.statvfs(path)
    free_bytes = statvfs.f_frsize * statvfs.f_bfree
    print(size, free_bytes)
    if size >= free_bytes:
        return False
    return True


def get_genres(language=None, api_key=None):
    if api_key is not None:
        tmdb.API_KEY = api_key

    genres = tmdb.Genres()
    for genre in genres.movie_list(language=language)["genres"]:
        yield genre
    for genre in genres.tv_list(language=language)["genres"]:
        yield genre


class SearchMovie:
    def __init__(self, api_key):
        tmdb.API_KEY = api_key
        self.search = tmdb.Search()

    def search_movie(self, string, year=None, language=None):
        if language is not None:
            language = language[:2]
        self.search.movie(query=string, primary_release_year=year)
        if len(self.search.results) > 0:
            for s in self.search.results:
                s = tmdb.Movies(s["id"]).info(language=language)
                if "release_date" in s and year is not None:
                    if int(s["release_date"][:4]) == year:
                        yield s
                elif year is None:
                    yield s
        return None


def normalize_filename(name):
    banished = ('.',)
    replace = ('\'', ':', ',', ' ', '/')
    name = name.lower()
    for item in banished:
        name = name.replace(item, '')
    for item in replace:
        name = name.replace(item, '.')

    return name


def get_normalized_title(tmdb_info):
    if AlphabetDetector().is_latin(tmdb_info["original_title"]):
        title = tmdb_info["original_title"]
    else:
        title = tmdb_info["title"]
    return normalize_filename(title)


def get_normalized_file_name(tmdb_info, ext):
    name = get_normalized_title(tmdb_info)
    name += "."+tmdb_info["release_date"][:4]+'.'+ext
    return name


def get_movie_info(_id, language=None):
    if language is not None:
        language = language[:2]
    return tmdb.Movies(_id).info(language=language)


def get_video_info(path, media_type):
    ret = {}
    media_info = MediaInfo.parse(path)
    for track in media_info.tracks:
        if track.track_type == 'General':
            ret["codecs_video"] = track.codecs_video
            ret["bit_rate"] = track.overall_bit_rate
            ret["duration"] = track.duration
            ret["size"] = track.file_size
            ret["m_time"] = track.file_last_modification_date
        if track.track_type == 'Video':
            ret["width"] = track.width
            ret["height"] = track.height
    ret["media_type"] = media_type
    ret["path"] = path
    return ret


def get_videos(path):
    mime = magic.Magic(mime=True)
    if not os.path.isdir(path):
        raise Exception("Not a valid directory -> %s" % path)
    for root, subdirs, files in os.walk(path):
        for f in files:
            f = os.path.join(root, f)
            if mime.from_file(f).split("/")[0] == "video":
                yield f