import queue
import sys
import threading
import traceback
import types

Lock = threading.Lock

class Thread(threading.Thread):
    def __init__(self,**kwargs):
        self.debug = False
        threading.Thread.__init__(self,**kwargs)
        self.queue = queue.Queue()
        self.brun = False

    def set_queue(self,queue):
        self.queue = queue

    def run(self):
        while True:
            data = self.queue.get()
            if data is None:
                break
            self.brun = True
            fct,ret,args,kwargs = data
            if self.debug:
                print("execute ",fct.__name__,str(args),str(kwargs),
                                                    " in ",self.getName())
            try:
                ret.set_value(fct(*args,**kwargs))
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback,
                             file=sys.stdout)
                print("exception in thread"+self.getName()+" :")
                ret.set_error(e)
            self.brun = False
            self.queue.task_done()
        print("end thread "+self.getName())

    def is_working(self):
        return self.brun

def threadedFunction(thread=None):
    def decorated(func):
        def wrapper(*args, **kwargs):
            return args[0].exec_fct(thread,func,*args,**kwargs)
        return wrapper
    return decorated

def sequesterFunction(thread=None):
    def decorated(func):
        def wrapper(*args, **kwargs):
            return args[0].exec_fct(thread,func,*args,**kwargs).get_value()
        return wrapper
    return decorated

def lockedFunction():
    def decorated(func):
        def wrapper(*args, **kwargs):
            args[0].lock.acquire()
            ret = None
            exception = None
            try:
                ret = func(*args,**kwargs)
            except Exception as e:
                exception = e
            finally:
                args[0].lock.release()
                if(exception is not None):
                    raise(exception)
                else:
                    return ret
        return wrapper
    return decorated

def lockedGenerator():
    def decorated(func):
        def wrapper(*args, **kwargs):
            args[0].lock.acquire()
            exception = None
            ret = []
            try:
                for _ret in func(*args,**kwargs):
                    ret.append(_ret)
            except Exception as e:
                exception = e
            finally:
                args[0].lock.release()
                if(exception is not None):
                    raise(exception)
                else:
                    return ret
        return wrapper
    return decorated

class ThreadMananger():
    def __init__(self,nbr_thread=1,debug=False,one_queue=False):
        self.list_thread = []
        self.i = 0
        self.one_queue = one_queue
        if self.one_queue:
            self.main_queue = queue.queue()
        for i in range(0,nbr_thread):
            t = Thread(name="Thread "+str(i))
            t.debug = debug
            if one_queue:
                t.queue = self.main_queue
            self.list_thread.append(t)
        self.alive = True
        for thread in self.list_thread:
            thread.start()

    def _increment(self):
        self.i += 1
        if self.i >= len(self.list_thread):
            self.i = 0
        return self.i

    def exec_fct(self,i,func,*args,**kwargs):
        ret = ThreadReturn()
        if self.one_queue:
            self.main_queue.put((func,ret,args,kwargs))
            return ret
        if i is None:
            for thread in self.list_thread:
                if not thread.is_working():
                    thread.queue.put((func,ret,args,kwargs))
                    return ret
            i = self._increment()
        self.list_thread[i].queue.put((func,ret,args,kwargs))
        return ret

    def join_all_job(self):
        for thread in self.list_thread:
            thread.queue.join()

    def close(self):
        self.alive = False
        for thread in self.list_thread:
            thread.queue.put(None)
            thread.join()

class ThreadReturn():
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

    def set_value(self,value):
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
