import platform

import pyconfig


def configure_callback():

    pyconfig.create("hostname", default=platform.node())
    pyconfig.create("language", default="fr_be")
    pyconfig.create("tmdb.api_key", default='bd00b4d04b286b876c3455692a531120')
    pyconfig.create("videos.downloads.path", default=[])
    pyconfig.create("videos.movies.path", default=[])
    pyconfig.create("videos.tvs.path", default=[])
    pyconfig.create("rsc.poster_mini_path", default=pyconfig.get_dir("poster/mini"))
    pyconfig.create("rsc.poster_original_path", default=pyconfig.get_dir("poster/original"))
    pyconfig.create("database.path", default=pyconfig.appData_path()+"test.db")


MEDIA_TYPE_UNKNOWN = 0
MEDIA_TYPE_MOVIE = 1
MEDIA_TYPE_TV = 2

NOTIFY_REFRESH = 0
NOTIFY_PROGRESS = 1
