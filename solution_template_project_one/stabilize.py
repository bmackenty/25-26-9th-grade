#!/usr/bin/env python3
"""
stabilize_env.py

Run this at the start of class to make sure:

- You are in the correct folder (the one with app.py).
- A virtual environment exists in ./venv (create it if missing).
- Flask (and anything in requirements.txt) is installed into that venv.
- You get clear instructions on how to activate the venv and run the app.

Usage (in the project folder):
    python3 stabilize_env.py
"""

import os
import sys
import subprocess
import shutil
from textwrap import dedent

PROJECT_MARKERS = ["app.py"]          # files that must exist in the correct folder
VENV_DIR = "venv"                     # name of the virtual environment folder
REQUIREMENTS_FILE = "requirements.txt"


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def fail(msg: str) -> None:
    print(f"\n[ERROR] {msg}")
    print("Fix the issue, then run: python3 stabilize_env.py again.")
    sys.exit(1)


def run(cmd, python=False):
    """
    Run a command and return its stdout as text.
    If python=True, show it as a Python command in the logs.
    """
    display = " ".join(cmd)
    print(f"\n> {display}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    if result.returncode != 0:
        print(result.stdout)
        fail(f"Command failed: {display}")
    print(result.stdout.strip())
    return result.stdout.strip()


def find_system_python() -> str:
    """
    Try to find a suitable system Python (python3 preferred).
    """
    for name in ("python3", "python"):
        path = shutil.which(name)
        if path:
            return path
    fail("Could not find python3 or python on this system.")


def get_venv_python() -> str:
    """
    Return the path to the python executable inside the venv.
    Handles macOS/Linux and Windows.
    """
    # macOS / Linux
    candidate = os.path.join(VENV_DIR, "bin", "python")
    if os.path.exists(candidate):
        return candidate

    # Windows
    candidate = os.path.join(VENV_DIR, "Scripts", "python.exe")
    if os.path.exists(candidate):
        return candidate

    fail("Could not find the venv Python interpreter. Something is wrong with the venv.")


def check_in_correct_folder() -> None:
    """
    Ensure the student is in the correct project directory.
    """
    print_header("Step 1: Checking current folder")

    missing = [f for f in PROJECT_MARKERS if not os.path.exists(f)]
    if missing:
        print("You are NOT in the correct folder.")
        print("This script expects to find these files here:")
        for f in PROJECT_MARKERS:
            print(f"  - {f}")
        print("\nCurrent working directory:")
        print(f"  {os.getcwd()}")
        fail(
            "Use 'cd' in your terminal to move into the folder that contains app.py, "
            "then run this script again."
        )
    else:
        print("Good: app.py found. You are in the correct project folder.")


def ensure_venv_exists(system_python: str) -> None:
    """
    Create ./venv if it does not exist.
    """
    print_header("Step 2: Checking virtual environment (venv)")

    if os.path.isdir(VENV_DIR):
        print(f"Virtual environment '{VENV_DIR}' already exists. Good.")
        return

    print(f"Virtual environment '{VENV_DIR}' not found. Creating it now...")
    run([system_python, "-m", "venv", VENV_DIR])
    print(f"Created virtual environment in ./{VENV_DIR}")


def install_dependencies(venv_python: str) -> None:
    """
    Upgrade pip and install packages into the venv.
    Priority:
    - If requirements.txt exists, install from there.
    - Otherwise, ensure Flask is installed.
    """
    print_header("Step 3: Installing / checking dependencies")

    print("Upgrading pip in the virtual environment...")
    run([venv_python, "-m", "pip", "install", "--upgrade", "pip"])

    if os.path.exists(REQUIREMENTS_FILE):
        print(f"Found {REQUIREMENTS_FILE}. Installing required packages...")
        run([venv_python, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    else:
        print(f"No {REQUIREMENTS_FILE} found. Ensuring Flask is installed...")
        # Try to import flask; if that fails, install it.
        code = "import importlib; print(importlib.util.find_spec('flask') is not None)"
        result = run([venv_python, "-c", code])
        if result.strip() == "True":
            print("Flask is already installed in this venv. Good.")
        else:
            print("Flask not found in venv. Installing flask...")
            run([venv_python, "-m", "pip", "install", "flask"])


def verify_flask(venv_python: str) -> None:
    """
    Verify that Flask can be imported and show its version.
    """
    print_header("Step 4: Verifying Flask in the venv")

    code = "import flask; print(flask.__version__)"
    version = run([venv_python, "-c", code])
    print(f"Flask import succeeded. Version: {version}")


def print_final_instructions(venv_python: str) -> None:
    print_header("Environment ready")

    instructions = dedent(f"""
    Your Python / Flask environment looks good.

    From NOW ON in this terminal session, do this:

      1. Activate the virtual environment:
             source {VENV_DIR}/bin/activate

      2. Run your Flask app (for example):
             python app.py

    Tips:
    - Every time you open a NEW terminal, you must:
        a) cd into your project folder
        b) run: source {VENV_DIR}/bin/activate
    - If anything breaks or you get 'ModuleNotFoundError: No module named flask',
      run this script again:
             python3 stabilize_env.py
    """).strip("\n")

    print(instructions)


def main():
    check_in_correct_folder()

    system_python = find_system_python()
    print(f"\nUsing system Python: {system_python}")

    ensure_venv_exists(system_python)

    venv_python = get_venv_python()
    print(f"\nVirtual environment Python: {venv_python}")

    install_dependencies(venv_python)
    verify_flask(venv_python)
    print_final_instructions(venv_python)


if __name__ == "__main__":
    main()
