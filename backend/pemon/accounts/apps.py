from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'User Accounts'

    def ready(self):
        """
        Initialize app when Django starts.
        
        Import signal handlers and perform startup tasks.
        """
        
        pass