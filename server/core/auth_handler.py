
import os
from collections import Counter
from os import path
from socket import socket as Socket
from typing import Dict, Tuple, List

from core.exceptions import AuthenticationError
from core.utils import get_timestamp, log, get_time_str
from core.log_helper import LogHelper


class AuthHandler:
    '''Handler user login/logout'''

    attempts: int

    # store all devices info
    user_passwd_dict: Dict[str, str] = {}  # username : password

    # store online devices
    user_socket_dict: Dict[str, Socket] = {}  # username : socket
    socket_user_dict: Dict[Socket, str] = {}  # socket : username
    # store all online clients
    # username : (ip,udp_port,online since)
    online_client_dict: Dict[str, Tuple[str, int, int]] = {}

    # store all baned users and ips
    ban_dict: Dict[str, int] = {}  # ip/username : timestamp till unban
    # store all failed login tries
    failed_tries = Counter()  # ip/username : failed attempts

    # store all devices with its own id
    user_id_dict: Dict[str, int] = {}  # username : deviceID

    device_logger: LogHelper

    nextDeviceID: int = 1

    def __init__(self, base_path: str, attempts: int, logger: LogHelper):
        self.attempts = attempts
        self.device_logger = logger
        self.__load_users(base_path)

    def __load_users(self, base_path: str) -> None:
        auth_file = os.path.join(base_path, 'credentials.txt')
        self.user_passwd_dict = {}

        try:
            if not path.exists(auth_file):
                open(auth_file, 'a', encoding='utf-8').close()

            with open(auth_file, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    if not line:
                        continue

                    seps = line.strip().split(' ')
                    if len(seps) == 2:
                        user, passwd = seps
                        self.user_passwd_dict[user] = passwd

        except Exception as e:
            print(e)

    def auth(self, socket: Socket) -> str:
        '''get username if logined, else None'''
        user = self.socket_user_dict.get(socket, None)
        return user

    def __test_ban(self, target: str) -> bool:
        '''check if target is baned, True baned, False not baned'''
        if not target:
            return False

        if target in self.ban_dict:
            now = get_timestamp()
            if now > self.ban_dict[target]:
                self.failed_tries[target] = 0
                self.ban_dict.pop(target)
                return False
            else:
                return True
        else:
            return False

    def login(self, username: str, password: str, port: int, socket: Socket) -> str:
        '''user login, return token if success'''

        addr = socket.getpeername()
        ip = addr[0]

        if self.__test_ban(ip) or self.__test_ban(username):
            raise AuthenticationError(
                'Too many failed attempts, please try again later')

        if not username:
            self.increase_failed_count(None, ip)
            raise AuthenticationError('Device name can not be empty')

        elif username not in self.user_passwd_dict:
            self.increase_failed_count(username, ip)
            raise AuthenticationError(f'User {username} not exists')

        elif username in self.user_socket_dict:
            self.increase_failed_count(username, ip)
            raise AuthenticationError(f'User {username} already login')

        elif self.user_passwd_dict[username] != password:
            self.increase_failed_count(username, ip)
            raise AuthenticationError(
                f'Password incorrect error for user {username}')

        else:
            self.user_socket_dict[username] = socket
            self.socket_user_dict[socket] = username
            self.online_client_dict[username] = (ip, port, get_timestamp())

            self.failed_tries[username] = 0
            self.failed_tries[ip] = 0

            deviceID = 0
            if username not in self.user_id_dict:
                deviceID = self.nextDeviceID
                self.user_id_dict[username] = deviceID
                self.nextDeviceID += 1
            else:
                deviceID = self.user_id_dict[username]

            self.device_logger.log(
                deviceID, get_time_str(), username, ip, port
            )
            log(f'Edge device {username} online', addr, False)

            return username

    def logout(self, socket: Socket) -> str:
        '''user logout, return True if success'''
        username = self.auth(socket)

        if username:
            self.socket_user_dict.pop(socket, None)
            self.user_socket_dict.pop(username, None)
            addr = self.online_client_dict.pop(username, None)

            log(f'Edge device {username} offline', addr, False)
            return username
        else:
            return None

    def increase_failed_count(self, username: str, ip: str):
        if username:
            self.failed_tries[username] += 1
            self.failed_tries[ip] += 1
            if (self.failed_tries[ip] >= self.attempts or self.failed_tries[username] >= self.attempts):
                self.ban_dict[ip] = get_timestamp() + 5
                self.ban_dict[username] = get_timestamp() + 5
                raise AuthenticationError(
                    'Too many failed attempts, please try again later')

        else:
            self.failed_tries[ip] += 1
            if (self.failed_tries[ip] >= self.attempts):
                self.ban_dict[ip] = get_timestamp() + 5
                raise AuthenticationError(
                    'Too many failed attempts, please try again later')

    def count_online(self) -> int:
        count = len(self.online_client_dict.keys())
        return count

    def get_online_clients(self) -> List[Tuple[str, str, int, int]]:
        '''return [(device ip port timestamp), ...]'''
        result = []
        for device, data in self.online_client_dict.items():
            result.append((device, data[0], data[1], data[2]))
        return result
