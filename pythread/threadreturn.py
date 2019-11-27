import asyncio
import queue
import threading
import types


class Event(asyncio.Event):
    # TODO: clear() method
    def set(self):
        # FIXME: The _loop attribute is not documented as public api!
        self._loop.call_soon_threadsafe(super().set)


class ThreadReturn:
    def __init__(self):
        self.value = None
        self.error = None
        self.completeEvent = threading.Condition()
        try:
            self.asyncEvent = Event()
        except RuntimeError:
            self.asyncEvent = None
        self.completed = False
        self.gen_queue = queue.Queue()
        self.gen = False

    async def async_wait(self):
        await self.asyncEvent.wait()
        self.asyncEvent.clear()

    def join(self):
        with self.completeEvent:
            self.completeEvent.wait()

    def set_value(self, value):
        with self.completeEvent:
            self.completed = True
            self.completeEvent.notify_all()
            if self.asyncEvent:
                self.asyncEvent.set()
            if isinstance(value, types.GeneratorType):
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
            if self.error is not None:
                raise self.error
            if data is not None:
                yield data
            else:
                break

    def get_value(self):
        if not self.completed:
            self.join()
        if self.gen:
            return self._get_generator()
        if self.error is not None:
            raise self.error
        return self.value
