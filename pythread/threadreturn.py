import queue
import threading
import types


class ThreadReturn:
    def __init__(self):
        self.value = None
        self.error = None
        self.completeEvent = threading.Condition()
        self.completed = False
        self.gen_queue = queue.Queue()
        self.gen = False

    def join(self):
        with self.completeEvent:
            self.completeEvent.wait()

    def set_value(self, value):
        with self.completeEvent:
            self.completed = True
            self.completeEvent.notify_all()
            if(isinstance(value, types.GeneratorType)):
                self.gen = True
                for data in value:
                    self.gen_queue.put(data)
                value = None
            self.gen_queue.put(value)

    def set_error(self, error):
        self.error = error
        self.completed = True
        try:
            self.completeEvent.notify_all()
        except RuntimeError:
            pass

    def _get_generator(self):
        while True:
            data = self.gen_queue.get()
            if(self.error is not None):
                raise self.error
            if data is not None:
                yield data
            else:
                break

    def get_value(self):
        if(not self.completed):
            self.join()
        if self.gen:
            return self._get_generator()
        if(self.error is not None):
            raise self.error
        return self.value