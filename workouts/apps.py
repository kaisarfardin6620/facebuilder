import sys
import os
import json
import re
import time
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def auto_seed_exercises(sender, **kwargs):
    from .models import Exercise
    from django.conf import settings
    
    try:
        current_count = Exercise.objects.count()
    except Exception:
        return

    target_total = 100
    if current_count >= target_total:
        return

    print(f"--------- INITIALIZING AI DATA SEEDING ({current_count}/{target_total}) ---------")

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        print("ERROR: OPENAI_API_KEY is missing.")
        return

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        while current_count < target_total:
            batch_size = 20
            print(f"Fetching batch of {batch_size} exercises...")

            prompt = f"""
            Generate a JSON list of {batch_size} UNIQUE facial fitness exercises.
            Mix: JAWLINE, SYMMETRY, PUFFINESS, GENERAL.
            Structure: [{{"name": "...", "description": "...", "instructions": ["step1", "step2", "step3", "step4", "step5"], "default_reps": "10s", "target_metric": "JAWLINE"}}]
            Return raw JSON only.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.choices[0].message.content
                content = content.replace("```json", "").replace("```", "").strip()
                content = re.sub(r'\s+', ' ', content)

                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    continue

                final_list = []
                if isinstance(data, list):
                    final_list = data
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list): 
                            final_list = v
                            break
                
                for item in final_list:
                    if not isinstance(item, dict): continue
                    
                    metric = item.get('target_metric', 'GENERAL').replace(" ", "")
                    name = item.get('name', 'Unknown')

                    if not Exercise.objects.filter(name=name).exists():
                        Exercise.objects.create(
                            name=name,
                            description=item.get('description', ''),
                            instructions=item.get('instructions', []),
                            default_reps=item.get('default_reps', '10 reps'),
                            target_metric=metric
                        )
                
                current_count = Exercise.objects.count()
                time.sleep(1)

            except Exception as e:
                print(f"Batch failed: {str(e)}")
                break
        
        print(f"SUCCESS! Total Exercises: {current_count}")

    except Exception as e:
        print(f"Critical Error: {str(e)}")

class WorkoutsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workouts'

    def ready(self):
        post_migrate.connect(auto_seed_exercises, sender=self)