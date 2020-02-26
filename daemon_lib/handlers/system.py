import os
import time

from pynet.http.exceptions import HTTPError

import pythread
from pynet.http.handler import HTTPHandler
from pythread.modes import RunForeverMode


class Task:
    def __init__(self, tasks, script, *args, **kwargs):
        self.tasks = tasks
        self.id = self.tasks.get_id()
        self.script = script
        self.args = args
        self.kwargs = kwargs
        self.progress = 0.0
        self.string = ""

    def is_alive(self):
        return self.tasks.is_alive()

    def execute(self):
        self.script.fct(self, *self.args, **self.kwargs)

    def execute_description(self):
        return self.script.description(*self.args, **self.kwargs)

    def do_progress(self, progress, string):
        self.progress = progress
        self.string = string
        self.tasks.notify_progress(self)

    def json(self):
        return {"id": self.id,
                "name": self.script.name,
                "description": self.execute_description(),
                "progress": self.progress,
                "string": self.string}


class Tasks:
    def __init__(self, com):
        self.com = com
        self.id_count = 0
        self.tasks = []
        self.scripts = []
        self.notify = []
        self.last_time = time.time()
        pythread.create_new_mode(RunForeverMode, "tasks", self.run)

    def is_alive(self):
        return pythread.get_mode("tasks").is_alive()

    def create_script(self, script):
        self.scripts.append(script)

    def get_script(self, name):
        for script in self.scripts:
            if script.name == name:
                return script
        raise Exception("Script not Found "+str(name))

    def run(self):
        if len(self.tasks) > 0:
            task = self.tasks.pop(0)
            task.do_progress(0.0, "starting")
            task.execute()
            task.do_progress(1.0, "ended")

            if task.script.refresh_type not in self.notify:
                self.notify.append(task.script.refresh_type)

            if self.last_time+60 >= time.time():
                self.clear_notify()

            return True

        self.clear_notify()

        time.sleep(1)
        return True

    def clear_notify(self):
        for n in self.notify:
            self.com.notify_refresh(n)
        self.last_time = time.time()
        self.notify = []

    def new_task(self, name, *args, **kwargs):
        task = Task(self, self.get_script(name), *args, **kwargs)
        self.tasks.append(task)
        self.com.notify_task(task.json())

    def notify_progress(self, task):
        self.com.notify_task(task.json())

    def get_id(self):
        self.id_count += 1
        return self.id_count

    def json(self):
        ret = []
        for task in self.tasks:
            ret.append(task.json())
        return ret


class SystemHandler(HTTPHandler):
    def GET(self, url):
        action = url.regex[0]
        if action == "suspend":
            os.system("systemctl suspend")
            return self.response.text(200, "ok")
        if action == "tasks":
            return self.response.json(200, self.user_data["tasks"].json())
        raise HTTPError(404)

