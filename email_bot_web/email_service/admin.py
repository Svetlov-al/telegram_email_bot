from django.contrib import admin
from email_service.models import BoxFilter, EmailBox, EmailService


class BoxFilterInline(admin.TabularInline):
    """
    Встроенный интерфейс для модели BoxFilter.

    Позволяет редактировать фильтры прямо в форме почтового ящика.
    """
    model = BoxFilter
    extra = 1


@admin.register(EmailBox)
class BoxAdmin(admin.ModelAdmin):
    """Админ-панель модели почтового ящика."""

    list_display = ('display_user', 'display_email_service', 'email_username')
    list_filter = ('email_service__title',)
    search_fields = ('email_username',)

    search_help_text = 'Поиск по имени пользователя'

    list_per_page = 50

    inlines = (BoxFilterInline,)

    def display_user(self, obj: EmailBox) -> str:
        return obj.user_id.telegram_id

    display_user.short_description = 'Пользователь'  # type: ignore

    def display_email_service(self, obj: EmailBox) -> str:
        return obj.email_service.title

    display_email_service.short_description = 'Почтовый сервис'  # type: ignore


@admin.register(EmailService)
class EmailServiceAdmin(admin.ModelAdmin):
    """Админ-панель модели почтового сервиса."""

    list_display = ('title', 'slug', 'address', 'port')
    list_editable = ('slug', 'address', 'port')

    list_per_page = 50


@admin.register(BoxFilter)
class FilterAdmin(admin.ModelAdmin):
    """Админ-панель модели фильтра почтового ящика."""

    list_display = ('display_box', 'filter_value', 'filter_name')

    list_per_page = 50

    def display_box(self, obj: BoxFilter) -> str:
        return obj.box_id.email_username

    display_box.short_description = 'Почтовый ящик'  # type: ignore
