from pythread import create_new_mode
from pythread.modes import RunOnceMode


class Scripts:
    def __init__(self):
        self.mode = create_new_mode(RunOnceMode, type(self).__name__)
        self.script_name = None
        self.progress = 0.0
        self.string = ""
        self.script_list = {}
        self.alive = True

    def set_script(self, script_name, script):
        self.script_list[script_name] = script

    def get_script(self, script_name):
        try:
            return self.script_list[script_name]
        except KeyError:
            return None

    def get_state(self):
        return {"script": self.script_name, "progress": self.progress, "string": self.string}

    def set_progress(self, progress, string):
        self.progress = progress
        self.string = string

    def start_script(self, script_name, *args, **kwargs):
        script = self.get_script(script_name)
        if script is not None:
            self.script_name = script_name
            if not self.mode.is_busy():
                self.mode.process(script, *args, **kwargs)
            return True
        return False

    def close(self):
        self.mode.close()
        self.alive = False
