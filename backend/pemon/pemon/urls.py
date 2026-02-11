from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# HEALTH CHECK ENDPOINTS
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns basic system health status without requiring authentication.
    
    Returns:
        Response: JSON response with status and version information
    """
    return Response({
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'Pemon Fintech API',
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check endpoint for Kubernetes/container orchestration.
    
    Checks if the application is ready to serve requests by verifying:
    - Database connectivity
    - Redis connectivity
    - Other critical dependencies
    
    Returns:
        Response: JSON response with readiness status
    """
    from django.db import connection
    from django.core.cache import cache
    
    checks = {
        'database': False,
        'cache': False,
    }
    
    # Check database
    try:
        connection.ensure_connection()
        checks['database'] = True
    except Exception:
        pass
    
    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception:
        pass
    
    # All checks must pass
    is_ready = all(checks.values())
    
    return Response({
        'ready': is_ready,
        'checks': checks,
    }, status=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE)


# URL PATTERNS
urlpatterns = [
    # ADMIN INTERFACE
    path('admin/', admin.site.urls),
    
    # HEALTH CHECK ENDPOINTS
    path('health/', health_check, name='health-check'),
    path('ready/', readiness_check, name='readiness-check'),
    
    # API DOCUMENTATION
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 ENDPOINTS
    path('api/v1/auth/', include('accounts.urls', namespace='accounts')),
    path('api/v1/kyc/', include('kyc.urls')),
    path('api/v1/wallet/', include('wallets.urls')),
    path('api/v1/transactions/', include('transactions.urls')),
    path('api/v1/transfers/', include('p2p_transfers.urls')),
    
]

# ADMIN SITE CUSTOMIZATION
admin.site.site_header = 'Pemon Administration'
admin.site.site_title = 'Pemon Admin Portal'
admin.site.index_title = 'Welcome to Pemon Administration'

# STATIC AND MEDIA FILES (Development Only)
if settings.DEBUG:
    # Serve static and media files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass