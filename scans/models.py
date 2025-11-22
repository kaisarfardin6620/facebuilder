from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class FaceScan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scans')
    image = models.ImageField(upload_to='scan_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    jawline_angle = models.FloatField(help_text="Degrees. Lower is sharper.")
    symmetry_score = models.FloatField(help_text="Percentage 0-100.")
    puffiness_index = models.FloatField(help_text="Lower is better.")

    def __str__(self):
        return f"{self.user.phone_number} - {self.created_at.strftime('%Y-%m-%d')}"

class UserGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='goals')
    target_jawline = models.FloatField()
    target_symmetry = models.FloatField()
    target_puffiness = models.FloatField()
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Goals for {self.user.phone_number}"