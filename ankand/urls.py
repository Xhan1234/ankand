from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

# Override the 3 most important variables
admin.site.site_header = "Ankand Admin"
admin.site.site_title = "Ankand Admin Portal"
admin.site.index_title = "Welcome to Ankand Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls')),
    path('', include('auctions.urls')),
    path('', include('users.urls')),
    path('', include('messaging.urls')),
    path('', include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
