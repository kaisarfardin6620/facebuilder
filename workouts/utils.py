from .models import WorkoutPlan, PlanExercise, Exercise

def generate_workout_plan(user, scan_data, user_goals):
    WorkoutPlan.objects.filter(user=user).update(is_active=False)

    plan = WorkoutPlan.objects.create(user=user, difficulty_level=1, is_active=True)

    exercises_to_add = []

    if user_goals.wants_sharper_jawline:
        exs = Exercise.objects.filter(target_metric='JAWLINE')[:2]
        exercises_to_add.extend(exs)
        
    if user_goals.wants_reduce_puffiness:
        exs = Exercise.objects.filter(target_metric='PUFFINESS')[:2]
        exercises_to_add.extend(exs)
        
    if user_goals.wants_improve_symmetry:
        exs = Exercise.objects.filter(target_metric='SYMMETRY')[:2]
        exercises_to_add.extend(exs)

    if len(exercises_to_add) < 3:
        general = Exercise.objects.filter(target_metric='GENERAL')[:3]
        exercises_to_add.extend(general)

    unique_exercises = []
    [unique_exercises.append(x) for x in exercises_to_add if x not in unique_exercises]

    order_counter = 1
    for ex in unique_exercises:
        if order_counter == 1:
            duration = 10 + ((plan.difficulty_level - 1) * 5)
            reps_value = f"{duration}s"
        else:
            reps_value = ex.default_reps

        PlanExercise.objects.create(
            plan=plan,
            exercise=ex,
            reps=reps_value,
            order=order_counter
        )
        order_counter += 1

    return plan