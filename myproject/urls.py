from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from myapp.views import sitemap_view

BASE_DIR = settings.BASE_DIR

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', serve, {'path': 'robots.txt', 'document_root': BASE_DIR}),
    path('sitemap.xml', sitemap_view),
    # मीडिया फाइल्स को सीधे ब्राउज़र में खोलने के लिए:
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('', include('myapp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)