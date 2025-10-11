# stages/stage3_vfs.py
from vfs.core import VFS, VFSNodeError
from vfs.utils import load_vfs_from_csv, split_subcommands, parse_cmd
# arg parsing, run_start_script, repl — но execute() будет вызывать VFS методы