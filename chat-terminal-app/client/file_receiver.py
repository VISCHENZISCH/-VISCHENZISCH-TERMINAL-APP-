from __future__ import annotations

from pathlib import Path
import httpx
from .progress_bar import create_async_progress_bar


async def download_file(
    http_base_url: str, filename: str, destination_dir: str | Path
) -> Path:
    """Download a file from the server's static uploads and save it locally."""
    destination_directory = Path(destination_dir).expanduser().resolve()
    destination_directory.mkdir(parents=True, exist_ok=True)

    url = http_base_url.rstrip("/") + f"/uploads/{filename}"
    destination_path = destination_directory / filename

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        destination_path.write_bytes(response.content)

    return destination_path


async def download_file_with_progress(
    http_base_url: str, filename: str, destination_dir: str | Path
) -> Path:
    """Download a file from the server's static uploads and save it locally with progress bar."""
    destination_directory = Path(destination_dir).expanduser().resolve()
    destination_directory.mkdir(parents=True, exist_ok=True)

    url = http_base_url.rstrip("/") + f"/uploads/{filename}"
    destination_path = destination_directory / filename

    async with httpx.AsyncClient(timeout=60) as client:
        # D'abord, obtenir la taille du fichier
        head_response = await client.head(url)
        if head_response.status_code == 200:
            content_length = head_response.headers.get('content-length')
            total_size = int(content_length) if content_length else 0
        else:
            total_size = 0
        
        progress_bar = create_async_progress_bar(total_size, f"Téléchargement de {filename}")
        
        response = await client.get(url)
        response.raise_for_status()
        
        # Écrire le fichier
        destination_path.write_bytes(response.content)
        
        # Marquer comme terminé
        await progress_bar.set_progress(len(response.content))
        await progress_bar.finish()
        
        return destination_path


