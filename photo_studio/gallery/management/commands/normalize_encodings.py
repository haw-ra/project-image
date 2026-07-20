# gallery/management/commands/normalize_encodings.py
from django.core.management.base import BaseCommand
from gallery.models import Photo
import numpy as np
import json

def l2_normalize(vec):
    v = np.array(vec, dtype=float)
    n = np.linalg.norm(v)
    return (v / n).tolist() if n != 0 else v.tolist()

class Command(BaseCommand):
    help = "Normalize existing encodings stored in DB (one-time)"

    def handle(self, *args, **options):
        updated = 0
        for p in Photo.objects.all():
            if not p.encoding:
                continue
            if isinstance(p.encoding, str):
                try:
                    arr = json.loads(p.encoding)
                except Exception:
                    arr = eval(p.encoding)
            else:
                arr = p.encoding
            normed = l2_normalize(arr)
            p.encoding = normed
            p.save(update_fields=['encoding'])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"✅ normalized {updated} records"))
