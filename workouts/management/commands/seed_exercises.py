import json
import re  # <--- NEW IMPORT
from django.core.management.base import BaseCommand
from django.conf import settings
from workouts.models import Exercise
from openai import OpenAI

class Command(BaseCommand):
    help = 'Populate the database with AI-generated facial exercises using OpenAI'

    def handle(self, *args, **kwargs):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR("OPENAI_API_KEY is missing."))
            return

        client = OpenAI(api_key=api_key)
        self.stdout.write("Contacting OpenAI... (Waiting for response)")

        prompt = """
        Generate a JSON list of 20 facial fitness exercises. 
        Structure:
        [
            {
                "name": "Exercise Name",
                "description": "Short summary",
                "instructions": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
                "default_reps": "10 reps",
                "target_metric": "JAWLINE"
            }
        ]
        Target Metrics must be exactly: JAWLINE, SYMMETRY, PUFFINESS, GENERAL.
        Return ONLY the raw JSON list. No markdown.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a JSON data generator."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content
            
            # --- FIX: SANITIZE THE INPUT ---
            # 1. Remove Markdown
            content = content.replace("```json", "").replace("```", "").strip()
            
            # 2. Remove Newlines inside strings (The "SYM\nMETRY" Fix)
            # This replaces all whitespace/newlines with a single space to prevent JSON crashes
            content = re.sub(r'\s+', ' ', content)
            # -------------------------------

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"JSON Parse Error: {str(e)}"))
                return

            # Smart List Finding
            final_list = []
            if isinstance(data, list):
                final_list = data
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        final_list = value
                        break
            
            count = 0
            for item in final_list:
                if not isinstance(item, dict): continue

                # Fix "SYM METRY" typo if it happened during sanitization
                metric = item.get('target_metric', 'GENERAL').replace(" ", "")
                
                if not Exercise.objects.filter(name=item.get('name')).exists():
                    Exercise.objects.create(
                        name=item.get('name', 'Unknown'),
                        description=item.get('description', ''),
                        instructions=item.get('instructions', []),
                        default_reps=item.get('default_reps', '10 reps'),
                        target_metric=metric # Use the clean metric
                    )
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(f"Successfully added {count} exercises!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical Error: {str(e)}"))