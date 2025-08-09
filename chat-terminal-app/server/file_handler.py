from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import UploadFile


UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> Path:
    """Save an incoming UploadFile to disk in a memory-efficient way."""
    destination_path = UPLOADS_DIR / upload_file.filename
    with destination_path.open("wb") as output_file:
        while True:
            chunk = await upload_file.read(1024 * 1024)  # 1 MiB chunks
            if not chunk:
                break
            output_file.write(chunk)
    await upload_file.close()
    return destination_path


def list_uploaded_files() -> List[str]:
    """Return a sorted list of filenames present in the uploads directory."""
    return sorted(
        [path.name for path in UPLOADS_DIR.iterdir() if path.is_file()]
    )


