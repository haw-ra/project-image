# gallery/management/commands/recompute_encodings.py
from django.core.management.base import BaseCommand
from gallery.models import Photo
from deepface import DeepFace
import json
import numpy as np
import os
import traceback

def l2_normalize(vec):
    v = np.array(vec, dtype=float)
    n = np.linalg.norm(v)
    return (v / n).tolist() if n != 0 else v.tolist()

class Command(BaseCommand):
    help = "Recompute encodings for all photos using Facenet (128) and save as JSON normalized list."

    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, default='Facenet', help='model_name to use (default Facenet)')
        parser.add_argument('--skip-missing', action='store_true', help='skip photos whose file path is missing')

    def handle(self, *args, **options):
        model = options['model']
        skipped = 0
        updated = 0
        for p in Photo.objects.all():
            try:
                if not getattr(p, 'path', None) or not os.path.exists(p.path):
                    skipped += 1
                    if not options['skip_missing']:
                        self.stdout.write(self.style.WARNING(f"File missing for id {p.id}: {p.path}"))
                    continue

                reps = DeepFace.represent(img_path=p.path,
                                          model_name=model,
                                          detector_backend='mtcnn',
                                          enforce_detection=False)

                if not reps or not isinstance(reps, list) or 'embedding' not in reps[0]:
                    self.stdout.write(self.style.WARNING(f"No embedding for id {p.id} ({p.path})"))
                    continue

                encoding = reps[0]['embedding']
                normed = l2_normalize(encoding)
                p.encoding = json.dumps(normed)
                p.save(update_fields=['encoding'])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated id {p.id}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed id {getattr(p,'id',None)}: {e}"))
                traceback.print_exc()
        self.stdout.write(self.style.SUCCESS(f"Done. updated={updated}, skipped={skipped}"))
