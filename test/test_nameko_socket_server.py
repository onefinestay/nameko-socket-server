import socket

import pytest

from nameko_socket_server import (
    SOCKET_SERVER_LISTEN_CONFIG_KEY, socket_command,
)


class Service(object):
    name = 'service'

    @socket_command('hello')
    def hello(self):
        return 'hello world'


def test_server(container_factory):
    config = {
        SOCKET_SERVER_LISTEN_CONFIG_KEY: '6000',
    }
    container = container_factory(Service, config)
    container.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('', 6000))
    sock.sendall('hello\n')
    data = sock.recv(1024)
    sock.close()
    assert data == 'hello world'
    container.stop()


def test_unknown_command(container_factory):
    config = {
        SOCKET_SERVER_LISTEN_CONFIG_KEY: '6000',
    }
    container = container_factory(Service, config)
    container.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('', 6000))
    sock.sendall('unknown\n')
    data = sock.recv(1024)
    sock.close()
    assert data == 'unknown command `unknown`'


def test_bad_config(container_factory):
    config = {
        SOCKET_SERVER_LISTEN_CONFIG_KEY: 'foo',
    }
    with pytest.raises(RuntimeError) as exc:
        container_factory(Service, config)
    assert 'Misconfigured bind address' in str(exc)
