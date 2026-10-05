from pathlib import Path
from typing import Optional
import uuid

_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "avatars"
_MAX_BYTES = 5 * 1024 * 1024
_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def save_avatar(user_id: uuid.UUID, data: bytes, content_type: Optional[str]) -> str:
    if not data:
        raise ValueError("Choose a profile photo")
    if len(data) > _MAX_BYTES:
        raise ValueError("Profile photo must be 5 MB or smaller")

    ext = _TYPES.get((content_type or "").split(";")[0].strip().lower()) or _sniff(data)
    if ext is None:
        raise ValueError("Profile photo must be a JPEG, PNG, or WebP image")

    _ROOT.mkdir(parents=True, exist_ok=True)
    for old in _ROOT.glob(f"{user_id}.*"):
        old.unlink()
    path = _ROOT / f"{user_id}{ext}"
    path.write_bytes(data)
    return str(path.relative_to(_ROOT.parents[1]))


def delete_avatar(relative_path: Optional[str]) -> None:
    path = avatar_file(relative_path)
    if path is not None and path.is_file():
        path.unlink()


def avatar_file(relative_path: Optional[str]) -> Optional[Path]:
    if not relative_path:
        return None
    root = _ROOT.resolve()
    path = (_ROOT.parents[1] / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def _sniff(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    return None
