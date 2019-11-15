from pythread.threadreturn import ThreadReturn
from pythread.threads import ProcessThread, RunForeverThread, RunOnceThread


class ThreadMode:
    def __init__(self, name, debug=False):
        self.name = name
        self._debug = debug

    def close(self):
        pass


class ProcessMode(ThreadMode):
    def __init__(self, name, size=1, debug=False):
        ThreadMode.__init__(self, name, debug)
        self._threads = []
        for i in range(0, size):
            self._threads.append(ProcessThread(self.name + "-" + str(i), debug=self._debug))

    def process(self, fct, *args, **kwargs):
        ret = ThreadReturn()
        self.get_less_active_thread().queued_fct(fct, ret, args, kwargs)
        return ret

    def get_less_active_thread(self):
        less_thread = None
        for thread in self._threads:
            if less_thread is None or len(less_thread) > len(thread):
                less_thread = thread
        return less_thread

    def close(self):
        for thread in self._threads:
            thread.close()


class RunForeverMode(ThreadMode):
    def __init__(self, name, fct, *args, debug=False, **kwargs):
        ThreadMode.__init__(self, name, debug)
        self._thread = RunForeverThread(name, fct, args, kwargs)

    def process(self, fct, *args, **kwargs):
        self._thread.reset(fct, args, kwargs)

    def close(self):
        self._thread.close()


class RunOnceMode(ThreadMode):
    def __init__(self, name, debug=False):
        ThreadMode.__init__(self, name, debug)
        self._thread = RunOnceThread(name)

    def process(self, fct, *args, **kwargs):
        self._thread.reset(fct, args, kwargs)

    def is_busy(self):
        return self._thread.is_busy()

    def close(self):
        self._thread.close()
