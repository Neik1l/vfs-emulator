# vfs/core.py
from pathlib import Path
import base64

class VFSNodeError(Exception):
    pass

class VFS:
    def __init__(self, name="default_vfs"):
        self.name = name
        self.root = {'type':'dir','children':{},'owner':'root','meta':{}}
        self.cwd = []

    def _split_path(self, path_str):
        # нормализация (реализация как в stage3_vfs.py)
        ...

    def add_from_row(self, path_str, typ, content=None, owner='root'):
        # добавление узла (реализация как раньше)
        ...

    def list_dir(self, path=None): ...
    def change_dir(self, path=None): ...
    def read_file(self, path): ...
    def chown(self, path, owner): ...
    def rmdir(self, path): ...