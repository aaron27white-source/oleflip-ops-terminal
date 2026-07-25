"""storage.py — Tier 4 file storage abstraction.

LocalStorage writes under UPLOAD_DIR and is served by the /uploads static mount.
The interface (save/delete/url) is deliberately swappable for an S3 backend later
without touching the photo service or router.
"""

from pathlib import Path

from app.config import settings


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)

    def save(self, rel_path: str, data: bytes) -> str:
        full = self.base / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        return self.url(rel_path)

    def delete(self, rel_path: str) -> None:
        full = self.base / rel_path
        if full.exists():
            full.unlink()

    def url(self, rel_path: str) -> str:
        return f"/uploads/{rel_path}"


storage = LocalStorage(settings.upload_dir)
