import sys
import os
import json
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def auto_seed_exercises(sender, **kwargs):
    from .models import Exercise
    from django.conf import settings
    
    try:
        if Exercise.objects.exists():
            return
    except Exception:
        return

    print("--------- INITIALIZING AI DATA SEEDING ---------")
    print("Database is empty. Asking OpenAI for exercises...")

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        print("ERROR: OPENAI_API_KEY is missing. Cannot seed data.")
        return

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = """
        Generate a JSON list of 20 facial fitness exercises. 
        For each exercise, provide:
        1. "name": A short, catchy name (e.g., "Jawline Clench").
        2. "description": A short 2-sentence instruction on how to do it.
        3. "target_metric": Must be exactly one of these strings: "JAWLINE", "SYMMETRY", "PUFFINESS", "GENERAL".
        
        Ensure there are at least 5 exercises for each target_metric.
        Output only raw JSON, no markdown.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a fitness API that outputs data in JSON."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "")
        exercises_data = json.loads(content)

        count = 0
        for item in exercises_data:
            Exercise.objects.create(
                name=item['name'],
                description=item['description'],
                target_metric=item['target_metric']
            )
            count += 1
        
        print(f"SUCCESS: Automatically created {count} exercises!")

    except Exception as e:
        print(f"ERROR: Auto-seeding failed: {e}")

class WorkoutsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workouts'

    def ready(self):
        post_migrate.connect(auto_seed_exercises, sender=self)