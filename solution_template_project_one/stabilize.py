#!/usr/bin/env python3
"""
stabilize_env.py

Run this from inside the project folder:

    .../solution_template_project_one/

It will:
- Confirm you are in the correct folder.
- Ensure a virtual environment exists in ./venv (create it if missing).
- Install dependencies (requirements.txt if present, otherwise Flask).
- Verify Flask can be imported from the venv.
- Configure VS Code (.vscode/settings.json) to use the venv interpreter.

Usage (in the terminal):
    python3 stabilize_env.py
"""

import os
import sys
import subprocess
import shutil
import json
from textwrap import dedent

# We only care that the current folder is this:
EXPECTED_FOLDER_NAME = "solution_template_project_one"

# Files that must exist in the project
PROJECT_MARKERS = ["app.py"]

VENV_DIR = "venv"
REQUIREMENTS_FILE = "requirements.txt"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def fail(msg: str) -> None:
    print(f"\n[ERROR] {msg}")
    print("Fix the issue, then run: python3 stabilize_env.py again.")
    sys.exit(1)


def run(cmd):
    """
    Run a shell command and return its stdout text.
    On failure, print output and exit with a clear error.
    """
    print(f"\n> {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    if result.returncode != 0:
        print(result.stdout)
        fail(f"Command failed: {' '.join(cmd)}")
    print(result.stdout.strip())
    return result.stdout.strip()


def is_running_in_vscode() -> bool:
    """
    Heuristic: detect if this script is run from VS Code's integrated terminal.
    """
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if term_program == "vscode":
        return True
    if "VSCODE_PID" in os.environ:
        return True
    if "VSCODE_INJECTOR" in os.environ:
        return True
    return False


# ---------------------------------------------------------------------------
# Directory and project checks
# ---------------------------------------------------------------------------

def enforce_correct_directory() -> None:
    """
    Ensure this script is being run from a folder named:
        solution_template_project_one
    """
    print_header("Checking current working directory")

    cwd = os.getcwd()
    normalized = os.path.normpath(cwd)
    folder_name = os.path.basename(normalized)

    if folder_name != EXPECTED_FOLDER_NAME:
        print("You are NOT in the correct folder.\n")
        print(f"This script MUST be run from a folder named:")
        print(f"  {EXPECTED_FOLDER_NAME}\n")
        print("Your current folder is:")
        print(f"  {cwd}\n")

        if is_running_in_vscode():
            print("It looks like you are using VS Code.")
            print("In VS Code, do this:")
            print("  1. File → Open Folder…")
            print("  2. Choose the folder that contains:")
            print("         solution_template_project_one")
            print("  3. Then open: solution_template_project_one")
            print("  4. Open a terminal (View → Terminal).")
            print("  5. Run: python3 stabilize_env.py\n")
        else:
            print("In your terminal, you should run something like:")
            print("  cd path/to/solution_template_project_one\n")

        fail("You are in the wrong directory.")
    else:
        print(f"Good: You are in the '{EXPECTED_FOLDER_NAME}' project directory.")


def check_project_files() -> None:
    """
    Ensure required files exist (e.g., app.py)
    """
    missing = [f for f in PROJECT_MARKERS if not os.path.exists(f)]
    if missing:
        print_header("Checking required project files")
        print("Missing required files:")
        for f in missing:
            print(f"  - {f}")
        fail("You are in the right folder name, but the project files are missing.")
    print("\nProject files found. Good.")


# ---------------------------------------------------------------------------
# Python / venv helpers
# ---------------------------------------------------------------------------

def find_system_python() -> str:
    """
    Find a suitable system Python (python3 preferred).
    """
    for name in ("python3", "python"):
        path = shutil.which(name)
        if path:
            return path
    fail("Could not find python3 or python on this system.")


def get_venv_python() -> str:
    """
    Get the Python interpreter inside the venv (supports macOS/Linux and Windows).
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


def ensure_venv_exists(system_python: str) -> None:
    """
    Create ./venv if it does not exist.
    """
    print_header("Checking virtual environment (venv)")
    if os.path.isdir(VENV_DIR):
        print(f"Virtual environment '{VENV_DIR}' already exists. Good.")
        return

    print("Virtual environment not found. Creating it now...")
    run([system_python, "-m", "venv", VENV_DIR])
    print(f"Created virtual environment in ./{VENV_DIR}")


def install_dependencies(venv_python: str) -> None:
    """
    Upgrade pip and install packages into the venv.
    - If requirements.txt exists, install from there.
    - Otherwise, ensure Flask is installed.
    """
    print_header("Installing / checking dependencies")

    print("Upgrading pip in the virtual environment...")
    run([venv_python, "-m", "pip", "install", "--upgrade", "pip"])

    if os.path.exists(REQUIREMENTS_FILE):
        print(f"Found {REQUIREMENTS_FILE}. Installing required packages...")
        run([venv_python, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    else:
        print(f"No {REQUIREMENTS_FILE} found. Ensuring Flask is installed...")
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
    print_header("Verifying Flask in the venv")
    code = "import flask; print(flask.__version__)"
    version = run([venv_python, "-c", code])
    print(f"Flask import succeeded. Version: {version}")


# ---------------------------------------------------------------------------
# VS Code configuration
# ---------------------------------------------------------------------------

def configure_vscode_settings(venv_python: str) -> None:
    """
    Create or update .vscode/settings.json so VS Code uses the venv Python.

    Sets:
        "python.defaultInterpreterPath": "<venv_python>"
        "python.terminal.activateEnvironment": true
    """
    print_header("Configuring VS Code (Python interpreter)")

    project_root = os.getcwd()
    vscode_dir = os.path.join(project_root, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)

    settings_path = os.path.join(vscode_dir, "settings.json")
    settings = {}

    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            print(f"Loaded existing VS Code settings from {settings_path}")
        except Exception:
            print("Existing settings.json is invalid JSON. Overwriting it with fresh settings.")
            settings = {}

    # Update settings
    settings["python.defaultInterpreterPath"] = venv_python
    settings["python.terminal.activateEnvironment"] = True

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

    print(f"Updated VS Code settings at: {settings_path}")
    print("VS Code should now automatically use the venv interpreter for this folder.")


# ---------------------------------------------------------------------------
# Final instructions
# ---------------------------------------------------------------------------

def print_final_instructions() -> None:
    print_header("Environment Ready")

    instructions = dedent(f"""
    Your Python / Flask environment for this project is set up correctly.

    From now on, when you start work:

        1. Open VS Code.
        2. Use File → Open Folder… and open the folder that contains:
               {EXPECTED_FOLDER_NAME}
        3. Then open the folder:
               {EXPECTED_FOLDER_NAME}
        4. Open a terminal in VS Code (View → Terminal).
        5. If needed, activate the venv:
               source venv/bin/activate
        6. Run your Flask app:
               python app.py

    If you get errors like 'ModuleNotFoundError: No module named flask', run:
        python3 stabilize_env.py

    VS Code has been configured to use the virtual environment's Python interpreter
    for this folder (.vscode/settings.json).
    """).strip("\n")

    print(instructions)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    enforce_correct_directory()
    check_project_files()

    system_python = find_system_python()
    print(f"\nUsing system Python: {system_python}")

    ensure_venv_exists(system_python)
    venv_python = get_venv_python()
    print(f"\nVirtual environment Python: {venv_python}")

    install_dependencies(venv_python)
    verify_flask(venv_python)
    configure_vscode_settings(venv_python)
    print_final_instructions()


if __name__ == "__main__":
    main()
