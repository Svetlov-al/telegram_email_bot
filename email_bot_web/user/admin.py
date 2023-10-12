from django.contrib import admin
from user.models import BotUser


@admin.register(BotUser)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель модели User."""

    list_display = ('telegram_id',)
    list_display_links = ('telegram_id',)
    search_fields = ('telegram_id',)
    exclude = ('is_active',)
    readonly_fields = ('telegram_id',)
    search_help_text = 'Поиск по телеграм ID'

    list_per_page = 50
