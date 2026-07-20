from django.core.management.base import BaseCommand
from gallery.models import Photo
import os
import numpy as np
from deepface import DeepFace

# دالة التوحيد
def l2_normalize(v):
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    return (v / n).tolist() if n != 0 else v.tolist()

class Command(BaseCommand):
    help = "استيراد ذكي: يضيف الصور الجديدة فقط ويتخطى القديمة"

    def add_arguments(self, parser):
        parser.add_argument("--root", type=str, required=True)

    def handle(self, *args, **opt):
        root = opt["root"]
        
        # 1. جلب كل الصور من قاعدة البيانات لمعرفة الموجود مسبقاً
        existing_paths = set(Photo.objects.values_list('path', flat=True))
        
        new_count = 0
        skipped_count = 0

        self.stdout.write(f"📂 المجلد: {root}")

        for dp, _, files in os.walk(root):
            for file in files:
                if not file.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue

                full_path = os.path.join(dp, file)

                # 🔥 هنا الذكاء: إذا الصورة موجودة، اعبرها فوراً
                if full_path in existing_paths:
                    skipped_count += 1
                    continue

                # إذا وصلنا هنا، يعني الصورة جديدة
                try:
                    embedding_objs = DeepFace.represent(
                        img_path=full_path,
                        model_name="Facenet",
                        detector_backend="ssd",  # توحيد الكاشف
                        enforce_detection=False
                    )

                    if len(embedding_objs) > 0:
                        raw_embedding = embedding_objs[0]["embedding"]
                        norm_embedding = l2_normalize(raw_embedding)

                        Photo.objects.create(
                            path=full_path,
                            encoding=norm_embedding
                        )

                        new_count += 1
                        self.stdout.write(self.style.SUCCESS(f"✔ جديد: {file}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"⚠ خطأ: {file}"))

        self.stdout.write(self.style.SUCCESS(f"--------------------------------"))
        self.stdout.write(self.style.SUCCESS(f"🎉 تم الانتهاء!"))
        self.stdout.write(f"📥 تمت إضافة: {new_count} صورة جديدة")
        self.stdout.write(f"⏩ تم تخطي: {skipped_count} صورة قديمة")