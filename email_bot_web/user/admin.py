from django.contrib import admin
from email_service.models import EmailBox
from user.models import BotUser


class EmailBoxInline(admin.TabularInline):
    model = EmailBox
    extra = 1


@admin.register(BotUser)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель модели User."""

    list_display = ('telegram_id', 'is_active')
    list_editable = ('is_active',)
    list_display_links = ('telegram_id',)
    list_filter = ('is_active',)
    search_fields = ('telegram_id',)

    search_help_text = 'Поиск по телеграм ID'

    list_per_page = 50

    inlines = [EmailBoxInline]

    fieldsets = (
        (None, {
            'fields': ('telegram_id', 'is_active'),
            'description': {
                'ID Телеграм': 'Уникальный идентификатор пользователя в Telegram.',
                'Активность': 'Указывает, активен ли пользователь.'
            }
        }),
    )
