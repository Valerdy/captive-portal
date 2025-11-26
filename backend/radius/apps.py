from django.apps import AppConfig


class RadiusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'radius'

    def ready(self):
        """Import signals when app is ready"""
        import radius.signals  # noqa
