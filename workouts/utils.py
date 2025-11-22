from .models import WorkoutPlan, PlanExercise, Exercise

def generate_workout_plan(user, scan_data):
    """
    Creates a personalized workout plan based on AI scan metrics.
    """
    # 1. Deactivate old plans
    WorkoutPlan.objects.filter(user=user, is_active=True).update(is_active=False)

    # 2. Create new plan (Level 1 start)
    plan = WorkoutPlan.objects.create(
        user=user,
        difficulty_level=1,
        is_active=True
    )

    # 3. Select Exercises based on "Weakest" areas
    # Logic: If a score is poor, add exercises for that area.
    
    exercises_to_add = []
    
    # Jawline Check (High angle = needs work)
    if scan_data.jawline_angle > 125:
        jaw_exercises = Exercise.objects.filter(target_metric='JAWLINE')[:2]
        exercises_to_add.extend(jaw_exercises)
        
    # Puffiness Check (High index = needs work)
    if scan_data.puffiness_index > 0.5: # Adjust threshold as needed
        puff_exercises = Exercise.objects.filter(target_metric='PUFFINESS')[:2]
        exercises_to_add.extend(puff_exercises)
        
    # Symmetry Check (Low score = needs work)
    if scan_data.symmetry_score < 80:
        sym_exercises = Exercise.objects.filter(target_metric='SYMMETRY')[:2]
        exercises_to_add.extend(sym_exercises)

    # Fallback: If they are perfect, or we didn't find enough, add General exercises
    if len(exercises_to_add) < 3:
        general = Exercise.objects.filter(target_metric='GENERAL')[:3]
        exercises_to_add.extend(general)

    # Remove duplicates (maintain order)
    unique_exercises = []
    [unique_exercises.append(x) for x in exercises_to_add if x not in unique_exercises]

    # 4. Assign to Plan with Reps (Level 1 Reps)
    order_counter = 1
    for ex in unique_exercises:
        PlanExercise.objects.create(
            plan=plan,
            exercise=ex,
            reps="10 reps" if "Hold" not in ex.name else "10s hold", # Simple logic for text
            order=order_counter
        )
        order_counter += 1

    return plan