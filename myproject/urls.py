from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from myapp.views import sitemap_view

BASE_DIR = settings.BASE_DIR

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', serve, {'path': 'robots.txt', 'document_root': BASE_DIR}),
    path('sitemap.xml', sitemap_view),
    path('', include('myapp.urls')), # App URLs link
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)