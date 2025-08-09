from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import httpx


async def run_code(http_base_url: str, language: str, file_path: str, args: List[str] | None = None, stdin_text: str | None = None) -> Dict[str, Any]:
    """Send a run request to the server to compile/execute code.

    The server supports languages: C, C++, C#, Shell.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    payload = {
        "language": language,
        "path": str(path),
        "args": args or [],
        "stdin": stdin_text or None,
    }

    url = http_base_url.rstrip("/") + "/run"
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


