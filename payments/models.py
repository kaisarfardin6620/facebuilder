from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    is_active = models.BooleanField(default=False)
    plan_name = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name} - {'Active' if self.is_active else 'Expired'}"