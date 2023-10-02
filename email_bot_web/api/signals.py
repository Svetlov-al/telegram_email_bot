from api.services.tools import CACHE_PREFIX, redis_client
from asgiref.sync import async_to_sync
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from email_service.models import EmailService


@receiver(post_save, sender=EmailService)
def clear_cache_on_save(sender, instance, **kwargs):  # noqa
    async_to_sync(clear_cache_async)()


@receiver(post_delete, sender=EmailService)
def clear_cache_on_delete(sender, instance, **kwargs):  # noqa
    async_to_sync(clear_cache_async)()


async def clear_cache_async():
    await redis_client.delete_key(f'{CACHE_PREFIX}all_email_domains')
