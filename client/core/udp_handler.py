
import os
import time
from base64 import b64decode, b64encode
from socket import socket as Socket
from threading import Thread
from time import sleep
from typing import Dict, List, Tuple

from core.exceptions import (ArgumentError, FileIOError, FileParseError,
                             P2PBaseException, PayloadParseError,
                             UnsupportedCmdError)
from core.json_helper import json_2_dict
from core.payload_factory import PayloadFactory

CHUNK_SIZE = 40000


def println(msg: str, addr: Tuple[str, int] = None, error: bool = False):
    if addr:
        title = f'{addr[0]}:{addr[1]}'
        color = 32 if not error else 31
    else:
        title = 'Server'
        color = 34 if not error else 35

    print(f'[\033[{color}m {title} \033[0m] {msg}')


def random_str():
    return str(time.time())[-4:]


def read_file_content(file_path: str) -> Tuple[str, str]:
    with open(file_path, 'rb') as f:
        data = f.read()
        if len(data) > 50000:
            raise FileParseError('File is too large, can not send')

    body = b64encode(data).decode('utf-8')
    return body


def read_file_content_ex(file_path: str) -> Tuple[str, str]:
    with open(file_path, 'rb') as f:
        data = f.read()

    body = b64encode(data).decode('utf-8')
    return body


class UDPHandler():
    sock: Socket
    data_path: str
    base_path: str
    download_file: Dict[str, List[bytes]] = {}
    download_from: Dict[str, str] = {}
    file_cache: Dict[str, bytes] = {}

    def __init__(self, data_path: str, base_path: str, socket: Socket):
        self.data_path = data_path
        self.base_path = base_path
        self.sock = socket

    def download_from_peer(self, file_name: str, addr: Tuple[str, int], chunk: int):
        try:
            device = self.download_from[file_name]
            count = 5
            for i in range(3):
                for i in range(chunk):
                    if count < 0:
                        sleep(2)
                        count = 5
                    if not self.download_file[file_name][i]:
                        echo = random_str()
                        payload = PayloadFactory.request_dwn(
                            file_name, i, echo)
                        self.sock.sendto(payload, addr)
                        count -= 1

                check = True
                for content in self.download_file[file_name]:
                    if not content:
                        check = False
                        break

                if check:
                    break

            file_path = os.path.join(self.data_path, file_name)
            with open(file_path, 'wb')as f:
                body = ''.join(self.download_file[file_name])
                raw = b64decode(body)
                f.write(raw)

            println(
                f'Received {file_name} from {device}, save at {file_path}', addr, False)
            print('> ', end='')
        except Exception as e:
            println(
                f'Received {file_name} from {device} failed, {e}', addr, True)
            print('> ', end='')
        finally:
            self.download_file.pop(file_name, None)
            self.download_from.pop(file_name, None)
            self.file_cache.pop(file_name, None)

    def handle_message(self, raw: bytes, addr: Tuple[str, int]):
        try:
            response = None

            payload = json_2_dict(raw)

            # log(f'U IN  <-- {payload}', None, False)

            echo = payload['echo']

            if 'cmd' in payload:
                cmd = payload['cmd']
                if cmd == 'UVF':
                    file_name = payload['name']
                    port = payload['port']
                    chunk = payload['chunk']
                    device = payload['device']

                    if file_name not in self.download_file:
                        self.download_file[file_name] = [None] * chunk
                        self.download_from[file_name] = device

                        Thread(
                            target=self.download_from_peer,
                            args=(file_name, (addr[0], port), chunk)
                        ).start()

                elif cmd == 'DWN':
                    file_name = payload['name']
                    index = payload['i']

                    cache = None
                    if file_name not in self.file_cache:
                        file_path = None
                        file_path1 = os.path.join(self.base_path, file_name)
                        file_path2 = os.path.join(self.data_path, file_name)

                        if os.path.exists(file_path1):
                            file_path = file_path1
                        elif os.path.exists(file_path2):
                            file_path = file_path2
                        else:
                            raise FileIOError('File not exists')

                        cache = read_file_content_ex(file_path)
                        self.file_cache[file_name] = cache

                    else:
                        cache = self.file_cache[file_name]

                    chunk = len(cache) // CHUNK_SIZE

                    start = CHUNK_SIZE * index
                    end = start+CHUNK_SIZE-1 if index < chunk else len(cache)

                    response = PayloadFactory.response_dwn(
                        file_name, cache[start:end], index, echo)

                elif cmd == 'DWNR':
                    file_name = payload['name']
                    body = payload['body']
                    index = payload['i']

                    if file_name in self.download_file:
                        self.download_file[file_name][index] = body

                else:
                    raise UnsupportedCmdError('Bad Request')

            else:
                raise ArgumentError('Bad Request')

        except PayloadParseError as e:
            response = PayloadFactory.response_error(e, 'FAULT')

        except KeyError as e:
            err = PayloadParseError(f'Missing {e} in the payload')
            response = PayloadFactory.response_error(err, echo)

        except Exception as e:
            err = P2PBaseException('Internal Server Error')
            response = PayloadFactory.response_error(err, echo)

        finally:
            if response:
                # log(f'U OUT --> {response.decode("utf-8")}', None, False)
                return response
