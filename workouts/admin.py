from django.contrib import admin
from .models import Exercise, WorkoutPlan, PlanExercise, WorkoutSession

class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 1 

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_metric')
    list_filter = ('target_metric',)
    search_fields = ('name',)

@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'difficulty_level', 'sessions_completed_count', 'is_active')
    list_filter = ('is_active', 'difficulty_level')
    search_fields = ('user__phone_number',)
    inlines = [PlanExerciseInline]

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_completed')
    list_filter = ('date_completed',)
    search_fields = ('user__phone_number',)