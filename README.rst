nameko-socket-server
--------------------

Entrypoints for access via simple sockets

Usage
-----

.. code-block:: python

    from nameko_socket_server import socket_command

    class MyService(object):
        @socket_command('hello')
        def hello(self):
            return 'hello world'


.. code-block:: bash

    $ echo 'hello' | nc localhost 6000; echo
    hello world
