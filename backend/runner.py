import venv
import subprocess
import os
import platform
import sys


def main(program_path, *args):
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        venv.create(venv_dir, with_pip=True, upgrade_deps=True)

    current_os = platform.system()

    if current_os == "Windows":
        program_path = os.path.join(venv_dir, "Scripts", program_path + ".exe")
    else:
        program_path = os.path.join(venv_dir, "bin", program_path)

    subprocess.run([program_path, *args])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python runner.py <program> <args>")
        sys.exit(1)

    main(sys.argv[1], *sys.argv[2:])
