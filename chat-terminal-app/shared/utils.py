from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime


def compute_sha256(file_path: str | Path) -> str:
    path = Path(file_path)
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


