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

    subprocess.run([program_path, *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def start():
    execute("python", "src/server.py")


def lint():
    # execute("flake8", "src", "--max-line-length=120") TODO: fix flake8
    pass


def format():
    execute("black", "src")


def prepare():
    dependencies = [
        "mediapipe",
        "aiortc",
        "black",
        "flake8",
        "aiohttp",
        "opencv-python",
    ]

    if OS == "Windows" or OS == "Linux":
        dependencies.append("onnxruntime-gpu")
    else:
        dependencies.append("onnxruntime")

    execute("pip", "install", *dependencies)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "lint", "format", "prepare"])
    args = parser.parse_args()

    if args.command == "start":
        start()
    elif args.command == "lint":
        lint()
    elif args.command == "format":
        format()
    elif args.command == "prepare":
        prepare()
