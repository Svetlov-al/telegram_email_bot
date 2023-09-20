from django.apps import AppConfig


class EmailServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_domain'
    verbose_name = 'Ящики электронной почты'
