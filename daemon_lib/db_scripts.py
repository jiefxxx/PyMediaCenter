import os

import magic

import pyconfig
from common_lib.config import MEDIA_TYPE_UNKNOWN, MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from common_lib.fct import ensure_dir, move_file
from common_lib.videos_info import SearchTmdb, get_video_info, get_videos, get_genres, parse_movie_name, \
    get_episode_info, parse_episode_name, get_movie_info, get_normalized_file_name, get_tv_info, \
    get_normalized_episode_name
from daemon_lib.handlers.videos import get_directory


class MovieEdit:
    name = "edit_movie"
    refresh_type = "movies"

    def fct(self, task, db, video, movie_id, directory, ext):
        movie_info = get_movie_info(movie_id, language=pyconfig.get("language"))

        if movie_info is None:
            return

        directory = get_directory(directory, video["size"], pyconfig.get("videos.movies.path"))
        definitive_filename = directory + get_normalized_file_name(movie_info, ext)
        if video["path"] != definitive_filename:
            try:
                move_file(video["path"], definitive_filename)
            except FileNotFoundError:
                pass
        video["path"] = definitive_filename
        db.set("videos", video)

        video["media_id"] = movie_id

        db.set("videos", video)
        db.set("movies", movie_info)

    def description(self, db, video, movie_id, directory, ext):
        return "Edit Movie "+video["path"]


class TvEdit:
    name = "edit_tv"
    refresh_type = "tvs"

    def fct(self, task, db, tv_video, tv_id, season, episode, directory, ext):
        tv_info = get_tv_info(tv_id, language=pyconfig.get("language"))
        episode_info = get_episode_info(tv_id, season, episode, language=pyconfig.get("language"))

        if tv_info is None or episode_info is None:
            return

        directory = get_directory(directory, tv_video["size"], pyconfig.get("videos.tvs.path"))
        definitive_filename = directory + get_normalized_episode_name(tv_info, season, episode, ext)
        ensure_dir(os.path.dirname(definitive_filename))
        if tv_video["path"] != definitive_filename:
            try:
                move_file(tv_video["path"], definitive_filename)
            except FileNotFoundError:
                pass
        tv_video["path"] = definitive_filename

        tv_video["media_id"] = episode_info["id"]

        db.set("tv_shows", tv_info)
        db.set("tv_episodes", episode_info)
        db.set("videos", tv_video)

    def description(self, db, tv_video, tv_id, season, episode, directory, ext):
        return "Edit Tv "+tv_video["path"]


class GenresUpdate:
    name = "update_genres"
    refresh_type = "genres"

    def fct(self, task, db):
        for genre in get_genres(language=pyconfig.get("language"), api_key=pyconfig.get("tmdb.api_key")):
            db.set("genres", genre)

    def description(self, db):
        return "update genre table"


def update_videos_worker(task, paths, media_type, db):
    mime = magic.Magic(mime=True)
    if not task.is_alive():
        return
    for root_path in pyconfig.get(paths):
        videos = list(get_videos(root_path))
        size = len(videos)
        i = 0
        for path in videos:
            if not task.is_alive():
                return
            i += 1
            task.do_progress(i/size, path)
            if mime.from_file(path).split("/")[0] != "video":
                pass
            elif len(list(db.get("videos", where={"path": path}))) == 0:
                video = get_video_info(path, media_type)
                db.set("videos", video)


class FilesUpdate:
    name = "update_videos"
    refresh_type = "videos"

    def fct(self, task, db):
        # update_videos_worker(task, "videos.downloads.path", MEDIA_TYPE_UNKNOWN, db)
        update_videos_worker(task, "videos.movies.path", MEDIA_TYPE_MOVIE, db)
        update_videos_worker(task, "videos.tvs.path", MEDIA_TYPE_TV, db)

    def description(self, db):
        return "update file table"


class RefreshUnknowns:
    name = "refresh_unknowns"
    refresh_type = "videos"

    def fct(self, task, db):
        mime = magic.Magic(mime=True)
        if not task.is_alive():
            return
        for video in db.get("videos", where={"media_type": MEDIA_TYPE_UNKNOWN}):
            if not os.path.exists(video["path"]):
                db.delete_row("videos", where={"video_id": video["video_id"]})
        for root_path in pyconfig.get("videos.downloads.path"):
            videos = list(get_videos(root_path))
            size = len(videos)
            i = 0
            for path in videos:
                if not task.is_alive():
                    return
                i += 1
                task.do_progress(i / size, path)
                if path[-5:] == ".part":
                    pass
                elif mime.from_file(path).split("/")[0] != "video":
                    pass
                elif len(list(db.get("videos", where={"path": path}))) == 0:
                    video = get_video_info(path, MEDIA_TYPE_UNKNOWN)
                    db.set("videos", video)

    def description(self, db):
        return "refresh unknowns"


class TvsUpdate:
    name = "update_tvs"
    refresh_type = "tvs"

    def fct(self, task, db):
        search = SearchTmdb(pyconfig.get("tmdb.api_key"))
        videos = list(db.get("videos", where={"media_id": None, "media_type": MEDIA_TYPE_TV}))
        size = len(videos)
        i = 0
        cache = {}
        for video in videos:
            if not task.is_alive():
                return
            i += 1
            task.do_progress(i / size, video["path"])
            tv_name, season, episode = parse_episode_name(video["path"])
            if tv_name is not None:
                if tv_name in cache:
                    tv_info = cache[tv_name]
                else:
                    results = search.search_tv(tv_name, language=pyconfig.get("language"))
                    tv_info = next(results, None)
                    cache[tv_name] = tv_info
                if tv_info is not None:
                    episode_info = get_episode_info(tv_info["id"], season, episode, language=pyconfig.get("language"))
                    if episode_info is not None:
                        video["media_id"] = episode_info["id"]
                        db.set("tv_episodes", episode_info)
                        db.set("tv_shows", tv_info)
                        db.set("videos", video)

    def description(self, db):
        return "update tvs table"


class MoviesUpdate:
    name = "update_movies"
    refresh_type = "movies"

    def fct(self, task, db):
        search = SearchTmdb(pyconfig.get("tmdb.api_key"))
        videos = list(db.get("videos", where={"media_id": None, "media_type": MEDIA_TYPE_MOVIE}))
        size = len(videos)
        i = 0
        for video in videos:
            if not task.is_alive():
                return
            i += 1
            task.do_progress(i / size, video["path"])
            movie_name, movie_year = parse_movie_name(video["path"])
            if movie_name is not None:
                results = search.search_movie(movie_name, movie_year, language=pyconfig.get("language")[:2])
                movie_info = next(results, None)
                if movie_info is not None:
                    print(video["path"], movie_info["title"])
                    movie_info["genre_ids"] = []
                    for genre in movie_info["genres"]:
                        movie_info["genre_ids"].append(genre["id"])
                    video["media_id"] = movie_info["id"]
                    db.set("movies", movie_info)
                    db.set("videos", video)

    def description(self, db):
        return "update movies table"