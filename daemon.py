#! python3
import asyncio

import tmdbsimple as tmdb

from daemon_lib.db_scripts import DBUpdateScripts
from daemon_lib.http_handlers import MovieHandler, GenreHandler, VideoHandler, UploadHandler, ScriptHandler
from daemon_lib.db_description import database_description
from common_lib.config import ConfigMananger
from daemon_lib.ws_room import ScriptsRoom

from pydbm import DataBase

from pynet.http.server import HTTPServer

import sys

from pythread import close_all_mode

if len(sys.argv) > 1:
    config_path = sys.argv[1]
else:
    config_path = "./client.json"

config = ConfigMananger(config_path)
config.create("language", default="fr_be")
config.create("tmdb.api_key", default='bd00b4d04b286b876c3455692a531120')
config.create("videos.downloads.path", default=[])
config.create("videos.movies.path", default=[])
config.create("videos.tvs.path", default=[])
config.create("rsc.poster_path", default="./posters")
config.create("database.path", default="./test.db")

config.save()

database = DataBase(config.get("database.path"))
database.create(database_description)
scripts_room = ScriptsRoom()
database_scripts = DBUpdateScripts(scripts_room)

tmdb.API_KEY = config.get("tmdb.api_key")


_loop = asyncio.get_event_loop()
http_server = HTTPServer(_loop)


http_server.add_user_data("database", database)
http_server.add_user_data("config", config)

http_server.add_route("/movie/?([^/]*)/?", MovieHandler)
http_server.add_route("/genre", GenreHandler)
http_server.add_route("/video/?([^/]*)/?([^/]*)", VideoHandler)
http_server.add_route("/scripts/?([^/]*)", ScriptHandler, ws=scripts_room, user_data={"scripts": database_scripts})
http_server.add_route("/upload", UploadHandler)

http_server.initialize()
_loop.set_debug(False)
try:
    _loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
http_server.close()
_loop.close()
database_scripts.close()
close_all_mode()

