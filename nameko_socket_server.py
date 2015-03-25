from functools import partial
import re

import eventlet
from nameko.extensions import ProviderCollector, SharedExtension, Entrypoint


SOCKET_SERVER_LISTEN_CONFIG_KEY = 'SOCKET_SERVER_LISTEN'
SOCKET_SERVER_LISTEN_RE = re.compile('^((?P<address>[^:]+):)?(?P<port>\d+)$')


class SocketServer(ProviderCollector, SharedExtension):

    def __init__(self):
        super(SocketServer, self).__init__()
        self._gt = None
        self._sock = None
        self._starting = False
        self._is_accepting = True
        self._provider_map = {}

    @property
    def bind_addr(self):
        listen_str = self.container.config.get(
            SOCKET_SERVER_LISTEN_CONFIG_KEY,
            '6000',
        )
        match = SOCKET_SERVER_LISTEN_RE.match(listen_str)
        if match is None:
            raise RuntimeError(
                'Misconfigured bind address `{}`. Should be `[address:]port`.'
            )
        address = match.group('address') or ''
        port = int(match.group('port'))

        return (address, port)

    def run(self):
        try:
            while self._is_accepting:
                sock, _ = self._sock.accept()
                self.container.spawn_managed_thread(
                    partial(self.handle_connection, sock),
                    protected=True,
                )
        finally:
            self._sock.close()

    def start(self):
        for provider in self._providers:
            self._provider_map[provider.command] = provider

        if not self._starting:
            self._starting = True
            self._sock = eventlet.listen(self.bind_addr)
            self._gt = self.container.spawn_managed_thread(
                self.run, protected=True)

    def stop(self):
        self._is_accepting = False
        self._gt.kill()
        super(SocketServer, self).stop()

    def handle_connection(self, sock):
        fd = sock.makefile('rw')

        while True:
            command = fd.readline().strip()

            if not command:
                break

            try:
                provider = self._provider_map[command]
            except KeyError:
                fd.write("unknown command `{}`".format(command))
                fd.flush()
                continue

            self.container.spawn_worker(
                provider, (), {}, handle_result=partial(
                    self.handle_result, fd)
                )
        sock.close()

    def handle_result(self, fd, worker_ctx, result, exc_info):
        if result is not None:
            fd.write(result)
        fd.flush()
        return result, exc_info


class SocketCommandHandler(Entrypoint):
    server = SocketServer()

    def __init__(self, command):
        self.command = command

    def setup(self):
        self.server.register_provider(self)

    def stop(self):
        self.server.unregister_provider(self)
        super(SocketCommandHandler, self).stop()


socket_command = SocketCommandHandler.decorator
