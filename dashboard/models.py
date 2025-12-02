from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlan(models.Model):
    DURATION_CHOICES = (
        ('MONTHLY', 'Monthly'),
        ('6_MONTHS', '6 Months'),
        ('YEARLY', 'Yearly'),
    )

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_text = models.CharField(max_length=50, blank=True, null=True)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    
    market_product_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=100) 
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.plan_name}"