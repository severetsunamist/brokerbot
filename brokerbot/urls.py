from django.contrib import admin
from django.urls import path, include  # Make sure to import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bot/', include('botapp.urls')),  # This links to your bot app's URLs
]
