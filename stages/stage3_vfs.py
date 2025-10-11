#!/usr/bin/env python3
# stages/stage3_vfs.py
"""
Stage 3 — VFS from CSV (in-memory) + REPL.
CSV columns: path,type,content,owner
Commands: ls, cd, cat, chown, rmdir, exit
"""

import sys
import argparse
import csv
import base64
from pathlib import Path

class VFSNodeError(Exception):
    pass

class VFS:
    def __init__(self, name="default_vfs"):
        self.name = name
        self.root = {'type':'dir','children':{},'owner':'root','meta':{}}
        self.cwd = []

    def _split_path(self, path_str):
        if path_str is None or path_str == "":
            return list(self.cwd)
        s = str(path_str)
        if s.startswith('/'):
            parts = [p for p in s.strip('/').split('/') if p]
        else:
            base = '/'.join(self.cwd)
            combined = (base + '/' + s) if base else s
            parts = [p for p in combined.split('/') if p]
        res=[]
        for p in parts:
            if p=='.': continue
            if p=='..':
                if res: res.pop()
            else:
                res.append(p)
        return res

    def _get_node(self, parts):
        node = self.root
        for p in parts:
            if node['type'] != 'dir':
                return None
            node = node['children'].get(p)
            if node is None:
                return None
        return node

    def _ensure_parent(self, parts):
        if not parts:
            return self.root
        parent_parts = parts[:-1]
        node = self.root
        for p in parent_parts:
            ch = node['children'].get(p)
            if ch is None:
                node['children'][p] = {'type':'dir','children':{},'owner':'root','meta':{}}
                ch = node['children'][p]
            if ch['type'] != 'dir':
                raise VFSNodeError(f"Not a directory: {'/'.join(parent_parts)}")
            node = ch
        return node

    def add_from_row(self, path_str, typ, content=None, owner='root'):
        if not path_str:
            return
        p = path_str if path_str.startswith('/') else '/' + path_str
        parts = self._split_path(p)
        if not parts:
            return
        name = parts[-1]
        parent = self._ensure_parent(parts)
        if typ == 'dir':
            parent['children'][name] = {'type':'dir','children':{},'owner':owner,'meta':{}}
        elif typ == 'file':
            text = ''
            if content:
                if content.startswith('b64:'):
                    try:
                        b = base64.b64decode(content[4:])
                        text = b.decode('utf-8', errors='replace')
                    except Exception:
                        text = content
                else:
                    text = content
            parent['children'][name] = {'type':'file','content':text,'owner':owner,'meta':{}}
        else:
            raise VFSNodeError("Unknown type: " + str(typ))

    def list_dir(self, path=None):
        parts = self._split_path(path) if path is not None else list(self.cwd)
        node = self._get_node(parts)
        if node is None:
            raise VFSNodeError("No such directory: /" + "/".join(parts))
        if node['type'] != 'dir':
            raise VFSNodeError("Not a directory: /" + "/".join(parts))
        return node['children']

    def change_dir(self, path=None):
        parts = self._split_path(path) if path is not None else []
        node = self._get_node(parts)
        if node is None or node['type'] != 'dir':
            raise VFSNodeError("No such directory: /" + "/".join(parts))
        self.cwd = parts

    def read_file(self, path):
        parts = self._split_path(path)
        node = self._get_node(parts)
        if node is None:
            raise VFSNodeError("No such file: /" + "/".join(parts))
        if node['type'] != 'file':
            raise VFSNodeError("Not a file: /" + "/".join(parts))
        return node['content']

    def chown(self, path, owner):
        parts = self._split_path(path)
        node = self._get_node(parts)
        if node is None:
            raise VFSNodeError("No such path: /" + "/".join(parts))
        node['owner'] = owner

    def rmdir(self, path):
        parts = self._split_path(path)
        if not parts:
            raise VFSNodeError("Cannot remove root")
        parent_parts = parts[:-1]
        parent = self._get_node(parent_parts)
        if parent is None or parent['type'] != 'dir':
            raise VFSNodeError("No such directory")
        name = parts[-1]
        node = parent['children'].get(name)
        if node is None or node['type'] != 'dir':
            raise VFSNodeError("No such directory: /" + "/".join(parts))
        if node['children']:
            raise VFSNodeError("Directory not empty: /" + "/".join(parts))
        del parent['children'][name]

def load_vfs_from_csv(csv_path):
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    with p.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        if 'path' not in headers or 'type' not in headers:
            raise ValueError("CSV must contain 'path' and 'type' columns")
        vfs = VFS(name=p.stem)
        for lineno, row in enumerate(reader, start=2):
            path = (row.get('path') or '').strip()
            typ = (row.get('type') or 'file').strip()
            content = row.get('content') or ''
            owner = row.get('owner') or 'root'
            if not path:
                print(f"[csv line {lineno}] warning: empty path — skip")
                continue
            try:
                vfs.add_from_row(path, typ, content, owner)
            except Exception as e:
                print(f"[csv line {lineno}] error adding {path}: {e}")
        return vfs

def split_subcommands(line: str):
    parts=[]
    cur=""
    for ch in line:
        if ch in [';','&']:
            if cur.strip():
                parts.append(cur.strip())
            cur=""
        else:
            cur+=ch
    if cur.strip():
        parts.append(cur.strip())
    return parts

def parse_cmd(line: str):
    parts = line.strip().split()
    if not parts:
        return None, []
    return parts[0], parts[1:]

def execute(vfs, raw):
    cmd, args = parse_cmd(raw)
    if cmd is None:
        return
    if cmd == 'ls':
        if len(args) > 1:
            raise ValueError("ls: too many args (0 or 1 expected)")
        path = args[0] if args else None
        children = vfs.list_dir(path)
        for name,node in sorted(children.items()):
            s = '/' if node['type']=='dir' else ''
            print(f"{name}{s}\t{node['type']}\towner:{node.get('owner','?')}")
    elif cmd == 'cd':
        if len(args) > 1:
            raise ValueError("cd: too many args")
        path = args[0] if args else '/'
        vfs.change_dir(path)
    elif cmd == 'cat':
        if len(args) != 1:
            raise ValueError("cat requires one argument")
        print(vfs.read_file(args[0]))
    elif cmd == 'chown':
        if len(args) != 2:
            raise ValueError("chown requires path and owner")
        vfs.chown(args[0], args[1])
    elif cmd == 'rmdir':
        if len(args) != 1:
            raise ValueError("rmdir requires one argument")
        vfs.rmdir(args[0])
    elif cmd == 'exit':
        if args:
            raise ValueError("exit: no arguments allowed")
        print("Exiting...")
        sys.exit(0)
    else:
        raise RuntimeError(f"Unknown command: {cmd}")

def run_start_script(vfs, script_path):
    p = Path(script_path)
    if not p.exists():
        print("[start script] not found:", script_path)
        return
    print("[start script] executing:", script_path)
    with p.open(encoding='utf-8') as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip('\n')
            if not line.strip() or line.strip().startswith('#'):
                continue
            print(">>", line)
            subs = split_subcommands(line)
            for sc in subs:
                try:
                    execute(vfs, sc)
                except Exception as e:
                    print(f"[script line {lineno}] error in '{sc}': {e}")

def repl(vfs):
    while True:
        try:
            cwd = '/' if not vfs.cwd else '/' + '/'.join(vfs.cwd)
            prompt = f"[{vfs.name}:{cwd}]> "
            line = input(prompt)
            subs = split_subcommands(line)
            if not subs:
                continue
            for sc in subs:
                try:
                    execute(vfs, sc)
                except Exception as e:
                    print("Error:", e)
        except KeyboardInterrupt:
            print("\n(Press 'exit' or Ctrl+D to quit)")
        except EOFError:
            print("\nEOF — exit")
            sys.exit(0)
        except Exception as e:
            print("Internal REPL error:", e)

def main():
    parser = argparse.ArgumentParser(description="Stage3: VFS from CSV (in-memory) + REPL")
    parser.add_argument('--vfs', help='CSV file: path,type,content,owner', default=None)
    parser.add_argument('--script', help='start script file', default=None)
    args = parser.parse_args()

    if args.vfs:
        try:
            vfs = load_vfs_from_csv(args.vfs)
        except FileNotFoundError as e:
            print("Error loading VFS:", e)
            sys.exit(2)
        except ValueError as e:
            print("CSV format error:", e)
            sys.exit(2)
        except Exception as e:
            print("Unexpected error loading VFS:", e)
            sys.exit(2)
    else:
        vfs = VFS("default_vfs")

    print("CONFIG:")
    print("  VFS name:", vfs.name)
    print("  VFS source:", args.vfs)
    print("  Start script:", args.script)
    print("-"*40)

    if args.script:
        run_start_script(vfs, args.script)

    repl(vfs)

if __name__ == '__main__':
    main()