#! python3
import asyncio

import tmdbsimple as tmdb

from daemon_lib.db_scripts import DBUpdateScripts
from daemon_lib.http_handlers import MovieHandler, GenreHandler, VideoHandler, UploadHandler, ScriptHandler
from daemon_lib.db_description import database_description
from daemon_lib.ws_room import ScriptsRoom

from pydbm import DataBase

from pynet.http.server import HTTPServer

from pythread import close_all_mode

from common_lib.config import configure_callback
import pyconfig

pyconfig.load("pymediacenter", callback=configure_callback)


def set_proc_name(newname):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(newname)+1)
    buff.value = newname
    libc.prctl(15, byref(buff), 0, 0, 0)


set_proc_name("pymediacenter_daemon")


database = DataBase(pyconfig.get("database.path"))
database.create(database_description)
scripts_room = ScriptsRoom()
database_scripts = DBUpdateScripts(scripts_room)

tmdb.API_KEY = pyconfig.get("tmdb.api_key")


_loop = asyncio.get_event_loop()

http_server = HTTPServer(_loop)

http_server.add_user_data("database", database)

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

