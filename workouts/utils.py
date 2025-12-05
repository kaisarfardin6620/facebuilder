from .models import WorkoutPlan, PlanExercise, Exercise
import re

def calculate_reps_for_level(default_reps_str, level):
    nums = re.findall(r'\d+', default_reps_str)
    if not nums:
        return default_reps_str
    
    base_val = int(nums[0])
    increase_factor = max(0, level - 1)
    
    if 's' in default_reps_str.lower():
        new_val = min(base_val + (increase_factor * 5), 120)
        return f"{new_val}s"
    else:
        new_val = min(base_val + (increase_factor * 2), 50)
        return f"{new_val} reps"

def generate_workout_plan(user, scan_data, user_goals):
    WorkoutPlan.objects.filter(user=user).update(is_active=False)

    plan = WorkoutPlan.objects.create(user=user, difficulty_level=1, is_active=True)

    exercises_to_add = []

    if user_goals.wants_sharper_jawline:
        exs = list(Exercise.objects.filter(target_metric='JAWLINE').order_by('?')[:8])
        exercises_to_add.extend(exs)
        
    if user_goals.wants_reduce_puffiness:
        exs = list(Exercise.objects.filter(target_metric='PUFFINESS').order_by('?')[:8])
        exercises_to_add.extend(exs)
        
    if user_goals.wants_improve_symmetry:
        exs = list(Exercise.objects.filter(target_metric='SYMMETRY').order_by('?')[:8])
        exercises_to_add.extend(exs)

    if len(exercises_to_add) < 8:
        needed = 8 - len(exercises_to_add)
        general = list(Exercise.objects.filter(target_metric='GENERAL').order_by('?')[:needed])
        exercises_to_add.extend(general)

    unique_exercises = []
    seen_ids = set()
    for ex in exercises_to_add:
        if ex.id not in seen_ids:
            unique_exercises.append(ex)
            seen_ids.add(ex.id)

    order_counter = 1
    for ex in unique_exercises:
        reps_value = calculate_reps_for_level(ex.default_reps, plan.difficulty_level)

        PlanExercise.objects.create(
            plan=plan,
            exercise=ex,
            reps=reps_value,
            sets=ex.default_sets,
            order=order_counter
        )
        order_counter += 1

    return plan