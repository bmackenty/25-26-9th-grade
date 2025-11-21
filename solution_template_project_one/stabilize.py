#!/usr/bin/env python3
"""
Stabilize Flask environment for solution_template_project_one
"""

import os, sys, subprocess, shutil, json, urllib.request
from textwrap import dedent

EXPECTED_FOLDER = "solution_template_project_one"
VENV_DIR = "venv"
REQUIREMENTS_FILE = "requirements.txt"
PROJECT_MARKERS = ["app.py"]

# Versioning
LOCAL_VERSION = "2025.11.21-1"
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "bmackenty/25-26-9th-grade/main/solution_template_project_one/stabilize.py"
)


# ------------ Helpers -------------

def fail(msg):
    print(f"\n[ERROR] {msg}")
    sys.exit(1)


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        print(result.stdout)
        fail(f"Command failed: {' '.join(cmd)}")
    return result.stdout.strip()


# ------------ Version check -------------

def get_remote_version():
    try:
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=2) as r:
            text = r.read().decode("utf-8", "ignore")
        for line in text.splitlines():
            if line.strip().startswith("LOCAL_VERSION"):
                # Expect: LOCAL_VERSION = "2025.11.21-1"
                parts = line.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def check_version():
    remote = get_remote_version()
    if not remote:
        print(f"• stabilize.py version {LOCAL_VERSION} (GitHub check skipped)")
    elif remote == LOCAL_VERSION:
        print(f"✓ stabilize.py up to date ({LOCAL_VERSION})")
    else:
        print(f"[!] stabilize.py outdated (local {LOCAL_VERSION}, GitHub {remote})")
        print("    Get latest from: https://github.com/bmackenty/25-26-9th-grade")


# ------------ Checks -------------

def check_folder():
    if os.path.basename(os.path.normpath(os.getcwd())) != EXPECTED_FOLDER:
        fail(f"Run inside folder: {EXPECTED_FOLDER}")


def check_files():
    missing = [f for f in PROJECT_MARKERS if not os.path.exists(f)]
    if missing:
        fail(f"Missing required files: {', '.join(missing)}")


def find_python():
    for p in ("python3", "python"):
        q = shutil.which(p)
        if q:
            return q
    fail("python3 not found")


# ------------ VENV -------------

def make_venv(system_python):
    if os.path.isdir(VENV_DIR):
        print("✓ venv exists")
        return
    print("• Creating venv...")
    run([system_python, "-m", "venv", VENV_DIR])
    print("✓ venv created")


def venv_python():
    for path in (
        os.path.join(VENV_DIR, "bin", "python"),
        os.path.join(VENV_DIR, "Scripts", "python.exe")
    ):
        if os.path.exists(path):
            return path
    fail("venv python missing")


def install_deps(vpy):
    print("• Checking dependencies...")
    run([vpy, "-m", "pip", "install", "--upgrade", "pip"])
    if os.path.exists(REQUIREMENTS_FILE):
        run([vpy, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    else:
        code = "import importlib; print(importlib.util.find_spec('flask')!=None)"
        if run([vpy, "-c", code]) != "True":
            run([vpy, "-m", "pip", "install", "flask"])
    print("✓ Dependencies OK")


def verify_flask(vpy):
    code = "import importlib.metadata as m; print(m.version('flask'))"
    version = run([vpy, "-c", code])
    print(f"✓ Flask {version}")


# ------------ VS CODE -------------

def set_vscode(vpy):
    vscode_dir = os.path.join(os.getcwd(), ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)
    settings_path = os.path.join(vscode_dir, "settings.json")
    try:
        settings = json.load(open(settings_path)) if os.path.exists(settings_path) else {}
    except Exception:
        settings = {}
    settings["python.defaultInterpreterPath"] = vpy
    settings["python.terminal.activateEnvironment"] = True
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    print("✓ VS Code linked to venv")


# ------------ Main -------------

def main():
    check_folder()
    check_files()
    check_version()
    py = find_python()
    make_venv(py)
    vpy = venv_python()
    install_deps(vpy)
    verify_flask(vpy)
    set_vscode(vpy)

    print("\n=== Ready ===")
    print(dedent("""
      To start:
        source venv/bin/activate
        python3 app.py

      If anything breaks:
        python3 stabilize.py
    """).strip())


if __name__ == "__main__":
    main()
