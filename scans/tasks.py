from celery import shared_task
from django.core.files.base import ContentFile
from .models import FaceScan, UserGoal
from .ai_logic import analyze_face_image
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_face_scan(scan_id):
    try:
        scan = FaceScan.objects.get(id=scan_id)
        scan.status = 'PROCESSING'
        scan.save()

        with scan.image.open('rb') as img_file:
            metrics = analyze_face_image(img_file)

        scan.jawline_angle = metrics['jawline_angle']
        scan.symmetry_score = metrics['symmetry_score']
        scan.puffiness_index = metrics['puffiness_index']
        scan.status = 'COMPLETED'
        scan.save()

        UserGoal.objects.update_or_create(
            user=scan.user,
            defaults={
                'target_jawline': round(metrics['jawline_angle'] * 0.95, 1),
                'target_symmetry': min(100, round(metrics['symmetry_score'] * 1.10, 1)),
                'target_puffiness': round(metrics['puffiness_index'] * 0.90, 2)
            }
        )

        logger.info(f"Scan {scan_id} processed successfully.")
        return True

    except FaceScan.DoesNotExist:
        logger.error(f"Scan {scan_id} not found.")
        return False
        
    except Exception as e:
        logger.error(f"Error processing scan {scan_id}: {str(e)}")
        try:
            scan = FaceScan.objects.get(id=scan_id)
            scan.status = 'FAILED'
            scan.error_message = str(e)
            scan.save()
        except:
            pass
        return False