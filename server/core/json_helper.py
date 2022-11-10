
import json
import os
import time
from base64 import b64encode
from json import JSONDecodeError
from typing import Dict, Tuple

from core.exceptions import FileParseError, P2PBaseException, PayloadParseError


def dict_2_json(obj: dict) -> bytes:
    jd = json.dumps(obj)
    raw = jd.encode('utf-8')
    return raw


def json_2_dict(data: bytes) -> Dict[str, str]:
    try:
        raw = data.decode('utf-8')
        jd = json.loads(raw)
        if not isinstance(jd, dict):
            raise PayloadParseError('Payload invalid')
        elif 'echo' not in jd:
            raise PayloadParseError('Missing echo in the payload')
        return jd

    except Exception as e:
        if isinstance(e, P2PBaseException):
            raise e
        else:
            raise PayloadParseError('Payload parse error')
