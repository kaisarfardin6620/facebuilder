import csv
import sys
from django.core.management.base import BaseCommand
from workouts.models import Exercise

class Command(BaseCommand):
    help = 'Export exercises nicely formatted for Excel'

    def handle(self, *args, **kwargs):
        writer = csv.writer(sys.stdout)
        writer.writerow(['ID', 'Name', 'Category', 'Sets', 'Reps', 'Description', 'Instructions'])
        
        categories = ['JAWLINE', 'SYMMETRY', 'PUFFINESS', 'GENERAL']
        
        for cat in categories:
            exercises = Exercise.objects.filter(target_metric=cat)[:25]
            for ex in exercises:
                # FIX: Join steps with a space instead of a new line
                steps_text = " ".join([f"({i+1}) {step}" for i, step in enumerate(ex.instructions)])
                
                writer.writerow([
                    ex.id, 
                    ex.name, 
                    ex.target_metric, 
                    ex.default_sets, 
                    ex.default_reps, 
                    ex.description,
                    steps_text 
                ])