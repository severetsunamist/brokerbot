from django.contrib import admin
from .models import Premise

@admin.register(Premise)
class PremiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'offer_type', 'location_text', 'created_at')
    list_filter = ('offer_type', 'created_at')
    search_fields = ('name', 'location_text')
