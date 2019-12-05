#! python3
import asyncio
import os
import time

import tmdbsimple as tmdb

from daemon_lib.db_scripts import DBUpdateScripts
from daemon_lib.handlers.videos import VideoHandler
from daemon_lib.handlers.genres import GenreHandler
from daemon_lib.handlers.movies import MovieHandler
from daemon_lib.handlers.upload import UploadHandler
from daemon_lib.handlers.scripts import ScriptHandler
from daemon_lib.db_description import database_description
from daemon_lib.ws_room import ScriptsRoom

from pydbm import DataBase

from pynet.http.server import HTTPServer

from pythread import close_all_mode

from common_lib.config import configure_callback
import pyconfig

pyconfig.load("pymediacenter", proc_name="pymediacenter-daemon", callback=configure_callback)


async def power_management(sys_com):
    while True:
        sys_com.ping_all()
        await asyncio.sleep(30)
        if sys_com.last_pong+20*60 < time.time():
            print("entering power saving mode")
            os.system("sudo pm-suspend")


database = DataBase(pyconfig.get("database.path"))
database.create(database_description)
scripts_room = ScriptsRoom()
database_scripts = DBUpdateScripts(scripts_room)

tmdb.API_KEY = pyconfig.get("tmdb.api_key")


_loop = asyncio.get_event_loop()

http_server = HTTPServer(_loop)

http_server.add_user_data("database", database)
http_server.add_user_data("notify", scripts_room)

http_server.add_route("/movie/?([^/]*)/?", MovieHandler)
http_server.add_route("/genre", GenreHandler)
http_server.add_route("/video/?([^/]*)/?([^/]*)", VideoHandler)
http_server.add_route("/scripts/?([^/]*)", ScriptHandler, ws=scripts_room, user_data={"scripts": database_scripts})
http_server.add_route("/upload", UploadHandler)

http_server.initialize()
_loop.set_debug(False)
_loop.create_task(power_management(scripts_room))
try:
    _loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
http_server.close()
_loop.close()
database_scripts.close()
close_all_mode()

