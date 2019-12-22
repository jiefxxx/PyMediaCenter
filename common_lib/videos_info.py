import os
import re
import sys

import requests
import tmdbsimple as tmdb

if sys.platform == "win32":
    from winmagic import magic
else:
    import magic

from alphabet_detector import AlphabetDetector
from pymediainfo import MediaInfo


def check_for_space(path, size):
    statvfs = os.statvfs(path)
    free_bytes = statvfs.f_frsize * statvfs.f_bfree
    if size >= free_bytes:
        return False
    return True


def get_genres(language=None, api_key=None):
    if api_key is not None:
        tmdb.API_KEY = api_key

    genres = tmdb.Genres()
    for genre in genres.movie_list(language=language)["genres"]:
        genre["genre_id"] = genre["id"]
        genre["genre_name"] = genre["name"]
        yield genre
    for genre in genres.tv_list(language=language)["genres"]:
        genre["genre_id"] = genre["id"]
        genre["genre_name"] = genre["name"]
        yield genre


class SearchMovie:
    def __init__(self, api_key):
        tmdb.API_KEY = api_key
        self.search = tmdb.Search()

    def search_movie(self, string, year=None, language=None):
        if len(string) == 0:
            return
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

    def search_tv(self, string, language=None):
        if len(string) == 0:
            return
        if language is not None:
            language = language[:2]
        self.search.tv(query=string, language=language)
        for s in self.search.results:
            yield get_tv_info(s["id"], language=language)


def normalize_filename(name):
    banished = ('.',)
    replace = ('\'', ':', ',', ' ', '/')
    name = name.lower()
    for item in banished:
        name = name.replace(item, '')
    for item in replace:
        name = name.replace(item, '.')

    return name


def get_normalized_title(original_title, title):
    if AlphabetDetector().is_latin(original_title):
        title = original_title
    return normalize_filename(title)


def get_normalized_file_name(tmdb_info, ext):
    name = get_normalized_title(tmdb_info["original_title"],  tmdb_info["title"])
    name += "."+tmdb_info["release_date"][:4]+'.'+ext
    return name


def get_normalized_episode_name(tmdb_info, season, episode, ext):
    name = get_normalized_title(tmdb_info["original_name"], tmdb_info["name"])
    return "%s/%s.s%.2ie%.2i.%s" % (name, name, season, episode, ext)


def get_movie_info(_id, language=None):
    if language is not None:
        language = language[:2]
    movie_info = tmdb.Movies(_id).info(language=language)
    movie_info["genre_ids"] = []
    for genre in movie_info["genres"]:
        movie_info["genre_ids"].append(genre["id"])
    return movie_info


def get_tv_info(tv_id, language=None):
    if language is not None:
        language = language[:2]
    tv_info = tmdb.TV(tv_id).info(language=language)
    tv_info["genre_ids"] = []
    for genre in tv_info["genres"]:
        tv_info["genre_ids"].append(genre["id"])
    return tv_info


def get_episode_info(tv_id, season, episode, language=None):
    try:
        if language is not None:
            language = language[:2]
        info = tmdb.TV_Episodes(tv_id, season_number=season, episode_number=episode).info(language=language)
        info["episode_overview"] = info["overview"]
        info["episode_name"] = info["name"]
        info["episode_vote_average"] = info["vote_average"]
        info["tv_id"] = tv_id
        return info
    except requests.exceptions.HTTPError as e:
        print(e)
        return None


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
    if not os.path.isdir(path):
        raise Exception("Not a valid directory -> %s" % path)
    for root, subdirs, files in os.walk(path):
        for f in files:
            f = os.path.join(root, f)
            yield f


def parse_movie_name(path_name):
    name = path_name.split('/')[-1]
    try:
        return ' '.join(name.split('.')[:-2]), int(name.split('.')[-2])
    except ValueError:
        return None, None


def parse_episode_name(path_name):
    name = path_name.split('/')[-1]
    try:
        m = re.match(r"(.*)[s](\d*)[e](\d*).*", name.lower())
        tv_name = m.group(1).replace('.', ' ')
        saison = int(m.group(2))
        episode = int(m.group(3))
    except (AttributeError, ValueError):
        tv_name = None
        saison = None
        episode = None
    return tv_name, saison, episode


reg_tv_show = [r".*[s]?(\d+)[ex](\d+).*"]


def parse_episode_path(path_name):
    name = path_name.split('/')[-1]
    for reg in reg_tv_show:
        try:
            m = re.match(reg, name.lower())
            return int(m.group(1)), int(m.group(2))
        except (AttributeError, ValueError):
            pass

    return None, None
