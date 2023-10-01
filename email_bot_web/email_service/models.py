from api.services.tools import redis_client
from django.db import models
from user.models import BotUser


class EmailService(models.Model):
    """Модель почтового сервера."""

    title = models.CharField(max_length=128, verbose_name='Название', unique=True)
    slug = models.SlugField(verbose_name='Slug сервиса', unique=True)
    address = models.CharField(max_length=256, verbose_name='Адрес сервера')
    port = models.PositiveIntegerField(verbose_name='Порт сервера')

    class Meta:
        verbose_name = 'Почтовый сервис'
        verbose_name_plural = 'Почтовые сервисы'

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        redis_client.delete_key('all_email_services')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        redis_client.delete_key('all_email_services')


class EmailBox(models.Model):
    """Модель почтового ящика."""

    user_id = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='boxes', verbose_name='Пользователь')
    email_service = models.ForeignKey(EmailService, on_delete=models.PROTECT, related_name='boxes',
                                      verbose_name='Почтовый сервис')
    email_username = models.CharField(max_length=64, verbose_name='Имя пользователя')
    email_password = models.CharField(max_length=256, verbose_name='Пароль')
    listening = models.BooleanField(default=True, verbose_name='Слушает')

    class Meta:
        verbose_name = 'Почтовый ящик'
        verbose_name_plural = 'Почтовые ящики'

    def __str__(self) -> str:
        return self.email_username


class BoxFilter(models.Model):
    """Модель фильтра почтового ящика."""

    box_id = models.ForeignKey(EmailBox, on_delete=models.CASCADE, related_name='filters', verbose_name='Почтовый ящик')
    filter_value = models.CharField(max_length=256, verbose_name='Значение фильтра')
    filter_name = models.CharField(max_length=128, verbose_name='Имя фильтра', null=True, blank=True)

    class Meta:
        verbose_name = 'Фильтр'
        verbose_name_plural = 'Фильтры'

    def __str__(self) -> str:
        return self.filter_value
