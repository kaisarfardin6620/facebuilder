from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class FaceScan(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scans')
    image = models.ImageField(upload_to='scan_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    jawline_angle = models.FloatField(help_text="Degrees. Lower is sharper.", null=True, blank=True)
    symmetry_score = models.FloatField(help_text="Percentage 0-100.", null=True, blank=True)
    puffiness_index = models.FloatField(help_text="Lower is better.", null=True, blank=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.status} - {self.created_at.strftime('%Y-%m-%d')}"

class UserGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='goals')
    
    wants_sharper_jawline = models.BooleanField(default=True)
    wants_reduce_puffiness = models.BooleanField(default=True)
    wants_improve_symmetry = models.BooleanField(default=True)
    target_jawline = models.FloatField(null=True, blank=True)
    target_symmetry = models.FloatField(null=True, blank=True)
    target_puffiness = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Goals for {self.user.phone_number}"