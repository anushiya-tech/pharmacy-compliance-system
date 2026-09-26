"""
Tesseract OCR engine implementation for local optical character recognition on Windows.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCREngineUnavailableError, OCRExecutionError

COMMON_WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


class TesseractEngine(OCREngine):
    """
    OCR engine wrapping Google's Tesseract OCR via pytesseract.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the Tesseract OCR engine.

        Args:
            tesseract_cmd: Optional custom path to the tesseract executable.
        """
        self._custom_cmd = tesseract_cmd

    @property
    def name(self) -> str:
        return "tesseract"

    def find_tesseract_binary(self) -> Optional[Path]:
        """
        Locate the Tesseract OCR binary on Windows or Unix.
        Checks custom path, TESSERACT_CMD env var, system PATH, and common Windows locations.
        """
        # 1. Custom provided path
        if self._custom_cmd:
            path = Path(self._custom_cmd)
            if path.is_file():
                return path

        # 2. Environment variable
        env_cmd = os.environ.get("TESSERACT_CMD")
        if env_cmd:
            path = Path(env_cmd)
            if path.is_file():
                return path

        # 3. System PATH
        which_path = shutil.which("tesseract")
        if which_path:
            return Path(which_path)

        # 4. Common Windows installation directories
        for win_path_str in COMMON_WINDOWS_TESSERACT_PATHS:
            win_path = Path(win_path_str)
            if win_path.is_file():
                return win_path

        # 5. User LocalAppData fallback
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            local_path = Path(local_app_data) / "Programs" / "Tesseract-OCR" / "tesseract.exe"
            if local_path.is_file():
                return local_path

        return None

    def is_available(self) -> bool:
        """Check whether pytesseract is installed and the binary is discoverable."""
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            return False

        return self.find_tesseract_binary() is not None

    def extract_text(self, image_path: Path) -> str:
        """
        Extract raw text from a prescription image using Tesseract OCR.

        Args:
            image_path: Validated path to the image file.

        Returns:
            Extracted text string.

        Raises:
            OCREngineUnavailableError: If pytesseract or tesseract binary is missing.
            OCRExecutionError: If tesseract fails during processing.
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise OCREngineUnavailableError(
                "Required Python packages for Tesseract OCR are not installed. "
                "Please install them via: pip install -r prescription_processing/ocr/requirements.txt "
                f"(Missing dependency: {exc.name})"
            ) from exc

        binary_path = self.find_tesseract_binary()
        if not binary_path:
            raise OCREngineUnavailableError(
                "Tesseract-OCR executable was not found on your system.\n"
                "To resolve on Windows:\n"
                "1. Download and install Tesseract from: "
                "https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Either add its directory (e.g. C:\\Program Files\\Tesseract-OCR) to your PATH, "
                "or set the TESSERACT_CMD environment variable pointing to tesseract.exe."
            )

        pytesseract.pytesseract.tesseract_cmd = str(binary_path)

        try:
            with Image.open(image_path) as img:
                # Convert palette/alpha modes to RGB for OCR consistency
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                text = pytesseract.image_to_string(img)
                return text or ""
        except Exception as exc:
            raise OCRExecutionError(
                f"Tesseract OCR failed to process image '{image_path}'. Reason: {exc}"
            ) from exc
