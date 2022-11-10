
class P2PBaseException(Exception):
    '''P2PBaseException'''

    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self._m = msg

    @property
    def msg(self):
        return self._m


class PayloadParseError(P2PBaseException):
    '''Payload is invalid or unrecognized'''
    ...


class FileParseError(P2PBaseException):
    '''File missing or too large'''
    ...


class AuthenticationError(P2PBaseException):
    '''AuthenticationError'''
    ...


class ParamsInValidError(P2PBaseException):
    '''ParamsInValidError'''
    ...


class FileIOError(P2PBaseException):
    '''FileIOError'''
    ...


class ArgumentError(P2PBaseException):
    '''ArgumentError'''
    ...


class UnsupportedCmdError(P2PBaseException):
    '''UnsupportedCmdError'''
    ...
