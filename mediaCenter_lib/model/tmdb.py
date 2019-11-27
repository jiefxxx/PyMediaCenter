import pyconfig
from common_lib.videos_info import SearchMovie
from mediaCenter_lib.base_model import ModelTableListDict
from pythread import threaded


class TmdbModel(ModelTableListDict):
    def __init__(self):
        ModelTableListDict.__init__(self, [("Title", "title", False),
                                           ("Release date", "release_date", False)])
        self.search = SearchMovie(pyconfig.get("tmdb.api_key"))

    @threaded("httpCom")
    def on_search(self, text, year=None):
        self.begin_busy()
        self.clear()
        for movie in self.search.search_movie(text, year, language=pyconfig.get("language")):
            self.add_data(movie)
        self.end_busy()