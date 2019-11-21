import pyconfig


def configure_callback():
    pyconfig.create("language", default="fr_be")
    pyconfig.create("tmdb.api_key", default='bd00b4d04b286b876c3455692a531120')
    pyconfig.create("videos.downloads.path", default=[])
    pyconfig.create("videos.movies.path", default=[])
    pyconfig.create("videos.tvs.path", default=[])
    pyconfig.create("rsc.poster_path", default="./posters")
    pyconfig.create("database.path", default="./test.db")


MEDIA_TYPE_UNKNOWN = 0
MEDIA_TYPE_MOVIE = 1
MEDIA_TYPE_TV = 2