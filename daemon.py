#! python3

import tmdbsimple as tmdb


from daemon_lib.db_scripts import DBUpdateScripts, ScriptHandler
from daemon_lib.http_handlers import MovieHandler, GenreHandler, VideoHandler, UploadHandler
from daemon_lib.db_description import database_description

from common_lib.config import ConfigMananger


from pydbm import DataBase

from pynet.http_server import HTTP_server, HTTP_handler
from pynet.network import MainServer, init_serverSock

import sys

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
database_scripts = DBUpdateScripts()

tmdb.API_KEY = config.get("tmdb.api_key")


ms = MainServer()

http_server = HTTP_server()
http_server.add_route("/movie/?([^/]*)/?", MovieHandler, database, config)
http_server.add_route("/genre", GenreHandler, database, config)
http_server.add_route("/video/?([^/]*)/?([^/]*)", VideoHandler, database, config)
http_server.add_route("/scripts/?([^/]*)", ScriptHandler, database_scripts, database, config)
http_server.add_route("/upload/?", UploadHandler, database, config)

ms.add_socket(init_serverSock(4242), http_server)

try:
    while True:
        ms.run_once()
except KeyboardInterrupt:
    ms.close()
    database.close()
    database_scripts.close()
