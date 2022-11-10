
import json
import time
from base64 import b64encode
from json import JSONDecodeError
from typing import Dict, Tuple

from core.exceptions import FileParseError, P2PBaseException, PayloadParseError


def random_str():
    ts = str(time.time())[-4:]
    return ts


def get_timestamp():
    return int(time.time())


def get_time_str():
    return time.strftime("%d %B %Y %H:%M:%S", time.localtime())


def package_file(file_path: str) -> Tuple[str, str]:
    with open(file_path, 'rb') as f:
        data = f.read()
        if len(data) > 50000:
            raise FileParseError('File is too large, can not send')

    body = b64encode(data).decode('utf-8')
    return body


def package_file_ex(file_path: str) -> Tuple[str, str]:
    with open(file_path, 'rb') as f:
        data = f.read()

    body = b64encode(data).decode('utf-8')
    return body


def log(msg: str, addr: Tuple[str, int] = None, error: bool = False):
    if addr:
        title = f'{addr[0]}:{addr[1]}'
        color = 32 if not error else 31
    else:
        title = 'Client'
        color = 34 if not error else 35

    print(f'[\033[{color}m {title} \033[0m] {msg}')


def json_serializer(obj: dict) -> bytes:
    jd = json.dumps(obj)
    raw = jd.encode('utf-8')
    return raw


def json_deserializer(data: bytes) -> Dict[str, str]:
    try:
        raw = data.decode('utf-8')
        jd = json.loads(raw)
        if not isinstance(jd, dict):
            raise PayloadParseError('Payload invalid')
        elif 'echo' not in jd:
            raise PayloadParseError('Missing echo in the payload')
        return jd
    except UnicodeDecodeError:
        raise PayloadParseError('Payload can not decode to UTF-8')

    except JSONDecodeError:
        raise PayloadParseError('Payload can not decode to JSON')

    except Exception as e:
        if isinstance(e, P2PBaseException):
            raise e
        else:
            raise PayloadParseError('Payload parse error')
