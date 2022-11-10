
import os
import socket
import struct
import sys
from random import randint
from socket import socket as Socket
from threading import Thread

from core.exceptions import ArgumentError, FileIOError, P2PBaseException
from core.payload_factory import PayloadFactory
from core.udp_handler import CHUNK_SIZE, UDPHandler
from core.utils import (json_deserializer, package_file, package_file_ex,
                        random_str)

LISTEN_ON = '0.0.0.0'

RECV_BYTES = 65535

CMDS = ('EDG', 'UED', 'SCS', 'DTE', 'AED', 'OUT', 'UVF', 'HLP')

OPS = ('SUM', 'AVERAGE', 'MAX', 'MIN')

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_PATH, 'data')

TCP_SOCK: Socket
UDP_SOCK: Socket

DEVICE_NAME: str


def log(msg: str,  error: bool = False):
    '''Logging'''
    title = 'Client'
    color = 32 if not error else 31
    print(f'\r[\033[{color}m {title} \033[0m] {msg}')


def logcmd(msg: str, error: bool = False):
    '''Logging cmd result'''
    color = 34 if not error else 31
    title = 'Result' if not error else 'Error'
    sep = '<'
    for line in msg.split('\n'):
        print(f'\033[{color}m$ {title.center(6)} \033[0m{sep} {line}')
        title = ''
        sep = ' '


def ipt(device: str):
    '''Input text'''
    while True:
        txt = input(f'\033[32m$ {device.center(6)} \033[0m> ')
        if txt:
            return txt


def convert_int(string: str, key: str):
    try:
        return int(string)
    except ValueError:
        raise ArgumentError(f'Invalid argument {key}')


def init_udp_socket(port) -> bool:
    global UDP_SOCK

    UDP_SOCK = Socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        host = LISTEN_ON
        UDP_SOCK.bind((host, port))
        log(f'UDP server started on {host}:{port}', False)
        Thread(target=udp_server, daemon=True).start()
        return True
    except OSError as s:
        log(f'UDP server start error: {s}', None, True)
        return False


def udp_server():

    udp_handler = UDPHandler(DATA_PATH, BASE_PATH, UDP_SOCK)

    while True:
        try:
            data, addr = UDP_SOCK.recvfrom(RECV_BYTES)
            response = udp_handler.handle_message(data, addr)
            if response:
                UDP_SOCK.sendto(response, addr)
        except Exception:
            ...


def init_tcp_socket(host, port):
    global TCP_SOCK

    while True:
        try:
            TCP_SOCK = Socket(socket.AF_INET, socket.SOCK_STREAM)
            TCP_SOCK.setblocking(True)
            TCP_SOCK.connect((host, port))
            log(f'Connected to server {host} {port}', False)

            request = PayloadFactory.request_test('test')
            send_tcp(request)

            data = recv_tcp()

            if data == b'{"echo": "test"}':
                log('Server test ok', False)
                return
            else:
                log('Server test failed, reset socket', True)

        except OSError as e:
            log(f'TCP error: {e}',  True)


def send_tcp(data: bytes):
    msg_len = struct.pack('>i', len(data))
    TCP_SOCK.send(msg_len+data)


def recv_tcp() -> bytes:
    raw = TCP_SOCK.recv(4)
    msg_len, = struct.unpack('>i', raw)
    data = TCP_SOCK.recv(msg_len)
    return data


def recv_tcp_json() -> bytes:
    raw = recv_tcp()
    return json_deserializer(raw)


def interactive_login(port: int):
    global DEVICE_NAME
    while True:
        devicename = ipt('Enter device name:')
        password = ipt('Enter password:')
        request = PayloadFactory.request_log(
            devicename, password, port, random_str()
        )
        send_tcp(request)
        jd = recv_tcp_json()
        msg = jd.get('msg', 'Server Error')
        succ = jd.get('succ', False)
        log(msg, not succ)
        if succ:
            DEVICE_NAME = devicename
            return


def interactive_commdline(my_port: int) -> str:
    '''Interactive register'''

    device = DEVICE_NAME

    while True:
        print()
        log('Avilable commands:' + ', '.join(CMDS), False)

        user_input = ipt(device)
        args = user_input.split(' ')

        if len(args) == 0:
            continue

        cmd = args[0]
        args = args[1:]

        echo = random_str()

        try:
            if cmd == 'EDG':
                if len(args) < 2:
                    raise ArgumentError('Usage EDG <file id> <count>')

                fileID = convert_int(args[0], 'fileID')
                count = convert_int(args[1], 'count')
                if fileID < 1:
                    raise ArgumentError('FileID must > 1')

                if count < 1:
                    raise ArgumentError('FileID must > 1')

                try:
                    file_name = f'{device}-{fileID}.txt'
                    file_path = os.path.join(DATA_PATH, file_name)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for _ in range(count):
                            f.write(str(randint(1000, 9999))+'\n')
                except Exception as e:
                    raise FileIOError('File write error')

                logcmd(f'File {file_name} generated done', False)

            elif cmd == 'UED':
                if len(args) < 1:
                    raise ArgumentError('Usage UED <file id>')

                fileID = convert_int(args[0], 'fileID')
                if fileID < 1:
                    raise ArgumentError('FileID must > 1')

                file_name = f'{device}-{fileID}.txt'
                file_path = os.path.join(DATA_PATH, file_name)

                if not os.path.exists(file_path):
                    raise FileIOError('File not exists')

                body = package_file(file_path)
                payload = PayloadFactory.request_ued(fileID, body, echo)

                send_tcp(payload)
                jd = recv_tcp_json()

                error = not jd.get('succ', False)
                msg = jd.get('msg', 'Server Error')
                logcmd(msg, error)

            elif cmd == 'SCS':
                if len(args) < 2:
                    raise ArgumentError(
                        'Usage SCS <file id> <computation operation>')

                fileID = convert_int(args[0], 'fileID')
                if fileID < 1:
                    raise ArgumentError('FileID must > 1')

                op = args[1]
                if op not in OPS:
                    raise ArgumentError(
                        'Invalid operation, avilable: SUM,AVERAGE,MAX,MIN')

                payload = PayloadFactory.request_scs(fileID, op, echo)

                send_tcp(payload)
                jd = recv_tcp_json()

                error = not jd.get('succ', False)
                msg = jd.get('msg', 'Server Error')
                logcmd(msg, error)

            elif cmd == 'DTE':
                if len(args) < 1:
                    raise ArgumentError('Usage DTE <file id>')

                fileID = convert_int(args[0], 'fileID')
                if fileID < 1:
                    raise ArgumentError('FileID must > 1')

                payload = PayloadFactory.request_dte(fileID, echo)

                send_tcp(payload)
                jd = recv_tcp_json()

                error = not jd.get('succ', False)
                msg = jd.get('msg', 'Server Error')
                logcmd(msg, error)

            elif cmd == 'AED':
                payload = PayloadFactory.request_aed(echo)

                send_tcp(payload)
                jd = recv_tcp_json()

                error = not jd.get('succ', False)
                msg = jd.get('msg', 'Server Error')
                clients = jd.get('client', [])

                if not error:
                    if len(clients) == 0:
                        msg = 'No client online'
                    else:
                        data = ['Online clients:']
                        for d, ip, port, ts in clients:
                            data.append(
                                f'{d}; {ip}; {port}; active since {ts}')
                logcmd(msg, error)

            elif cmd == 'OUT':
                payload = PayloadFactory.request_out(echo)

                send_tcp(payload)
                jd = recv_tcp_json()

                error = not jd.get('succ', False)
                msg = jd.get('msg', 'Server Error')
                clients = jd.get('clients', [])
                logcmd(msg, error)
                return

            elif cmd == 'UVF':
                if len(args) < 2:
                    raise ArgumentError('Usage UVF <device name> <file name>')

                device_name = args[0]
                file_name = args[1]

                file_path = None
                file_path1 = os.path.join(BASE_PATH, file_name)
                file_path2 = os.path.join(DATA_PATH, file_name)

                if os.path.exists(file_path1):
                    file_path = file_path1
                elif os.path.exists(file_path2):
                    file_path = file_path2
                else:
                    raise FileIOError('File not exists')

                payload = PayloadFactory.request_aed(echo)

                send_tcp(payload)
                jd = recv_tcp_json()

                error = not jd.get('succ', False)

                if error:
                    msg = jd.get('msg', 'Server Error')
                    logcmd(msg, error)

                clients = jd.get('client', [])

                target_addr = None
                for d, ip, port, ts in clients:
                    if d == device_name:
                        target_addr = (ip, port)
                        break

                if not target_addr:
                    logcmd(f'Device {device_name} not found', True)
                else:
                    body = package_file_ex(file_path)
                    chunk = len(body) // CHUNK_SIZE + 1

                    payload = PayloadFactory.request_uvf(
                        file_name, DEVICE_NAME, my_port, chunk, echo)
                    UDP_SOCK.sendto(payload, target_addr)
                    UDP_SOCK.sendto(payload, target_addr)
                    logcmd(f'Sending file {file_name} to {device_name}', False)

            else:
                payload = PayloadFactory.request_oth(cmd, echo)
                send_tcp(payload)
                jd = recv_tcp_json()
                error = not jd.get('succ', False)
                msg = jd.get('msg', 'Server Error')
                logcmd(msg, error)

        except P2PBaseException as e:
            log(e, True)


if __name__ == '__main__':
    try:
        args = sys.argv[1:]

        if len(args) < 3:
            log('Missing arguments', None, True)
            raise ValueError

        server_ip, server_port, client_port, *_ = args
        try:
            server_port = int(server_port)
            client_port = int(client_port)
        except ValueError as e:
            log('Arguments type invalid', None, True)
            raise e

        if not 0 < server_port <= 65535:
            log('Server_port is invalid (0,65535]', None, True)
            raise ValueError

        if client_port == -1:
            client_port = randint(10000, 60000)

        if not 0 < client_port <= 65535:
            log('client_port is invalid [1,5]', None, True)
            raise ValueError

    except ValueError:
        log('Usage: python3 client.py <server ip> <server port> <client udp server port>', None, True)
        input('Press enter to exit...')
        exit(1)

    try:
        if not init_udp_socket(client_port):
            log('Maybe port is already in use, please use another port',  True)
            exit()

        if not os.path.exists(DATA_PATH):
            os.mkdir(DATA_PATH)
        else:
            for name in os.listdir(DATA_PATH):
                file_path = os.path.join(DATA_PATH, name)
                os.remove(file_path)

        while True:
            try:
                init_tcp_socket(server_ip, server_port)
                print()
                interactive_login(client_port)
                interactive_commdline(client_port)

            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                log(e, True)
            finally:
                print()

    except KeyboardInterrupt:
        print()
        log('Client shutdown ...', False)
        exit()
