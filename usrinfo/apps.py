from django.apps import AppConfig


class UsrinfoConfig(AppConfig): # to run custom startup code/ inherits the default appconfig and modify the configuration(we can insert signals before the app runs)
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usrinfo'

    def ready(self):#override the default ready
        import usrinfo.signals  # important to connect signals
