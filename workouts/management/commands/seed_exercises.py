import json
import re
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from workouts.models import Exercise
from openai import OpenAI

class Command(BaseCommand):
    help = 'Populate the database with 100 AI-generated facial exercises'

    def handle(self, *args, **kwargs):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR("OPENAI_API_KEY is missing."))
            return

        client = OpenAI(api_key=api_key)
        
        target_total = 100
        current_count = Exercise.objects.count()
        
        self.stdout.write(f"Current exercises: {current_count}. Goal: {target_total}")

        while current_count < target_total:
            needed = target_total - current_count
            batch_size = 20
            
            self.stdout.write(f"Fetching batch of {batch_size} exercises... (Current Total: {current_count})")

            prompt = f"""
            Generate a JSON list of {batch_size} UNIQUE facial fitness exercises.
            Mix of categories: JAWLINE, SYMMETRY, PUFFINESS, GENERAL.
            
            Structure:
            [
                {{
                    "name": "Creative Name",
                    "description": "Short summary",
                    "instructions": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
                    "default_reps": "10s" or "15 reps",
                    "target_metric": "JAWLINE"
                }}
            ]
            Return ONLY raw JSON. No markdown.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a fitness API that outputs raw JSON."},
                        {"role": "user", "content": prompt}
                    ]
                )

                content = response.choices[0].message.content
                content = content.replace("```json", "").replace("```", "").strip()
                content = re.sub(r'\s+', ' ', content)

                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    self.stdout.write(self.style.WARNING("JSON Error in this batch, retrying..."))
                    continue

                final_list = []
                if isinstance(data, list):
                    final_list = data
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            final_list = value
                            break
                
                added_in_batch = 0
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
                        added_in_batch += 1
                
                current_count = Exercise.objects.count()
                self.stdout.write(self.style.SUCCESS(f" + Added {added_in_batch} new exercises."))
                
                time.sleep(1)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
                break

        self.stdout.write(self.style.SUCCESS(f"DONE! Total exercises in DB: {current_count}"))