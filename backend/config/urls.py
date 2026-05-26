from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("ingestion.urls")),
    path("api/auth/", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve React build in production
frontend_dist = settings.BASE_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    urlpatterns += [
        re_path(
            r"^(?!api/|admin/|static/|media/).*$",
            TemplateView.as_view(template_name="index.html"),
            name="frontend",
        ),
    ]
