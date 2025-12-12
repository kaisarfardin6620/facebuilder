from .models import WorkoutPlan, PlanExercise, Exercise
import random

def swap_exercise(plan_exercise):
    current_ex = plan_exercise.exercise
    plan = plan_exercise.plan
    
    existing_ids = plan.exercises.values_list('exercise_id', flat=True)
    
    candidates = Exercise.objects.filter(target_metric=current_ex.target_metric).exclude(id__in=existing_ids)
    
    if candidates.exists():
        new_exercise = random.choice(list(candidates))
        
        plan_exercise.exercise = new_exercise
        plan_exercise.sets = new_exercise.default_sets
        
        if new_exercise.default_duration and new_exercise.default_duration > 0:
            plan_exercise.duration = new_exercise.default_duration
            plan_exercise.reps = 0
        else:
            plan_exercise.reps = new_exercise.default_reps
            plan_exercise.duration = 0
            
        plan_exercise.save()
        return True
    return False

def update_plan_difficulty(plan):
    for plan_ex in plan.exercises.all():
        increased = max(0, plan.difficulty_level - 1)
        
        if plan_ex.duration and plan_ex.duration > 0:
            new_duration = plan_ex.exercise.default_duration + (increased * 5)
            
            if new_duration >= 60:
                swapped = swap_exercise(plan_ex)
                if not swapped:
                    plan_ex.duration = 60
                    plan_ex.save()
            else:
                plan_ex.duration = new_duration
                plan_ex.save()
                
        elif plan_ex.reps and plan_ex.reps > 0:
            new_reps = plan_ex.exercise.default_reps + increased
            
            if new_reps >= 12:
                swapped = swap_exercise(plan_ex)
                if not swapped:
                    plan_ex.reps = 12
                    plan_ex.save()
            else:
                plan_ex.reps = new_reps
                plan_ex.save()

def generate_workout_plan(user, scan_data, user_goals):
    WorkoutPlan.objects.filter(user=user).update(is_active=False)

    plan = WorkoutPlan.objects.create(user=user, difficulty_level=1, is_active=True)

    selected_metrics = []
    if user_goals.wants_sharper_jawline:
        selected_metrics.append('JAWLINE')
    if user_goals.wants_reduce_puffiness:
        selected_metrics.append('PUFFINESS')
    if user_goals.wants_improve_symmetry:
        selected_metrics.append('SYMMETRY')

    if not selected_metrics:
        selected_metrics.append('GENERAL')

    total_needed = 5
    goal_count = len(selected_metrics)
    base_count = total_needed // goal_count
    remainder = total_needed % goal_count

    exercises_to_add = []

    finisher = Exercise.objects.filter(name="Lymphatic Drainage").first()
    
    base_query = Exercise.objects.exclude(name="Lymphatic Drainage")

    for i, metric in enumerate(selected_metrics):
        count_for_this = base_count
        if i < remainder:
            count_for_this += 1
        
        exs = list(base_query.filter(target_metric=metric).order_by('?')[:count_for_this])
        exercises_to_add.extend(exs)

    if len(exercises_to_add) < total_needed:
        needed = total_needed - len(exercises_to_add)
        general = list(base_query.filter(target_metric='GENERAL').order_by('?')[:needed])
        exercises_to_add.extend(general)

    unique_exercises = []
    seen_ids = set()
    for ex in exercises_to_add:
        if ex.id not in seen_ids:
            unique_exercises.append(ex)
            seen_ids.add(ex.id)

    if finisher:
        unique_exercises.append(finisher)

    order_counter = 1
    for ex in unique_exercises:
        duration_val = 0
        reps_val = 0
        
        if ex.default_duration and ex.default_duration > 0:
            duration_val = ex.default_duration
        else:
            reps_val = ex.default_reps

        PlanExercise.objects.create(
            plan=plan,
            exercise=ex,
            reps=reps_val,
            duration=duration_val,
            sets=ex.default_sets,
            order=order_counter
        )
        order_counter += 1

    return plan