import os
from io import TextIOBase


class LogHelper():
    file_handler: TextIOBase = None

    def __init__(self, base_path, file_name) -> None:
        file_path = os.path.join(base_path, file_name)
        self.file_handler = open(file_path, 'w', encoding='utf-8')

    def log(self, *msg):
        msg = [str(x) for x in msg]
        string = '; '.join(msg) + '\n'
        self.file_handler.write(string)
        self.file_handler.flush()

    def __del__(self):
        self.file_handler.close()
