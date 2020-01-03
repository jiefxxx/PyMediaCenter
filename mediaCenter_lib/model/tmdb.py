import pyconfig
from common_lib.videos_info import SearchTmdb
from mediaCenter_lib.model import ModelTableListDict
from pythread import threaded


class TmdbMovieModel(ModelTableListDict):
    def __init__(self):
        ModelTableListDict.__init__(self, [("Title", "title", False, None),
                                           ("Release date", "release_date", False, None)])
        self.search = SearchTmdb(pyconfig.get("tmdb.api_key"))

    @threaded("httpCom")
    def on_search(self, text, year=None):
        self.begin_busy()
        self.clear()
        for movie in self.search.search_movie(text, year, language=pyconfig.get("language")):
            self.add_data(movie)
        self.end_busy()


class TmdbTvModel(ModelTableListDict):
    def __init__(self):
        ModelTableListDict.__init__(self, [("Title", "name", False, None),
                                           ("Release date", "first_air_date", False, None),
                                           ("Overview", "overview", False, None)])
        self.search = SearchTmdb(pyconfig.get("tmdb.api_key"))

    @threaded("httpCom")
    def on_search(self, text, year=None):
        self.begin_busy()
        self.clear()
        for movie in self.search.search_tv(text, language=pyconfig.get("language")):
            self.add_data(movie)
        self.end_busy()
