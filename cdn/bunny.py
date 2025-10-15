import os
import mimetypes
import logging
from urllib.parse import urljoin
from io import BytesIO
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Build the base URL used for Storage API calls (upload/delete)
STORAGE_BASE = (
    settings.BUNNY_STORAGE_ENDPOINT.rstrip("/") + "/" +
    settings.BUNNY_STORAGE_ZONE.strip("/") + "/"
)

def _ext_from(file_obj) -> str:
    name = getattr(file_obj, "name", "")
    ctype = getattr(file_obj, "content_type", None)
    ext = os.path.splitext(name)[1]
    if not ext and ctype:
        ext = mimetypes.guess_extension(ctype) or ""
    return ext or ".bin"

def _path_for(folder: str, base_name: str, file_obj) -> str:
    folder = folder.strip("/")
    ext = _ext_from(file_obj)
    return f"{folder}/{base_name}{ext}"

def upload(file_obj, *, folder: str, base_name: str) -> dict:
    path = _path_for(folder, base_name, file_obj)
    put_url = STORAGE_BASE + path
    headers = {
        "AccessKey": settings.BUNNY_STORAGE_PASSWORD, 
        "Content-Type": getattr(file_obj, "content_type", "application/octet-stream"),
    }

    try:
        # Read stream (Django InMemoryUploadedFile/TemporaryUploadedFile)
        content = file_obj.read()
        resp = requests.put(put_url, data=content, headers=headers, timeout=60)
        resp.raise_for_status()

        logger.info(f"Successfully uploaded file to Bunny CDN: {path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload file to Bunny CDN: {path}, Error: {str(e)}")
        raise

    # Build CDN URL, append optimizer defaults if configured
    cdn_url = urljoin(settings.BUNNY_CDN_BASE_URL.rstrip("/") + "/", path)
    qs = getattr(settings, "BUNNY_OPTIMIZER_DEFAULTS", "")
    if qs:
        connector = "&" if "?" in cdn_url else "?"
        cdn_url = f"{cdn_url}{connector}{qs}"

    return {"path": path, "url": cdn_url}

def upload_bytes(
    data: bytes,
    *,
    folder: str,
    base_name: str,
    content_type: str,
    extension: str,
) -> dict:
    folder = folder.strip("/")
    path = f"{folder}/{base_name}{extension}"
    put_url = STORAGE_BASE + path
    headers = {
        "AccessKey": settings.BUNNY_STORAGE_PASSWORD,
        "Content-Type": content_type,
    }

    try:
        resp = requests.put(put_url, data=data, headers=headers, timeout=60)
        resp.raise_for_status()

        logger.info(f"Successfully uploaded compressed bytes to Bunny CDN: {path} ({len(data)} bytes)")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to upload compressed bytes to Bunny CDN: {path}, Error: {str(e)}")
        raise

    cdn_url = urljoin(settings.BUNNY_CDN_BASE_URL.rstrip("/") + "/", path)
    qs = getattr(settings, "BUNNY_OPTIMIZER_DEFAULTS", "")
    if qs:  # leaving this on won't hurt; with Optimizer off it's ignored
        connector = "&" if "?" in cdn_url else "?"
        cdn_url = f"{cdn_url}{connector}{qs}"

    return {"path": path, "url": cdn_url}

def delete(path: str) -> bool:
    
    if not path:
        logger.warning("Attempted to delete empty path from Bunny CDN")
        return False

    del_url = STORAGE_BASE + path.lstrip("/")
    headers = {"AccessKey": settings.BUNNY_STORAGE_PASSWORD}

    try:
        resp = requests.delete(del_url, headers=headers, timeout=30)
        resp.raise_for_status()
        logger.info(f"Successfully deleted file from Bunny CDN: {path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to delete file from Bunny CDN: {path}, Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting file from Bunny CDN: {path}, Error: {str(e)}")
        return False

def purge_cache(urls: list[str]) -> dict:
    
    if not urls:
        logger.warning("Attempted to purge cache with empty URL list")
        return {"success": [], "failed": []}

    if not settings.BUNNY_PULL_ZONE_ID:
        logger.warning("BUNNY_PULL_ZONE_ID not configured, skipping cache purge")
        return {"success": [], "failed": urls}

    if not settings.BUNNY_API_KEY:
        logger.warning("BUNNY_API_KEY not configured, skipping cache purge")
        return {"success": [], "failed": urls}

    api = f"https://api.bunny.net/pullzone/{settings.BUNNY_PULL_ZONE_ID}/purgeCache"
    headers = {"AccessKey": settings.BUNNY_API_KEY}

    success = []
    failed = []

    for url in urls:
        if not url:
            continue

        try:
            resp = requests.post(api, headers=headers, json={"url": url}, timeout=30)
            resp.raise_for_status()
            success.append(url)
            logger.info(f"Successfully purged cache for URL: {url}")
        except requests.exceptions.RequestException as e:
            failed.append(url)
            logger.error(f"Failed to purge cache for URL: {url}, Error: {str(e)}")
        except Exception as e:
            failed.append(url)
            logger.error(f"Unexpected error purging cache for URL: {url}, Error: {str(e)}")

    return {"success": success, "failed": failed}
