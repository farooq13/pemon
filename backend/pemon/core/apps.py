from django.apps import AppConfig


class CoreConfig(AppConfig):    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when the app is ready. Use it to:
        - Import signal handlers
        - Register system checks
        - Perform startup initialization
        """
        # Import signal handlers
        # import core.signals  # Uncomment when signals are created
        pass