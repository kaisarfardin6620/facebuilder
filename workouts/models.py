from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Exercise(models.Model):
    TARGET_CHOICES = (
        ('JAWLINE', 'Jawline'),
        ('SYMMETRY', 'Symmetry'),
        ('PUFFINESS', 'Puffiness'),
        ('GENERAL', 'General'),
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    diagram_image = models.ImageField(upload_to='exercises/', blank=True, null=True)
    target_metric = models.CharField(max_length=20, choices=TARGET_CHOICES)
    
    def __str__(self):
        return self.name

class WorkoutPlan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workout_plan')
    created_at = models.DateTimeField(auto_now_add=True)
    sessions_completed_count = models.IntegerField(default=0) 
    difficulty_level = models.IntegerField(default=1)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Plan for {self.user.phone_number} (Lvl {self.difficulty_level})"

class PlanExercise(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    reps = models.CharField(max_length=50, help_text="e.g. '15 reps' or '30s hold'")
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    date_completed = models.DateTimeField(auto_now_add=True)
    plan_snapshot = models.JSONField(default=dict) 

    def __str__(self):
        return f"Session {self.pk} - {self.user.phone_number}"