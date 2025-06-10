from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Premise(models.Model):
    OFFER_TYPES = (
        ('sale', 'Sale'),
        ('lease', 'Lease'),
    )
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    location_text = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPES)
    
    # Area fields
    industrial_area = models.DecimalField(max_digits=10, decimal_places=2)
    mezzanine_area = models.DecimalField(max_digits=10, decimal_places=2)
    office_area = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Lease pricing
    industrial_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    mezzanine_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    office_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Sale pricing
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Premise"
        verbose_name_plural = "Premises"
    
    def __str__(self):
        return f"{self.name} ({self.get_offer_type_display()})"
