import json
import re
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from workouts.models import Exercise
from openai import OpenAI

class Command(BaseCommand):
    help = 'Populate the DB with exactly 25 exercises per category (100 total) including sets'

    def handle(self, *args, **kwargs):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR("OPENAI_API_KEY is missing."))
            return

        client = OpenAI(api_key=api_key)
        
        categories = ['JAWLINE', 'SYMMETRY', 'PUFFINESS', 'GENERAL']
        target_per_category = 25

        for category in categories:
            current_count = Exercise.objects.filter(target_metric=category).count()
            
            self.stdout.write(f"Checking {category}: Have {current_count}/{target_per_category}")

            while current_count < target_per_category:
                needed = target_per_category - current_count
                batch_size = min(5, needed)

                self.stdout.write(f" -> Fetching {batch_size} new {category} exercises...")

                prompt = f"""
                Generate a JSON list of {batch_size} UNIQUE facial fitness exercises specifically for: {category}.
                
                Structure:
                [
                    {{
                        "name": "Creative Name",
                        "description": "Short summary",
                        "instructions": ["Step 1", "Step 2", "Step 3"],
                        "default_reps": "10s" or "15 reps",
                        "default_sets": 3 (integer between 2 and 4),
                        "target_metric": "{category}"
                    }}
                ]
                Return ONLY raw JSON. No markdown.
                """

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
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
                        self.stdout.write(self.style.WARNING("JSON Error, retrying..."))
                        continue

                    final_list = []
                    if isinstance(data, list):
                        final_list = data
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                final_list = v
                                break
                    
                    added_count = 0
                    for item in final_list:
                        name = item.get('name', 'Unknown')
                        if not Exercise.objects.filter(name=name).exists():
                            Exercise.objects.create(
                                name=name,
                                description=item.get('description', ''),
                                instructions=item.get('instructions', []),
                                default_reps=item.get('default_reps', '10 reps'),
                                default_sets=item.get('default_sets', 3),
                                target_metric=category
                            )
                            added_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"    + Added {added_count} exercises."))
                    
                    current_count = Exercise.objects.filter(target_metric=category).count()
                    time.sleep(1)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
                    break

        total = Exercise.objects.count()
        self.stdout.write(self.style.SUCCESS(f"DONE! Total exercises in DB: {total}"))