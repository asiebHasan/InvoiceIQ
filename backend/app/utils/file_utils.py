import os
import hashlib
from pathlib import Path


def compute_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def safe_filename(filename: str) -> str:
    name = Path(filename).stem
    ext = Path(filename).suffix
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return f"{safe}{ext}"
