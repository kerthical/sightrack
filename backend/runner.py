import argparse
import os
import platform
import subprocess
import venv

VENV_DIR = ".venv"
OS = platform.system()


def execute(program_path, *args):
    if not os.path.exists(VENV_DIR):
        venv.create(VENV_DIR, with_pip=True, upgrade_deps=True)
        prepare()

    if OS == "Windows":
        program_path = os.path.join(VENV_DIR, "Scripts", program_path + ".exe")
    else:
        program_path = os.path.join(VENV_DIR, "bin", program_path)

    subprocess.run([program_path, *args], stderr=subprocess.DEVNULL)


def start():
    execute("python", "src/server.py")


def cli(*args):
    execute("python", "src/cli.py", *args)


def lint():
    execute("black", "src")
    pass


def prepare():
    dependencies = ["mediapipe", "aiortc", "black", "flake8", "aiohttp", "opencv-python"]

    if OS == "Windows" or OS == "Linux":
        dependencies.append("onnxruntime-gpu")
    else:
        dependencies.append("onnxruntime")

    execute("pip", "install", *dependencies)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, help="Command to execute")
    parser.add_argument("args", nargs="*", help="Arguments for command")
    args = parser.parse_args()

    if args.command == "start":
        start()
    elif args.command == "cli":
        cli(*args.args)
    elif args.command == "lint":
        lint()
    elif args.command == "prepare":
        prepare()
    else:
        parser.print_help()
