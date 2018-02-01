import contextlib
import threading

from server import Server

class ServerPool(object):
    def __init__(self, server_specs):
        self.servers = [Server(server_spec) for server_spec in server_specs]
        self.server_ready = threading.Event()

    def _find(self, browser, job):
        while True:
            for server in self.servers:
                if server.can_run(browser, job):
                    if server.lock.acquire(False):
                        return server

            self.server_ready.clear()
            self.server_ready.wait()

    @contextlib.contextmanager
    def for_job(self, browser, job):
        server = self._find(browser, job)

        yield server

        server.lock.release()
        self.server_ready.set()
