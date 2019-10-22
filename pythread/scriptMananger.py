from pythread.threadMananger import ThreadMananger


class Scripts(ThreadMananger):
    def __init__(self):
        ThreadMananger.__init__(self)
        self.script_name = None
        self.progress = 0.0
        self.string = ""
        self.script_list = {}

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
            self.exec_fct(None, script, *args, **kwargs)
            return True
        return False
