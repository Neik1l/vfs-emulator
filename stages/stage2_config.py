import sys
import argparse
from pathlib import Path

VFS_NAME = "default_vfs"

USAGE = """Доступные команды:
  ls [path], cd [path], exit
Поддерживаются разделители ';' и '&'.
"""

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

def handle_ls(args):
    if len(args) > 1:
        raise ValueError("ls: слишком много аргументов (ожидается 0 или 1).")
    print("COMMAND: ls")
    print("ARGUMENTS:", args)

def handle_cd(args):
    if len(args) > 1:
        raise ValueError("cd: слишком много аргументов (ожидается 0 или 1).")
    print("COMMAND: cd")
    print("ARGUMENTS:", args)

def execute_once(line: str):
    cmd, args = parse_cmd(line)
    if cmd is None:
        return
    if cmd == "ls":
        handle_ls(args)
    elif cmd == "cd":
        handle_cd(args)
    elif cmd == "exit":
        if args:
            print("exit: не ожидаются аргументы.")
            return
        print("Выход...")
        sys.exit(0)
    else:
        raise RuntimeError(f"Unknown command: {cmd}")

def run_start_script(script_path: Path):
    if not script_path.exists():
        print("Start script not found:", script_path)
        return
    with script_path.open(encoding='utf-8') as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip('\n')
            if not line.strip() or line.strip().startswith('#'):
                continue
            print(">>", line)
            subs = split_subcommands(line)
            for sc in subs:
                try:
                    execute_once(sc)
                except Exception as e:
                    print(f"[script line {lineno}] error in '{sc}': {e}")

def repl():
    while True:
        try:
            prompt = f"{VFS_NAME}> "
            line = input(prompt)
            subs = split_subcommands(line)
            if not subs:
                continue
            for sc in subs:
                try:
                    execute_once(sc)
                except Exception as e:
                    print("Ошибка выполнения команды:", e)
        except KeyboardInterrupt:
            print("\n(Нажмите 'exit' для выхода или Ctrl+D)")
        except EOFError:
            print("\nEOF — выход.")
            sys.exit(0)

def main():
    global VFS_NAME
    parser = argparse.ArgumentParser(description="Stage2 config + start script")
    parser.add_argument('--vfs', help='VFS name or path (stem used as VFS name)', default=None)
    parser.add_argument('--script', help='start script file', default=None)
    args = parser.parse_args()

    if args.vfs:
        VFS_NAME = Path(args.vfs).stem or Path(args.vfs).name

    print("CONFIG:")
    print("  VFS name:", VFS_NAME)
    print("  VFS path (provided):", args.vfs)
    print("  Start script:", args.script)
    print("-"*40)

    if args.script:
        run_start_script(Path(args.script))

    print("Starting REPL...")
    repl()

if __name__ == "__main__":
    main()