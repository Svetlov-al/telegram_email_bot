from django.db import models


class BotUser(models.Model):
    """Модель пользователя."""

    telegram_id = models.BigIntegerField(verbose_name='ID телеграм', primary_key=True)
    is_active = models.BooleanField(default=True, verbose_name='Активность')

    class Meta:
        verbose_name = 'Пользователь бота'
        verbose_name_plural = 'Пользователи бота'

    def __str__(self) -> str:
        return str(self.telegram_id)
