from django.contrib import admin
from .models import FaceScan, UserGoal

@admin.register(FaceScan)
class FaceScanAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'jawline_angle', 'symmetry_score', 'puffiness_index')
    list_filter = ('created_at',)
    search_fields = ('user__phone_number', 'user__name')
    readonly_fields = ('created_at',)

@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_jawline', 'target_symmetry', 'target_puffiness', 'updated_at')
    search_fields = ('user__phone_number',)