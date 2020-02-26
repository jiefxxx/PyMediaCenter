import os

from pynet.http.exceptions import HTTPError

from common_lib.config import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from common_lib.videos_info import check_for_space
from pynet.http.handler import HTTPHandler


class VideoHandler(HTTPHandler):
    enable_range = True

    def GET(self, url):
        video_id = url.regex[0]
        action = url.regex[1]
        db = self.user_data["database"]
        notify = self.user_data["notify"]

        columns = url.get("columns")
        if columns:
            columns = columns.split(",")

        if video_id is None:
            return self.response.json(200, list(db.get("videos", columns=columns,
                                                       where=url.to_sql_where(blacklist=["columns"]))))
        else:
            video_id = int(video_id)
            videos = list(db.get("videos", columns=columns, where={'video_id': video_id}))
            if len(videos) == 0:
                raise HTTPError(404)
            video = videos[0]

        if action is None:
            return self.response.json(200, video)

        if action == "stream":
            return self.file(video["path"])

        if action == "delete":
            os.remove(video["path"])
            db.delete_row("videos", where={'video_id': video_id})
            notify.notify_refresh("video")
            return self.response.text(200, "ok ")

        if action == "last_time":
            last_time = url.get("time", default=None, data_type=int)
            if last_time is None:
                raise HTTPError(404)

            video["last_time"] = last_time
            db.set("videos", video)
            return self.response.text(200, "ok ")

        if action == "edit":
            media_type = url.get("media_type", default=None, data_type=int)

            if media_type is None:
                raise HTTPError(400)

            copy = url.get("copy", default=False, data_type=bool)

            directory = os.path.dirname(video["path"])
            ext = video["path"].split(".")[-1]
            video["media_type"] = media_type

            if media_type == MEDIA_TYPE_MOVIE:
                movie_id = url.get("movie_id", default=None, data_type=int)
                if movie_id is None:
                    raise HTTPError(400)

                self.user_data["tasks"].new_task("edit_movie", db, video, movie_id, directory, ext, copy)

                return self.response.text(200, "ok " + video["path"])

            if media_type == MEDIA_TYPE_TV:
                tv_id = url.get("tv_id", default=None, data_type=int)
                season = url.get("season", default=None, data_type=int)
                episode = url.get("episode", default=None, data_type=int)

                if tv_id is None or season is None or episode is None:
                    raise HTTPError(400)

                self.user_data["tasks"].new_task("edit_tv", db, video, tv_id, season, episode, directory, ext, copy)

                return self.response.text(200, "ok " + video["path"])

            else:
                raise HTTPError(400)

        raise HTTPError(404)


def get_directory(current_directory, size, list_directory):
    if current_directory in list_directory:
        return current_directory
    for directory in list_directory:
        if check_for_space(directory, size):
            return directory
    raise Exception("No space available in path :" + str(list_directory))
