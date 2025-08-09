from __future__ import annotations

from pathlib import Path
import httpx
from .progress_bar import create_async_progress_bar


async def send_file(http_base_url: str, file_path: str) -> str:
    """Send a local file to the server via HTTP upload.

    Returns the filename recorded by the server.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    url = http_base_url.rstrip("/") + "/upload"
    async with httpx.AsyncClient(timeout=60) as client:
        with path.open("rb") as fp:
            files = {"file": (path.name, fp, "application/octet-stream")}
            response = await client.post(url, files=files)
            response.raise_for_status()
            return response.json().get("filename", path.name)


async def send_file_with_progress(http_base_url: str, file_path: str) -> str:
    """Send a local file to the server via HTTP upload with progress bar.

    Returns the filename recorded by the server.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    file_size = path.stat().st_size
    progress_bar = create_async_progress_bar(file_size, f"Envoi de {path.name}")

    url = http_base_url.rstrip("/") + "/upload"
    async with httpx.AsyncClient(timeout=60) as client:
        with path.open("rb") as fp:
            files = {"file": (path.name, fp, "application/octet-stream")}
            response = await client.post(url, files=files)
            response.raise_for_status()
            
            # Marquer comme terminé
            await progress_bar.set_progress(file_size)
            await progress_bar.finish()
            
            return response.json().get("filename", path.name)


