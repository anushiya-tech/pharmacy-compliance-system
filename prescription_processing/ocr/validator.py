"""
Input validation utilities for prescription image files.
"""

from pathlib import Path
from typing import Set, Union

from .base import InvalidImageError, UnsupportedFormatError

SUPPORTED_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg"}


def validate_image_path(image_path: Union[str, Path]) -> Path:
    """
    Validate that an input path exists, is a supported image format, and contains readable image data.

    Args:
        image_path: Path string or Path object to the target image file.

    Returns:
        Resolved Path object if valid.

    Raises:
        InvalidImageError: If the file does not exist, is empty, or cannot be decoded as an image.
        UnsupportedFormatError: If the file extension is not among supported formats (.png, .jpg, .jpeg).
    """
    if not image_path:
        raise InvalidImageError("Image path cannot be empty or None.")

    path = Path(image_path).resolve()

    if not path.exists():
        raise InvalidImageError(f"Prescription image not found at path: '{path}'")

    if not path.is_file():
        raise InvalidImageError(f"Provided path is not a file: '{path}'")

    if path.stat().st_size == 0:
        raise InvalidImageError(f"Image file is empty (0 bytes): '{path}'")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedFormatError(
            f"Unsupported file format '{suffix}'. Supported formats are: {supported_list}"
        )

    # Optional integrity check via Pillow if Pillow is installed
    try:
        from PIL import Image

        with Image.open(path) as img:
            img.verify()
    except ImportError:
        # If Pillow is not installed yet, basic file existence and extension checks succeed
        pass
    except Exception as exc:
        raise InvalidImageError(
            f"Failed to decode image file '{path}'. File may be corrupted. Error: {exc}"
        ) from exc

    return path
