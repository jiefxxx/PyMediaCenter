import os

import pyconfig
from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from common_lib.fct import ensure_dir
from common_lib.videos_info import get_movie_info, check_for_space, get_normalized_file_name, get_tv_info, \
    get_episode_info, get_normalized_episode_name
from pynet.http.handler import HTTPHandler


class VideoHandler(HTTPHandler):
    def GET(self, url, video_id, action):
        db = self.user_data["database"]
        columns = url.get("columns")
        if columns is not None:
            columns = columns.split(",")

        if video_id is None:
            return self.response.send_json(200, list(db.get("videos", columns=columns,
                                        where=url.to_sql_where(blacklist=["columns"]))))
        else:
            videos = list(db.get("videos", columns=columns, where={'video_id': int(video_id)}))

        if len(videos) == 0:
            return self.response.send_error(404)
        video = videos[0]

        if action is None:
            return self.response.send_json(200, videos[0])

        if action == "stream":
            try:
                return self.response.send_file(videos[0]["path"])
            except FileNotFoundError:
                pass

        if action == "delete":
            os.remove(video["path"])
            db.delete_row("videos", where={'video_id': int(video_id)})
            self.user_data["notify"].notify_refresh("video")
            return self.response.send_text(200, "ok ")

        if action == "last_time":
            last_time = int(self.header.url.get("media_type", default=None))
            if last_time is None:
                return self.response.send_error(400)

            video["last_time"] = last_time
            db.set("videos", video)
            return self.response.send_text(200, "ok ")

        if action == "edit":
            media_type = int(self.header.url.get("media_type", default=-1))
            if media_type == -1:
                return self.response.send_error(400)

            directory = os.path.dirname(video["path"])
            ext = video["path"].split(".")[-1]
            video["media_type"] = media_type

            if media_type == MEDIA_TYPE_MOVIE:
                movie_id = int(self.header.url.get("movie_id", default=-1))
                if movie_id == -1:
                    return self.response.send_error(400)

                movie_info = get_movie_info(movie_id, language=pyconfig.get("language"))

                if movie_info is None:
                    return self.response.send_error(404)

                video["media_id"] = movie_id

                db.set("videos", video)
                db.set("movies", movie_info)

                self.response.send_text(200, "ok " + video["path"])

                directory = get_directory(directory, video["size"], pyconfig.get("videos.movies.path"))
                definitive_filename = directory + "/" + get_normalized_file_name(movie_info, ext)
                self.user_data["tasks"].new_task("rename_video", db, video, definitive_filename)

            if media_type == MEDIA_TYPE_TV:
                tv_id = int(self.header.url.get("tv_id", default=-1))
                season = int(self.header.url.get("season", default=-1))
                episode = int(self.header.url.get("episode", default=-1))

                if tv_id == -1 or season == -1 or episode == -1:
                    return self.response.send_error(400)

                tv_info = get_tv_info(tv_id, language=pyconfig.get("language"))
                episode_info = get_episode_info(tv_id, season, episode, language=pyconfig.get("language"))

                if tv_info is None or episode_info is None:
                    return self.response.send_error(404)

                video["media_id"] = episode_info["id"]

                db.set("tv_shows", tv_info)
                db.set("tv_episodes", episode_info)
                db.set("videos", video)

                self.response.send_text(200, "ok " + video["path"])

                directory = get_directory(directory, video["size"], pyconfig.get("videos.tvs.path"))
                definitive_filename = directory + "/" + get_normalized_episode_name(tv_info, season, episode, ext)
                ensure_dir(os.path.dirname(definitive_filename))
                self.user_data["tasks"].new_task("rename_video", db, video, definitive_filename)

            else:
                return self.response.send_error(400)

        return self.response.send_error(404)


def get_directory(current_directory, size, list_directory):
    if current_directory in list_directory:
        return current_directory
    for directory in list_directory:
        if check_for_space(directory, size):
            return directory
    raise Exception("No space available in path :" + str(list_directory))
