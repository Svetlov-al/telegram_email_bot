from django.db import models
from user.models import BotUser


class EmailService(models.Model):
    """Модель почтового сервера."""

    service_slug = models.SlugField(
        verbose_name='Slug сервиса',
        unique=True,
    )
    service_address = models.CharField(
        max_length=255,
        verbose_name='Адрес сервера',
    )
    service_port = models.PositiveIntegerField(
        verbose_name='Порт сервера',
    )

    class Meta:
        verbose_name = 'Почтовый сервис'
        verbose_name_plural = 'Почтовые сервисы'

    def __str__(self) -> str:
        return f'{self.service_slug}'


class EmailBox(models.Model):
    """Модель почтового ящика."""

    user_id = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name='boxes',
        verbose_name='Пользователь',
    )

    email_service = models.ForeignKey(
        EmailService,
        on_delete=models.PROTECT,
        related_name='boxes',
        verbose_name='Почтовый сервис',
    )

    email_username = models.CharField(
        max_length=64,
        verbose_name='Имя пользователя',
    )

    email_password = models.CharField(
        max_length=255,
        verbose_name='Пароль',
    )

    class Meta:
        verbose_name = 'Почтовый ящик'
        verbose_name_plural = 'Почтовые ящики'

    def __str__(self) -> str:
        return f'{self.email_username}'


class BoxFilter(models.Model):
    """Модель фильтра почтового ящика."""

    box_id = models.ForeignKey(
        EmailBox,
        on_delete=models.CASCADE,
        related_name='filters',
        verbose_name='Почтовый ящик',
    )

    filter_value = models.CharField(
        max_length=255,
        verbose_name='Значение фильтра',
    )

    filter_name = models.CharField(
        max_length=100,
        verbose_name='Имя фильтра',
        null=True,
    )

    class Meta:
        verbose_name = 'Фильтр'
        verbose_name_plural = 'Фильтры'

    def __str__(self) -> str:
        return f'{self.filter_value}'
