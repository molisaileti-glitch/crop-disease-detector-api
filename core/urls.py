# core/urls.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main URL configuration.
# All API endpoints start with /api/v1/
# Swagger docs available at /swagger/
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ── SWAGGER CONFIGURATION ────────────────────────────
# Auto generates beautiful API documentation
# Access at: http://127.0.0.1:8000/swagger/
schema_view = get_schema_view(
    openapi.Info(
        title="Crop Disease Detector API",
        default_version='v1',
        description="""
        REST API for the Crop Disease Detector mobile app.
        Helps Tanzanian farmers identify crop diseases from photos.

        Features:
        - User authentication with JWT
        - Image upload and disease diagnosis
        - Treatment recommendations
        - Diagnosis history
        """,
        contact=openapi.Contact(email="molisaileti@gmail.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # All API endpoints — versioned with v1
    path('api/v1/', include('api.urls')),

    # Swagger API documentation
    path('swagger/', schema_view.with_ui(
        'swagger', cache_timeout=0
    ), name='schema-swagger-ui'),

    # Alternative API docs (ReDoc style)
    path('redoc/', schema_view.with_ui(
        'redoc', cache_timeout=0
    ), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )