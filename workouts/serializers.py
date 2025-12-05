from rest_framework import serializers
from .models import WorkoutPlan, PlanExercise, Exercise

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['name', 'description', 'instructions', 'diagram_image', 'target_metric', 'default_sets']

class PlanExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    
    class Meta:
        model = PlanExercise
        fields = ['exercise', 'reps', 'sets', 'order']

class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises = PlanExerciseSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkoutPlan
        fields = ['id', 'difficulty_level', 'sessions_completed_count', 'exercises']