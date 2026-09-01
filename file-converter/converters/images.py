"""Image format conversion using Pillow."""
from pathlib import Path
from PIL import Image

# Formats we expose in the UI -> (extension, Pillow save format)
IMAGE_FORMATS = {
    "PNG": "png",
    "JPEG": "jpg",
    "WEBP": "webp",
    "BMP": "bmp",
    "GIF": "gif",
    "TIFF": "tiff",
    "ICO": "ico",
}

SUPPORTED_INPUT_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif",
    ".tiff", ".tif", ".ico", ".heic", ".heif",
}

try:
    # Optional: adds .heic/.heif read support if the package is installed.
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def convert_image(input_path: str, output_path: str, target_format: str) -> str:
    """Convert an image file to the target format. Returns the output path."""
    img = Image.open(input_path)

    fmt = target_format.upper()
    if fmt == "JPEG" and img.mode in ("RGBA", "P"):
        # JPEG has no alpha channel; flatten onto white.
        img = img.convert("RGB")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format=fmt)
    return str(out)
