from django.apps import AppConfig


class UsrinfoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usrinfo'

    def ready(self):
        import usrinfo.signals  # important to connect signals
