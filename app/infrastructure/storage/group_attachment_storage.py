from pathlib import Path
from typing import Optional
import uuid

from app.infrastructure.storage.receipt_storage import receipt_file

_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "groups"
_IMAGE_MAX = 5 * 1024 * 1024
_VIDEO_MAX = 20 * 1024 * 1024
_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


def save_group_attachment(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    data: bytes,
    content_type: Optional[str],
) -> str:
    if not data:
        raise ValueError("Choose an image or video of the bill")
    kind = (content_type or "").split(";")[0].strip().lower()
    ext = _IMAGE_TYPES.get(kind) or _VIDEO_TYPES.get(kind) or _sniff(data)
    if ext is None:
        raise ValueError("Attachment must be a JPEG, PNG, WebP, MP4, or WebM file")
    limit = _VIDEO_MAX if ext in {".mp4", ".webm", ".mov"} else _IMAGE_MAX
    if len(data) > limit:
        raise ValueError(
            "Video must be 20 MB or smaller" if ext in {".mp4", ".webm", ".mov"} else "Image must be 5 MB or smaller"
        )
    folder = _ROOT / str(group_id)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob(f"{expense_id}.*"):
        old.unlink()
    path = folder / f"{expense_id}{ext}"
    path.write_bytes(data)
    return str(path.relative_to(_ROOT.parents[1]))


def save_group_image(group_id: uuid.UUID, data: bytes, content_type: Optional[str]) -> str:
    if not data:
        raise ValueError("Choose a group photo")
    if len(data) > _IMAGE_MAX:
        raise ValueError("Group photo must be 5 MB or smaller")
    kind = (content_type or "").split(";")[0].strip().lower()
    ext = _IMAGE_TYPES.get(kind) or _sniff(data)
    if ext is None or ext not in {".jpg", ".png", ".webp"}:
        raise ValueError("Group photo must be a JPEG, PNG, or WebP image")
    folder = _ROOT / str(group_id)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("cover.*"):
        old.unlink()
    path = folder / f"cover{ext}"
    path.write_bytes(data)
    return str(path.relative_to(_ROOT.parents[1]))


def group_file(relative_path: Optional[str]) -> Optional[Path]:
    return receipt_file(relative_path)


def _sniff(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return ".mp4"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return ".webm"
    return None
