
from typing import List, Tuple
from core.exceptions import P2PBaseException
from core.utils import json_serializer


class PayloadFactory:
    # C/S CMD
    # Test
    @staticmethod
    def request_test(echo: str = ''):
        '''Test request'''
        jd = {'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_test(echo: str = ''):
        '''Test response'''
        jd = {'echo': echo}
        data = json_serializer(jd)
        return data

    # Auth
    @staticmethod
    def request_log(user: str, passwd: str, port: int, echo: str = ''):
        '''Login request'''
        jd = {'cmd': 'LOG', 'name': user,
              'pass': passwd, 'port': port, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_log(msg: str = 'OK', echo: str = ''):
        '''Login response'''
        jd = {'succ': True, 'msg': msg, 'echo': echo}
        data = json_serializer(jd)
        return data

    # UED
    @staticmethod
    def request_ued(fileID: int, body: str, echo: str = ''):
        '''UED request'''
        jd = {'cmd': 'UED', 'fid': fileID, 'body': body, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_ued(msg: str = 'OK', echo: str = ''):
        '''UED response'''
        jd = {'succ': True, 'msg': msg, 'echo': echo}
        data = json_serializer(jd)
        return data

    # SCS
    @staticmethod
    def request_scs(fileID: int, operator: str, echo: str = ''):
        '''SCS request'''
        jd = {'cmd': 'SCS', 'fid': fileID, 'op': operator, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_scs(msg: str = 'OK',  echo: str = ''):
        '''SCS response'''
        jd = {'succ': True, 'msg': msg, 'echo': echo}
        data = json_serializer(jd)
        return data

    # DTE
    @staticmethod
    def request_dte(fileID: int,  echo: str = ''):
        '''DTE request'''
        jd = {'cmd': 'DTE', 'fid': fileID, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_dte(msg: str = 'OK', echo: str = ''):
        '''DTE response'''
        jd = {'succ': True, 'msg': msg, 'echo': echo}
        data = json_serializer(jd)
        return data

    # AED
    @staticmethod
    def request_aed(echo: str = ''):
        '''AED request'''
        jd = {'cmd': 'AED', 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_aed(client: List[Tuple[str, str, int, int]], msg: str = 'OK', echo: str = ''):
        '''AED response'''
        jd = {'succ': True, 'client': client, 'msg': msg, 'echo': echo}
        data = json_serializer(jd)
        return data

    # OUT
    @staticmethod
    def request_out(echo: str = ''):
        '''OUT request'''
        jd = {'cmd': 'OUT', 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_out(msg: str = 'OK', echo: str = ''):
        '''OUT response'''
        jd = {'succ': True, 'msg': msg, 'echo': echo}
        data = json_serializer(jd)
        return data

    # P2P CMD
    # UVF
    @staticmethod
    def request_uvf(file_name: str, device: str, port: int, chunk: int, echo: str = ''):
        '''UVF request'''
        jd = {'cmd': 'UVF', 'name': file_name, 'device': device,
              'port': port, 'chunk': chunk, 'echo': echo}
        data = json_serializer(jd)
        return data

    # DWN
    @staticmethod
    def request_dwn(file_name: str, index: int, echo: str = ''):
        '''DWN request'''
        jd = {'cmd': 'DWN', 'name': file_name, 'i': index, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_dwn(file_name: str, body: str, index: int, echo: str = ''):
        '''DWN response'''
        jd = {'cmd': 'DWNR', 'name': file_name, 'body': body,
              'i': index, 'echo': echo}
        data = json_serializer(jd)
        return data

    # OTHER
    @staticmethod
    def request_oth(cmd: str, echo: str = ''):
        '''OTHER request'''
        jd = {'cmd': cmd, 'echo': echo}
        data = json_serializer(jd)
        return data

    # Other
    # ERROR
    @staticmethod
    def response_error(err: P2PBaseException, echo: str = ''):
        '''Error response'''
        name = err.__doc__ or str(err.__class__)
        jd = {'succ': False, 'msg': err.msg, 'error': name, 'echo': echo}
        data = json_serializer(jd)
        return data
