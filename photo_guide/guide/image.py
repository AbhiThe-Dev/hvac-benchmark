"""Photo intake: orientation applied, resized to the long edge Anthropic recommends for vision, re-encoded as JPEG with all metadata
(EXIF, GPS) dropped. The same recipe as pilot/vision_extract.preprocess_image, kept separate so this folder stands alone."""
from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SIDE_PX = 1568
JPEG_QUALITY = 85
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class BadImage(ValueError):
    pass


def preprocess(raw: bytes) -> Image.Image:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise BadImage("photo is larger than 15 MB")
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        img.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as e:
        raise BadImage("that file is not a readable photo") from e
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX), Image.LANCZOS)
    return img


def to_jpeg(img: Image.Image, quality: int = JPEG_QUALITY) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
