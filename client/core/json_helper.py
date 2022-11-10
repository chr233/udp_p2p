
import json
from json import JSONDecodeError
from typing import Dict

from core.exceptions import P2PBaseException, PayloadParseError


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
    except UnicodeDecodeError:
        raise PayloadParseError('Payload can not decode to UTF-8')

    except JSONDecodeError:
        raise PayloadParseError('Payload can not decode to JSON')

    except Exception as e:
        if isinstance(e, P2PBaseException):
            raise e
        else:
            raise PayloadParseError('Payload parse error')
