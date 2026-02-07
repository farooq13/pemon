from django.apps import AppConfig


class KycConfig(AppConfig):
    """Configuration for the KYC application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kyc'
    verbose_name = 'KYC Verification'

    def ready(self):
        """
        Initialize app when Django starts.
        
        Import signal handlers to ensure they are registered.
        """
        import kyc.signals  # noqa: F401