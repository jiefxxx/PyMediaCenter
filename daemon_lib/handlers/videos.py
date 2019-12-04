import os

import pyconfig
from common_lib.config import MEDIA_TYPE_MOVIE
from common_lib.videos_info import get_movie_info, check_for_space, get_normalized_file_name
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
            media_type = int(self.header.url.get("media_type", default=None))
            media_id = int(self.header.url.get("media_id", default=None))
            if media_type is None or media_id is None:
                return self.response.send_error(400)

            if media_type == MEDIA_TYPE_MOVIE:
                movie_info = get_movie_info(media_id, language=pyconfig.get("language"))
                movie_info["genre_ids"] = []
                for genre in movie_info["genres"]:
                    movie_info["genre_ids"].append(genre["id"])

                directory = os.path.dirname(video["path"])
                ext = video["path"].split(".")[-1]

                base_paths = pyconfig.get("videos.movies.path")
                if directory not in base_paths:
                    directory = None
                    for path in base_paths:
                        if check_for_space(path, video["size"]):
                            directory = path
                if directory is None:
                    raise Exception("No space available in path :"+str(base_paths))

                definitive_filename = directory + "/" + get_normalized_file_name(movie_info, ext)
                os.rename(video["path"], definitive_filename)

                video["path"] = definitive_filename
                video["media_type"] = media_type
                video["media_id"] = media_id

                db.set("videos", video)
                db.set("movies", movie_info)
                self.user_data["notify"].notify_refresh("video")
                self.response.send_text(200, "ok " + video["path"])

            else:
                return self.response.send_error(400)

        return self.response.send_error(404)
