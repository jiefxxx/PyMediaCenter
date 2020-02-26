#! python3
import asyncio
import logging
import os
import time

import tmdbsimple as tmdb

from daemon_lib.db_scripts import GenresUpdate, FilesUpdate, TvsUpdate, MoviesUpdate, MovieEdit, TvEdit, RefreshUnknowns
from daemon_lib.handlers.system import Tasks
from daemon_lib.handlers.tvs import TvShowHandler, TvEpisodeHandler
from daemon_lib.handlers.videos import VideoHandler
from daemon_lib.handlers.genres import GenreHandler
from daemon_lib.handlers.movies import MovieHandler
from daemon_lib.handlers.upload import UploadHandler
from daemon_lib.handlers.scripts import ScriptHandler
from daemon_lib.db_description import database_description
from daemon_lib.ws_room import ScriptsRoom

from pydbm import DataBase

from pynet.http.server import HTTPServer
from pynet.multicast import create_multicast_server

from pythread import close_all_mode

from common_lib.config import configure_callback
import pyconfig

logging.basicConfig(level=logging.DEBUG)

pyconfig.load("pymediacenter", proc_name="pymediacenter-daemon", callback=configure_callback)


async def power_management(sys_com):
    while True:
        sys_com.ping_all()
        await asyncio.sleep(30)
        if sys_com.last_pong+20*60 < time.time():
            print("entering power saving mode")
            os.system("sudo pm-suspend")
            protocol.send_iam()
            sys_com.last_pong = time.time()


def print_iam(addr, name):
    pass
    # print("new client", addr, name)


tmdb.API_KEY = pyconfig.get("tmdb.api_key")

database = DataBase(pyconfig.get("database.path"))
database.create(database_description)

scripts_room = ScriptsRoom()
tasks = Tasks(scripts_room)

tasks.create_script(GenresUpdate())
tasks.create_script(FilesUpdate())
tasks.create_script(TvsUpdate())
tasks.create_script(MoviesUpdate())
tasks.create_script(MovieEdit())
tasks.create_script(TvEdit())
tasks.create_script(RefreshUnknowns())

loop = asyncio.get_event_loop()

http_server = HTTPServer(loop=loop, port=4242)

http_server.router.add_user_data("database", database)
http_server.router.add_user_data("notify", scripts_room)
http_server.router.add_user_data('tasks', tasks)

http_server.router.add_route("/movie/?([^/]*)/?", MovieHandler)
http_server.router.add_route("/tv/?([^/]*)/?", TvShowHandler)
http_server.router.add_route("/episode/?([^/]*)/?", TvEpisodeHandler)
http_server.router.add_route("/genre", GenreHandler)
http_server.router.add_route("/video/?([^/]*)/?([^/]*)", VideoHandler)
http_server.router.add_route("/scripts/?([^/]*)", ScriptHandler, ws=scripts_room)
http_server.router.add_route("/upload", UploadHandler)

http_server.start()

protocol = loop.run_until_complete(create_multicast_server(loop, "server_"+pyconfig.get("hostname"), print_iam))
# loop.create_task(power_management(scripts_room))

http_server.run_forever()

# Close the server
protocol.close()
loop.close()
close_all_mode()

