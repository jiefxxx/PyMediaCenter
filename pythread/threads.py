import asyncio
import queue
import sys
import threading
import time
import traceback


def debug_print(self, *args, **kwargs):
    if self._debug:
        print("[DEBUG THREAD] thread:", self.getName(), " - ", *args, **kwargs)


class Thread(threading.Thread):
    def __init__(self, name, debug=False):
        threading.Thread.__init__(self, name=name)
        self._debug = debug
        self._alive = False
        self._terminate = False

    def _exec_fct(self, fct, ret, args, kwargs):
        try:
            value = fct(*args, **kwargs)
            if ret:
                ret.set_value(value)
            return value
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
            print("exception in thread" + self.getName() + " :")
            if ret:
                ret.set_error(e)

    def _run(self):
        pass

    def run(self):
        debug_print(self, "start")
        self._alive = True
        while True:
            if self._terminate or not self._run():
                break
        self._alive = False
        debug_print(self, "ended")

    def is_alive(self):
        return self._alive

    def close(self):
        self._terminate = True


class RunOnceThread(Thread):
    def __init__(self, name, debug=False):
        Thread.__init__(self, name, debug)
        self.fct = None
        self.args = None
        self.kwargs = None
        self.sync = threading.Condition()
        self.busy = False
        self.start()

    def _run(self):
        with self.sync:
            self.sync.wait()
            if not self._terminate:
                self.busy = True
                debug_print(self, "execute ", self.fct.__name__, str(self.args),
                            str(self.kwargs), " in ", self.getName())

                self._exec_fct(self.fct, None, self.args, self.kwargs)
                self.busy = False
                return True

    def is_busy(self):
        return self.busy

    def reset(self, fct, args, kwargs):
        with self.sync:
            if not self.busy:
                self.fct = fct
                self.args = args
                self.kwargs = kwargs
                self.sync.notify_all()
            else:
                raise Exception("Thread busy")

    def close(self):
        with self.sync:
            Thread.close(self)
            self.sync.notify_all()


class AsyncioThread(Thread):
    def __init__(self, name, debug=True):
        Thread.__init__(self, name, debug)
        self.loop = None
        self.start()

    def get_loop(self):
        while not self.loop:
            time.sleep(0.01)
        return self.loop

    def _run_asyncio(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_forever()
        return False

    def _run(self):
        debug_print(self, "execute asyncio in ", self.getName())
        return self._run_asyncio()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        Thread.close(self)


class RunForeverThread(Thread):
    def __init__(self, name, fct, args, kwargs, debug=False):
        Thread.__init__(self, name, debug)
        self.fct = fct
        self.args = args
        self.kwargs = kwargs
        self.start()

    def _run(self):
        debug_print(self, "execute ", self.fct.__name__, str(self.args),
                    str(self.kwargs), " in ", self.getName())
        return self._exec_fct(self.fct, None, self.args, self.kwargs)

    def reset(self, fct, args, kwargs):
        self.fct = fct
        self.args = args
        self.kwargs = kwargs


class ProcessThread(Thread):
    def __init__(self, name, input_queue=None, debug=False):
        Thread.__init__(self, name, debug)
        self._running = False
        if type(input_queue) == queue.Queue:
            self.input_queue = input_queue
        else:
            self.input_queue = queue.Queue()
        self.start()

    def _run(self):
        processing_data = self.input_queue.get()
        if processing_data is None:
            return False
        fct, ret, args, kwargs = processing_data
        debug_print(self, "execute ", fct.__name__, str(args),
                    str(kwargs), " in ", self.getName())
        self._running = True
        self._exec_fct(fct, ret, args, kwargs)
        self._running = False
        self.input_queue.task_done()
        return True

    def close(self):
        self.input_queue.put(None)
        self.join()

    def __len__(self):
        size = self.input_queue.qsize()
        if self._running:
            size += 1
        return size

    def queued_fct(self, fct, ret, args, kwargs):
        self.input_queue.put((fct, ret, args, kwargs))