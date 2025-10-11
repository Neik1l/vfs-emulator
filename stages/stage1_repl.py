import sys

VFS_NAME = "my_vfs"

USAGE = """Доступные команды:
  ls [path]      - заглушка: вывести имя команды и аргументы (0 или 1 аргумент)
  cd [path]      - заглушка: перейти (0 или 1 аргумент)
  exit           - выйти из программы
"""

def split_subcommands(line: str):
    # поддержка ';' и '&' как разделителей (выполняются последовательно)
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
        # пустая команда
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
        print(f"Ошибка: неизвестная команда '{cmd}'.")
        print(USAGE)

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

if __name__ == "__main__":
    print("Stage1: minimal VFS CLI prototype")
    repl()