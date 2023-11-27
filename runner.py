import argparse
import os
import platform
import subprocess
import venv

VENV_DIR = ".venv"
OS = platform.system()


def execute(program, *args):
    if not os.path.exists(VENV_DIR):
        venv.create(VENV_DIR, with_pip=True, upgrade_deps=True)
        setup()

    if OS == "Windows":
        program = os.path.join(VENV_DIR, "Scripts", program + ".exe")
    else:
        program = os.path.join(VENV_DIR, "bin", program)

    try:
        result = subprocess.run([program, *args], stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(result.stderr.decode("utf-8"))
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        pass


def run(*args):
    execute("python", "src/cli.py", *args)


def setup():
    dependencies = [
        "opencv-python",
        "filterpy",
        "rerun-sdk"
    ]

    if OS == "Windows" or OS == "Linux":
        dependencies.append("onnxruntime-gpu")
    else:
        dependencies.append("onnxruntime")

    execute("pip", "install", "-U", *dependencies)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, help="Command to execute")
    parser.add_argument("args", nargs="*", help="Arguments for command")
    args = parser.parse_args()

    if args.command == "run":
        run(*args.args)
    elif args.command == "setup":
        setup()
    else:
        parser.print_help()
