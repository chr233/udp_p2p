
import os
import time
from base64 import b64decode
from socket import socket as Socket
from typing import List, Tuple

from core.auth_handler import AuthHandler
from core.exceptions import (ArgumentError, AuthenticationError,
                             FileParseError, P2PBaseException,
                             PayloadParseError, UnsupportedCmdError)
from core.json_helper import json_2_dict
from core.log_helper import LogHelper
from core.payload_fatory import PayloadFactory

CMD_USAGE = {
    'EDG': 'Usage: EDG fileID count',
    'UED': 'Usage: UED fileID',
    'SCS': 'Usage: SCS fileID computationOperation',
    'DTE': 'Usage: DTE fileID',
    'AED': 'Usage: AED',
    'OUT': 'Usage: OUT',
}

CMDS = CMD_USAGE.keys()

OPS = ('SUM', 'AVERAGE', 'MAX', 'MIN')


def get_localtime():
    return time.strftime("%d %B %Y %H:%M:%S", time.localtime())


def println(msg: str, addr: Tuple[str, int] = None, error: bool = False):
    if addr:
        title = f'{addr[0]}:{addr[1]}'
        color = 32 if not error else 31
    else:
        title = 'Server'
        color = 34 if not error else 35

    print(f'[\033[{color}m {title} \033[0m] {msg}')


class TCPHandler():
    auth_handler: AuthHandler
    upload_logger: LogHelper
    detetion_logger: LogHelper
    data_path: str

    def __init__(self, base_path: str, attempts: int):
        log_path = os.path.join(base_path, 'logs')
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        self.upload_logger = LogHelper(log_path, 'upload-log.txt')
        self.detetion_logger = LogHelper(log_path, 'deletion-log.txt')

        device_logger = LogHelper(log_path, 'edge-device-log.txt')

        self.auth_handler = AuthHandler(base_path, attempts, device_logger)

        self.data_path = os.path.join(base_path, 'data')
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)
        else:
            for name in os.listdir(self.data_path):
                file_path = os.path.join(self.data_path, name)
                os.remove(file_path)

    def handle_message(self, raw: bytes, socket: Socket):
        try:
            response = None
            payload = json_2_dict(raw)
            echo = payload['echo']

            addr = socket.getpeername()
            # log(f'T IN  <-- {payload}', addr, False)

            device = self.auth_handler.auth(socket)

            if 'cmd' not in payload:  # Test
                response = PayloadFactory.response_test(echo)

            else:
                if not device:  # not login, login first
                    device = payload['name']
                    password = payload['pass']
                    port = payload['port']

                    if self.auth_handler.login(device, password, port, socket):
                        response = PayloadFactory.response_log(
                            f'You\'re now login as {device}', echo)

                else:  # loged in
                    cmd = payload['cmd']

                    if cmd == 'UED':
                        fileID = payload['fid']
                        body = payload['body']

                        file_name = f'{device}-{fileID}.txt'
                        file_path = os.path.join(self.data_path, file_name)

                        if os.path.exists(file_path):
                            raise FileParseError(
                                f'File {file_name} already exists')

                        try:
                            raw = b64decode(body.encode('utf-8'))
                        except Exception:
                            raise FileParseError(
                                f'File {file_name} content decode error')

                        try:
                            with open(file_path, 'wb') as f:
                                f.write(raw)
                        except Exception:
                            raise FileParseError(
                                f'Can not write file {file_name}')

                        length = 0
                        try:
                            with open(file_path, 'r', encoding='utf-8')as f:
                                length = len(f.readlines())
                        except Exception:
                            raise FileParseError(
                                f'Parse file {file_name} error')

                        self.upload_logger.log(
                            device, get_localtime(), fileID, length
                        )

                        result = f'Successfully uploaded file {file_name}'
                        response = PayloadFactory.response_ued(result, echo)

                        println(f'{device} issued {cmd} command', addr, False)
                        println(
                            f'successful received file {file_name} from {device}', addr, False)

                    elif cmd == 'SCS':
                        fileID = payload['fid']
                        op = payload['op']

                        if op not in OPS:
                            raise ArgumentError(
                                f'Computation operation invalid, avilable: SUM,AVERAGE,MAX,MIN'
                            )

                        file_name = f'{device}-{fileID}.txt'
                        file_path = os.path.join(self.data_path, file_name)

                        if not os.path.exists(file_path):
                            raise FileParseError(
                                f'File {file_name} not exists')

                        nums: List[int] = []
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    nums.append(int(line.strip()))
                                except Exception:
                                    pass

                        value = 0
                        if op == 'SUM':
                            value = sum(nums)*1.0

                        elif op == 'AVERAGE':
                            value = sum(nums) * 1.0 / len(nums)

                        elif op == 'MAX':
                            value = max(nums)*1.0

                        elif op == 'MIN':
                            value = min(nums)*1.0

                        msg = f'Computation {op} result on the file {fileID} returned from the server is: {value}'
                        println(
                            f'{op} computation has been made on edge device {device} data file {fileID}, the result is {value}', addr, False)

                        response = PayloadFactory.response_scs(
                            msg, echo)

                        println(f'{device} issued {cmd} command', addr, False)

                    elif cmd == 'DTE':
                        fileID = payload['fid']

                        file_name = f'{device}-{fileID}.txt'
                        file_path = os.path.join(self.data_path, file_name)

                        if not os.path.exists(file_path):
                            raise FileParseError(
                                f'File {file_name} not exists')

                        length = 0
                        try:
                            with open(file_path, 'r', encoding='utf-8')as f:
                                length = len(f.readlines())
                        except Exception:
                            raise FileParseError(
                                f'Parse file {file_name} error')

                        try:
                            os.remove(file_path)
                        except Exception:
                            raise FileParseError(
                                f'Can not delete file {file_name}')

                        self.detetion_logger.log(
                            device, get_localtime(), fileID, length
                        )

                        result = f'Successfully deleted file {file_name}'
                        response = PayloadFactory.response_ued(result, echo)

                        println(f'{device} issued {cmd} command', addr, False)
                        println(
                            f'successful delete file {file_name} for {device}', addr, False
                        )

                    elif cmd == 'AED':
                        all_clients = self.auth_handler.get_online_clients()

                        clients = []
                        for d, ip, port, ts in all_clients:
                            if d != device:
                                clients .append((d, ip, port, ts))

                        response = PayloadFactory.response_aed(
                            clients, '', echo)

                        println(f'{device} issued {cmd} command', addr, False)

                    elif cmd == 'OUT':
                        self.auth_handler.logout(socket)
                        msg = 'You are now logout successfully'

                        response = PayloadFactory.response_out(msg, echo)

                        println(f'{device} issued {cmd} command', addr, False)

                    else:
                        u_cmd = cmd.upper()
                        if u_cmd in CMD_USAGE:
                            raise ArgumentError(CMD_USAGE[u_cmd])
                        else:
                            raise UnsupportedCmdError(f'Unknown cmd {cmd}')

        except PayloadParseError as e:
            response = PayloadFactory.response_error(e, 'FAULT')

        except KeyError as e:
            err = ArgumentError(f'Missing {e} in the payload')
            response = PayloadFactory.response_error(err, echo)

        except AuthenticationError as e:
            println(e.msg, addr, True)
            response = PayloadFactory.response_error(e, echo)

        except P2PBaseException as e:
            response = PayloadFactory.response_error(e, echo)

        except Exception as e:
            println(e, addr, True)
            err = P2PBaseException('Internal Server Error')
            response = PayloadFactory.response_error(err, echo)

        finally:
            if not response:
                err = P2PBaseException('Internal Server Error')
                response = PayloadFactory.response_error(err, echo)

            # log(f'T OUT --> {response.decode("utf-8")}', addr, False)
            return response
