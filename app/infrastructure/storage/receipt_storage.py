from pathlib import Path
from typing import Optional
import uuid

_ROOT = Path(__file__).resolve().parents[3] / "uploads"
_MAX_BYTES = 5 * 1024 * 1024
_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def save_receipt(
    user_id: uuid.UUID,
    expense_id: uuid.UUID,
    data: bytes,
    content_type: Optional[str],
) -> str:
    if not data:
        raise ValueError("Choose an image of the bill")
    if len(data) > _MAX_BYTES:
        raise ValueError("Bill image must be 5 MB or smaller")

    ext = _TYPES.get((content_type or "").split(";")[0].strip().lower()) or _sniff(data)
    if ext is None:
        raise ValueError("Bill must be a JPEG, PNG, or WebP image")

    folder = _ROOT / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob(f"{expense_id}.*"):
        old.unlink()
    path = folder / f"{expense_id}{ext}"
    path.write_bytes(data)
    return str(path.relative_to(_ROOT.parent))


def delete_receipt(relative_path: Optional[str]) -> None:
    path = receipt_file(relative_path)
    if path is not None and path.is_file():
        path.unlink()


def receipt_file(relative_path: Optional[str]) -> Optional[Path]:
    if not relative_path:
        return None
    root = _ROOT.resolve()
    path = (_ROOT.parent / relative_path).resolve()
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
