from admin_utils.admin_actions import delete_users_and_clear_chache
from django.contrib import admin
from user.models import BotUser


@admin.register(BotUser)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель модели User."""

    actions = [delete_users_and_clear_chache]

    list_display = ('telegram_id',)
    list_display_links = ('telegram_id',)
    search_fields = ('telegram_id',)
    exclude = ('is_active',)
    readonly_fields = ('telegram_id',)
    search_help_text = 'Поиск по телеграм ID'

    list_per_page = 50

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
