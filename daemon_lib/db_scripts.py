from common_lib.config import MEDIA_TYPE_UNKNOWN, MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
from pynet.http.handler import HTTPHandler
from pythread.scriptMananger import Scripts
from common_lib.videos_info import SearchMovie, get_video_info, get_videos, get_genres


def parse_movie_name(path_name):
    name = path_name.split('/')[-1]
    try:
        return ' '.join(name.split('.')[:-2]), int(name.split('.')[-2])
    except ValueError:
        return None, None


class DBUpdateScripts(Scripts):
    def __init__(self):
        Scripts.__init__(self)
        self.set_script("update_videos", self.update_videos)
        self.set_script("update_movies", self.update_movies)
        self.set_script("update_genres", self.update_genres)

    def update_genres(self, db, cm):
        self.set_progress(0, "started")
        for genre in get_genres(language=cm.get("language"), api_key=cm.get("tmdb.api_key")):
            db.set("genres", genre)
        self.set_progress(1, "finish")

    def update_videos_worker(self, paths, media_type, db, cm):
        if not self.alive:
            return
        for root_path in cm.get(paths):
            videos = list(get_videos(root_path))
            size = len(videos)
            i = 0
            for path in videos:
                if not self.alive:
                    return
                i += 1
                self.set_progress(i/size, path)
                if len(list(db.get("videos", where={"path": path}))) == 0:
                    video = get_video_info(path, media_type)
                    db.set("videos", video)

    def update_videos(self, db, cm):
        self.set_progress(0, "started")
        self.update_videos_worker("videos.downloads.path", MEDIA_TYPE_UNKNOWN, db, cm)
        self.update_videos_worker("videos.movies.path", MEDIA_TYPE_MOVIE, db, cm)
        self.update_videos_worker("videos.tvs.path", MEDIA_TYPE_TV, db, cm)
        self.set_progress(1, "finish")

    def update_movies(self, db, cm):
        self.set_progress(0, "started")
        search = SearchMovie(cm.get("tmdb.api_key"))
        videos = list(db.get("videos", where={"media_id": None, "media_type": MEDIA_TYPE_MOVIE}))
        size = len(videos)
        i = 0
        for video in videos:
            if not self.alive:
                return
            i += 1
            self.set_progress(i/size, video["path"])
            movie_name, movie_year = parse_movie_name(video["path"])
            if movie_name is not None:
                results = search.search_movie(movie_name, movie_year, language="fr")
                movie_info = next(results, None)
                if movie_info is not None:
                    print(video["path"], movie_info["title"])
                    movie_info["genre_ids"] = []
                    for genre in movie_info["genres"]:
                        movie_info["genre_ids"].append(genre["id"])
                    video["media_id"] = movie_info["id"]
                    db.set("movies", movie_info)
                    db.set("videos", video)


class ScriptHandler(HTTPHandler):
    def GET(self, url, script_name):
        scripts = self.user_data["scripts"]
        cm = self.user_data["config"]
        db = self.user_data["database"]
        if script_name is None:
            return self.response.send_error(404)

        if script_name == "state":
            return self.response.send_json(200, scripts.get_state())

        if scripts.start_script(script_name, db, cm):
            return self.response.send_text(200, "ok")

        return self.response.send_error(404)
