# cdn/image_utils.py
from io import BytesIO
from typing import Tuple
import logging
from PIL import Image, ImageOps
import pillow_heif

logger = logging.getLogger(__name__)

try:
    pillow_heif.register_heif_opener()
    logger.info("HEIF/HEIC image support enabled")
except ImportError:
    logger.warning("pillow_heif not installed, HEIF/HEIC images not supported")
except Exception as e:
    logger.error(f"Error initializing HEIF support: {str(e)}")

SUPPORTED_OUTPUTS = {"WEBP", "JPEG"}

def _choose_output_format(src_mode: str, want: str) -> Tuple[str, str]:
    has_alpha = src_mode in ("RGBA", "LA", "P")
    if want.upper() == "JPEG" and has_alpha:
        return "WEBP", ".webp"
    if want.upper() not in SUPPORTED_OUTPUTS:
        return "WEBP", ".webp"
    if want.upper() == "JPEG":
        return "JPEG", ".jpg"
    return "WEBP", ".webp"

def compress_image(
    file_obj,
    *,
    max_width: int | None = None,   # <-- None = don't resize, keep original dimensions
    quality: int = 75,              # lower = smaller files, 70–80 is a good start
    output_format: str = "WEBP",    # WEBP usually gives best size without resize
    strip_metadata: bool = True,
) -> Tuple[bytes, str, str]:
    
    # Validate parameters
    if quality < 1 or quality > 100:
        raise ValueError(f"Quality must be between 1 and 100, got {quality}")

    if max_width is not None and max_width < 1:
        raise ValueError(f"max_width must be positive, got {max_width}")

    try:
        img = Image.open(file_obj)
        original_format = img.format
        original_size = img.size

        logger.debug(f"Processing image: format={original_format}, size={original_size}, mode={img.mode}")
    except Exception as e:
        logger.error(f"Failed to open image: {str(e)}")
        raise IOError(f"Cannot open image file: {str(e)}")

    try:
        img = ImageOps.exif_transpose(img)

        # Convert paletted images to RGBA
        if img.mode == "P":
            img = img.convert("RGBA")

        # Resize if needed
        if max_width and img.width > max_width:
            ratio = max_width / float(img.width)
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            logger.debug(f"Resized image from {original_size} to {new_size}")

        # Choose output format based on image characteristics
        fmt, ext = _choose_output_format(img.mode, output_format)

        # Handle alpha channel for JPEG
        if fmt == "JPEG" and img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
            logger.debug("Converted RGBA to RGB for JPEG output")
        elif fmt == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")

        # Prepare save options
        out = BytesIO()
        save_kwargs = {}

        if fmt == "WEBP":
            save_kwargs.update(dict(quality=quality, method=6, optimize=True))
        elif fmt == "JPEG":
            save_kwargs.update(dict(quality=quality, optimize=True, progressive=True))

        # Strip metadata for privacy and smaller file size
        if strip_metadata:
            img.info.pop("exif", None)
            img.info.pop("icc_profile", None)

        # Save compressed image
        img.save(out, format=fmt, **save_kwargs)
        data = out.getvalue()

        original_size_bytes = getattr(file_obj, 'size', 0)
        compression_ratio = (1 - len(data) / original_size_bytes) * 100 if original_size_bytes > 0 else 0

        logger.info(
            f"Image compressed: {original_format} -> {fmt}, "
            f"size: {original_size_bytes}B -> {len(data)}B "
            f"({compression_ratio:.1f}% reduction)"
        )

        content_type = "image/webp" if fmt == "WEBP" else "image/jpeg"
        return data, content_type, ext

    except Exception as e:
        logger.error(f"Failed to compress image: {str(e)}")
        raise IOError(f"Image compression failed: {str(e)}")


"""
The Complete Workflow
Here's how image_utils.py and bunny.py work together in your Django project:

1. A user uploads an image in a Django form.

2. Your Django view receives the UploadedFile object.

3. You call compress_image(file_obj, max_width=1024, quality=80).

4. It returns the optimized data (bytes), content_type ('image/webp'), and extension ('.webp').

5. You then call upload_bytes(data=data, folder='user_avatars', base_name='some_unique_id', content_type=content_type, extension=extension).

6. The bunny.py script sends these bytes to Bunny CDN.

7. It returns a dictionary like {'path': 'user_avatars/some_unique_id.webp', 'url': 'https://...'}.

8. You save the path and url in your Django model's database field.

"""