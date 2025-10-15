import logging
from typing import Dict, Optional
from django.conf import settings
from rest_framework import serializers

from cdn import bunny
from cdn.image_utils import compress_image

logger = logging.getLogger(__name__)


def upload_image_to_bunny(
    file,
    *,
    folder: str,
    public_id: str,
    max_width: int = 800,
    quality: int = 75,
    output_format: str = "WEBP"
) -> Dict[str, str]:
    
    try:
        # Compress image
        data, content_type, ext = compress_image(
            file,
            max_width=max_width,
            quality=quality,
            output_format=output_format,
        )

        # Upload to Bunny CDN
        res = bunny.upload_bytes(
            data,
            folder=folder,
            base_name=public_id,
            content_type=content_type,
            extension=ext,
        )

        return {
            "public_id": res["path"],
            "secure_url": res["url"],
            "url": res["url"]
        }

    except IOError as e:
        logger.error(f"Image compression failed for {public_id}: {str(e)}")
        raise serializers.ValidationError(f"Failed to process image: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to upload image to Bunny CDN for {public_id}: {str(e)}")
        raise serializers.ValidationError(f"Failed to upload image: {str(e)}")


def delete_image_from_bunny(
    public_id: Optional[str],
    url: Optional[str] = None,
    purge_cache: bool = True
) -> bool:
    
    if not public_id:
        logger.debug("Skipping deletion: empty public_id")
        return False

    try:
        # Delete from storage
        success = bunny.delete(public_id)

        # Purge cache if requested and configured
        if success and purge_cache and url:
            should_purge = getattr(settings, 'BUNNY_PURGE_ON_OVERWRITE', True)
            if should_purge:
                result = bunny.purge_cache([url])
                if result['failed']:
                    logger.warning(f"Cache purge failed for {url}")

        return success

    except Exception as e:
        logger.error(f"Unexpected error deleting image {public_id}: {str(e)}")
        return False


def update_image_in_bunny(
    instance,
    image_file,
    *,
    public_id_field: str,
    url_field: str,
    folder: str,
    base_name: str,
    max_width: int = 800,
    quality: int = 75
) -> None:
    
    # Delete old image if exists
    old_public_id = getattr(instance, public_id_field, None)
    old_url = getattr(instance, url_field, None)

    if old_public_id:
        delete_image_from_bunny(old_public_id, old_url)

    # Upload new image
    res = upload_image_to_bunny(
        image_file,
        folder=folder,
        public_id=base_name,
        max_width=max_width,
        quality=quality
    )

    # Update instance fields
    setattr(instance, public_id_field, res['public_id'])
    setattr(instance, url_field, res['secure_url'] or res['url'])
    instance.save(update_fields=[public_id_field, url_field])

    logger.info(f"Updated image for {instance.__class__.__name__} {instance.pk}: {res['public_id']}")


def clear_image_from_bunny(
    instance,
    *,
    public_id_field: str,
    url_field: str
) -> None:
    public_id = getattr(instance, public_id_field, None)
    url = getattr(instance, url_field, None)

    if public_id:
        delete_image_from_bunny(public_id, url)

    # Clear fields
    setattr(instance, public_id_field, None)
    setattr(instance, url_field, None)
    instance.save(update_fields=[public_id_field, url_field])

    logger.info(f"Cleared image for {instance.__class__.__name__} {instance.pk}")


def bulk_delete_images_from_bunny(media_pairs: list) -> Dict[str, list]:
    
    success = []
    failed = []

    for public_id, url in media_pairs:
        if not public_id:
            continue

        if delete_image_from_bunny(public_id, url):
            success.append(public_id)
        else:
            failed.append(public_id)

    logger.info(f"Bulk delete: {len(success)} succeeded, {len(failed)} failed")
    return {'success': success, 'failed': failed}
