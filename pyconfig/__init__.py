import json
import os
import sys
from pathlib import Path

from pyconfig.exception import ConfigLoadError

_root = {}


def load(name, callback, proc_name=None):
    _root["name"] = name
    _root["config"] = {}

    if sys.platform.startswith('linux'):
        _root["appData"] = str(Path.home()) + "/." + name
    elif sys.platform == "win32":
        _root["appData"] = os.path.expandvars(r'%LOCALAPPDATA%') + "/." + name
    else:
        raise ConfigLoadError("Unknow Systeme")

    try:
        os.makedirs(_root["appData"])
    except OSError:
        if not os.path.isdir(_root["appData"]):
            raise ConfigLoadError(str(_root["appData"]) + "is not a directory")

    try:
        with open(_root["appData"]+"/config.json", "r") as f:
            _root["config"] = json.loads(f.read())

    except FileNotFoundError:
        pass

    if proc_name:
        set_proc_name(proc_name)

    callback()

    save()


def save():
    with open(_root["appData"]+"/config.json", "w") as f:
        f.write(json.dumps(_root["config"]))


def create(key_path, default=None):
    key_path = key_path.split(".")
    current = _root["config"]
    for key in key_path[:-1]:
        try:
            current = current[key]
        except KeyError:
            current[key] = {}
            current = current[key]
    try:
        current = current[key_path[-1]]
    except KeyError:
        current[key_path[-1]] = default


def get(key_path):
    key_path = key_path.split(".")
    current = _root["config"]
    for key in key_path[:-1]:
        current = current[key]
    return current[key_path[-1]]


def edit(key_path, value):
    key_path = key_path.split(".")
    current = _root["config"]
    for key in key_path[:-1]:
        current = current[key]
    current[key_path[-1]] = value


def appData_path():
    return _root["appData"]


def set_proc_name(newname):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(newname)+1)
    buff.value = newname.encode()
    libc.prctl(15, byref(buff), 0, 0, 0)
