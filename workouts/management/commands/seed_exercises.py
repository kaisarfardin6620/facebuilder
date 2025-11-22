import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from workouts.models import Exercise
from openai import OpenAI

class Command(BaseCommand):
    help = 'Populate the database with AI-generated facial exercises using OpenAI'

    def handle(self, *args, **kwargs):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR("OPENAI_API_KEY is missing in settings."))
            return

        client = OpenAI(api_key=api_key)
        self.stdout.write("Contacting OpenAI to generate exercises... (This may take 10-20 seconds)")

        prompt = """
        Generate a JSON list of 20 facial fitness exercises. 
        For each exercise, provide:
        1. "name": A short, catchy name (e.g., "Jawline Clench").
        2. "description": A short 2-sentence instruction on how to do it.
        3. "target_metric": Must be exactly one of these strings: "JAWLINE", "SYMMETRY", "PUFFINESS", "GENERAL".
        
        Ensure there are at least 5 exercises for each target_metric.
        Output only raw JSON, no markdown.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
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
                if not Exercise.objects.filter(name=item['name']).exists():
                    Exercise.objects.create(
                        name=item['name'],
                        description=item['description'],
                        target_metric=item['target_metric']
                    )
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(f"Successfully added {count} new exercises from OpenAI!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to generate exercises: {str(e)}"))