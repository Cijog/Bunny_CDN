"""
Bunny CDN integration package.

This package provides utilities for uploading, deleting, and managing
media files on Bunny CDN with automatic image compression and caching.

Main modules:
- bunny: Core Bunny CDN API operations (upload, delete, purge_cache)
- image_utils: Image compression and optimization utilities
- helpers: High-level helper functions for common operations
"""

# Import main functions for easier access
from cdn.bunny import upload, upload_bytes, delete, purge_cache
from cdn.image_utils import compress_image
from cdn.helpers import (
    upload_image_to_bunny,
    delete_image_from_bunny,
    update_image_in_bunny,
    clear_image_from_bunny,
    bulk_delete_images_from_bunny,
)

__all__ = [
    # Core functions
    'upload',
    'upload_bytes',
    'delete',
    'purge_cache',
    'compress_image',

    # Helper functions
    'upload_image_to_bunny',
    'delete_image_from_bunny',
    'update_image_in_bunny',
    'clear_image_from_bunny',
    'bulk_delete_images_from_bunny',
]
