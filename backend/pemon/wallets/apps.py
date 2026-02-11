from django.apps import AppConfig


class WalletsConfig(AppConfig):
    """Configuration for wallets app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wallets'
    verbose_name = 'Wallets'
    
    def ready(self):
        """
        Import signals when app is ready.
        
        This ensures signal handlers are registered when Django starts.
        """
        import wallets.signals  # noqa