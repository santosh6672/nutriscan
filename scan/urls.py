from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('scan/', views.scan_product_ajax, name='scan'),
    path('scan-loading/<str:filename>/', views.scan_loading_view, name='scan_loading'),
    path('process-scan/<str:filename>/', views.process_scan, name='process_scan'),
    path('result/', views.result, name='result'),
]

# Media configuration (serving during development)
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )