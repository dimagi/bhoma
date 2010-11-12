import threading

class TimeoutException(Exception):
    pass

class TimeoutTask(threading.Thread):
    def __init__(self, func, args, kwargs, cachefunc=None):
        threading.Thread.__init__(self)
        self.eval = lambda: func(*args, **kwargs)
        self.cachefunc = cachefunc
        self.expired = False
        self.lock = threading.Lock()

    def run(self):
        self.result = self.eval()
        with self.lock:
            if self.expired and self.cachefunc:
                self.cachefunc(self.result)

    def execute(self, timeout=None):
        self.start()
        self.join(timeout)
        with self.lock:
            if self.isAlive():
                self.expired = True
                raise TimeoutException()
            else:
                return self.result

def timeout(n, cachefunc=None):
    def timeout_n(f):
        return lambda *args, **kwargs: TimeoutTask(f, args, kwargs, cachefunc).execute(n)
    return timeout_n
