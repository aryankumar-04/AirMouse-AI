"""
AirMouse AI - Automated Windows PyInstaller Build & Packaging Script.

Runs unit tests, invokes PyInstaller, bundles models and configs, and packages
the release output into release/AirMouseAI-v1.0.0/.
"""

import os
import shutil
import subprocess
import sys
import time

VERSION = "v1.0.0"
APP_NAME = "AirMouseAI"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist", APP_NAME)
RELEASE_DIR = os.path.join(ROOT_DIR, "release", f"{APP_NAME}-{VERSION}")


def log(msg: str):
    print(f"[BUILD] {msg}")


def run_tests() -> bool:
    log("Running automated unit test suite before packaging...")
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode != 0:
        log("ERROR: Unit tests failed! Aborting packaging.")
        return False
    log("Unit tests passed successfully.")
    return True


def run_pyinstaller() -> bool:
    log("Executing PyInstaller build process...")
    spec_path = os.path.join(ROOT_DIR, "airmouse_ai.spec")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", spec_path]
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode != 0:
        log("ERROR: PyInstaller execution failed!")
        return False
    log("PyInstaller compilation completed successfully.")
    return True


def package_release() -> bool:
    log(f"Creating release package directory: '{RELEASE_DIR}'...")

    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)

    os.makedirs(RELEASE_DIR, exist_ok=True)

    # Copy PyInstaller distribution folder contents
    if os.path.exists(DIST_DIR):
        shutil.copytree(DIST_DIR, RELEASE_DIR, dirs_exist_ok=True)
    else:
        log(f"ERROR: Compiled dist directory '{DIST_DIR}' not found!")
        return False

    # Copy documentation files
    for doc in ["README.md", "CHANGELOG.md", "requirements.txt"]:
        src = os.path.join(ROOT_DIR, doc)
        if os.path.exists(src):
            shutil.copy(src, RELEASE_DIR)

    exe_path = os.path.join(RELEASE_DIR, f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        log("=========================================================")
        log(f"SUCCESS: {APP_NAME} {VERSION} release built successfully!")
        log(f"Executable Path : {exe_path}")
        log(f"Release Folder  : {RELEASE_DIR}")
        log(f"Executable Size : {size_mb:.2f} MB")
        log("=========================================================")
        return True
    else:
        log(f"ERROR: Output executable '{exe_path}' was not found!")
        return False


def main():
    start_time = time.time()

    if not run_tests():
        sys.exit(1)

    if not run_pyinstaller():
        sys.exit(1)

    if not package_release():
        sys.exit(1)

    elapsed = time.time() - start_time
    log(f"Total build time: {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
