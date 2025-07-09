import os
import shutil
import subprocess
from pathlib import Path
import zipfile

from project_root import PROJECT_ROOT

BUILD_DIR = PROJECT_ROOT / "lambda_build"
ZIP_NAME = "lambda_package.zip"
REQUIREMENTS_FILE = PROJECT_ROOT / "lambda_requirements.txt"
LAMBDA_SRC = PROJECT_ROOT / "lambda_package"

def clean_build_dir():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir()

def install_dependencies():
    subprocess.check_call([
        "pip", "install", "-r", str(REQUIREMENTS_FILE),
        "--target", str(BUILD_DIR)
    ])

def copy_source():
    for file in LAMBDA_SRC.iterdir():
        if file.is_file():
            shutil.copy(file, BUILD_DIR / file.name)

def zip_build():
    zip_path = PROJECT_ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in BUILD_DIR.rglob("*"):
            z.write(path, path.relative_to(BUILD_DIR))

    print(f"Created Lambda package at {zip_path}")

def main():
    clean_build_dir()
    install_dependencies()
    copy_source()
    zip_build()

if __name__ == "__main__":
    main()