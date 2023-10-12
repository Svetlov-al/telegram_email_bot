from infrastucture.tools import CACHE_PREFIX, redis_client


def delete_email_boxes_and_clear_cache(modeladmin, request, queryset):
    for obj in queryset:
        user_key = f'user:{obj.email_username}'
        redis_client.delete_key(user_key)
        filter_key = f'{CACHE_PREFIX}filters_for_{obj.user_id.telegram_id}_{obj.email_username}'
        redis_client.delete_key(filter_key)
        email_boxes = f'{CACHE_PREFIX}email_boxes_for_user_{obj.user_id.telegram_id}'
        redis_client.delete_key(email_boxes)
        email_box_key = f'{CACHE_PREFIX}email_box_{obj.user_id.telegram_id}_{obj.email_username}'
        redis_client.delete_key(email_box_key)

        obj.delete()


delete_email_boxes_and_clear_cache.short_description = 'Удалить выбранные и очистить кеш'  # type: ignore


def delete_filters_and_clear_chache(modeladmin, request, queryset):
    for obj in queryset:
        filter_key = f'{CACHE_PREFIX}filters_for_{obj.box_id.user_id.telegram_id}_{obj.box_id.email_username}'
        redis_client.delete_key(filter_key)
        email_boxes_key = f'{CACHE_PREFIX}email_boxes_for_user_{obj.box_id.user_id.telegram_id}'
        redis_client.delete_key(email_boxes_key)
        email_box_key = f'{CACHE_PREFIX}email_box_{obj.box_id.user_id.telegram_id}_{obj.box_id.email_username}'
        redis_client.delete_key(email_box_key)

        obj.delete()


delete_filters_and_clear_chache.short_description = 'Удалить выбранные и очистить кеш'  # type: ignore


def delete_users_and_clear_chache(modeladmin, request, queryset):
    for obj in queryset:
        if hasattr(obj, 'boxes') and obj.boxes.exists():
            email_box = obj.boxes.first()

            user_key = f'user:{email_box.email_username}'
            redis_client.delete_key(user_key)

            filter_key = f'{CACHE_PREFIX}filters_for_{obj.telegram_id}_{email_box.email_username}'
            redis_client.delete_key(filter_key)

            email_boxes_key = f'{CACHE_PREFIX}email_boxes_for_user_{obj.telegram_id}'
            redis_client.delete_key(email_boxes_key)

            email_box_key = f'{CACHE_PREFIX}email_box_{obj.telegram_id}_{email_box.email_username}'
            redis_client.delete_key(email_box_key)

        obj.delete()


delete_users_and_clear_chache.short_description = 'Удалить выбранные и очистить кеш'  # type: ignore
