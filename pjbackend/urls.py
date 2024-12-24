from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import health_check
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Pom Juice API",
        default_version="v1",
        description="Test description",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path(
        "swagger",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    path('admin/', admin.site.urls),
    path("", include("users.urls"), name="v1"),
    path("", include("locations.urls"), name="v1"),
    path("", include("startups.urls"), name="v1"),
    path("", include("reviews.urls"), name="v1"),
    path("", include("tracks.urls"), name="v1"),
    path("", include("investors.urls"), name="v1"),
    path("", include("payment.urls"), name="v1"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)