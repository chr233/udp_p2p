
import os
import select
import socket
import sys
from queue import Empty, Queue
from socket import socket as Socket
from typing import Dict, List, Tuple
import struct

from core.tcp_handler import TCPHandler


LISTEN_ON = '0.0.0.0'

RECV_BYTES = 10240


def println(msg: str, addr: Tuple[str, int] = None, error: bool = False):
    if addr:
        title = f'{addr[0]}:{addr[1]}'
        color = 32 if not error else 31
    else:
        title = 'Server'
        color = 34 if not error else 35

    print(f'[\033[{color}m {title} \033[0m] {msg}')


def main(port, attempts):
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Init TCP server
    tcp_socket = Socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 10)
    tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    tcp_socket.setblocking(False)
    try:
        host = LISTEN_ON
        tcp_socket.bind((host, port))
        tcp_socket.listen(10)
        println(f'TCP server listening on {host}:{port}', None, False)
    except OSError as s:
        println(f'TCP server start error: {s}', None, True)
        return

    # Init TCPHandler
    tcp_handler = TCPHandler(base_path, attempts)

    println('Wating for clients ...', None, False)

    # Event loop
    try:
        inputs: List[Socket] = [tcp_socket, ]
        outputs: List[Socket] = []
        msg_queue: Dict[Socket, Queue] = {}

        auth_handler = tcp_handler.auth_handler

        while True:
            rlist, wlist, elist = select.select(inputs, outputs, inputs, 1)
            for s in rlist:
                # any socket is ready for reading
                if s == tcp_socket:
                    # TCP incoming connection
                    conn, addr = s.accept()
                    conn.setblocking(False)

                    inputs.append(conn)
                    msg_queue[conn] = Queue()

                    println('TCP connection established', addr, False)

                else:
                    try:
                        addr = s.getpeername()
                        data = s.recv(4)

                        if data and len(data) == 4:
                            msg_len, = struct.unpack('>i', data)
                            data = s.recv(msg_len)

                            # log(f'TCP in {data}', addr, False)

                            # TCP message
                            response = tcp_handler.handle_message(data, s)

                            msg_len = struct.pack('>i', len(response))

                            msg_queue[s].put(msg_len+response)
                            if s not in outputs:
                                outputs.append(s)

                        else:
                            # TCP close
                            println('TCP connection closed', addr, False)

                            if s in outputs:
                                outputs.remove(s)
                            inputs.remove(s)
                            msg_queue.pop(s, None)
                            auth_handler.logout(s)
                            s.close()

                    except Exception as e:
                        println(e, addr, True)
                        try:
                            if s in outputs:
                                outputs.remove(s)
                            inputs.remove(s)
                            msg_queue.pop(s, None)
                            auth_handler.logout(s)
                            s.close()
                        except Exception:
                            ...

            for s in wlist:
                # any socket is ready for writing
                try:
                    payload = msg_queue[s].get_nowait()
                except Empty:
                    outputs.remove(s)
                except KeyError:
                    pass
                else:
                    s.send(payload)

            for s in elist:
                # any socket raises error
                println('TCP connection error', None, True)

                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)

                msg_queue.pop(s, None)
                auth_handler.logout(s)
                s.close()

    except KeyboardInterrupt:
        pass
    finally:
        tcp_socket.close()
        println('Server shutdown ...', None, True)


if __name__ == '__main__':
    try:
        args = sys.argv[1:]

        if len(args) < 2:
            println('Missing arguments', None, True)
            raise ValueError

        port, attempts, *_ = args
        try:
            port = int(port)
            attempts = int(attempts)
        except ValueError as e:
            println('Arguments type invalid', None, True)
            raise e

        if not 0 < port <= 65535:
            println('Server_port is invalid (0,65535]', None, True)
            raise ValueError
        if not 1 <= attempts <= 5:
            println('Number_of_consecutive_failed_attempts is invalid [1,5]',
                None, True)
            raise ValueError

    except ValueError:
        println('Usage: python3 server.py <server port> <number of consecutive failed attempts>', None, True)
        input('Press enter to exit...')
        exit(1)

    main(port, attempts)
