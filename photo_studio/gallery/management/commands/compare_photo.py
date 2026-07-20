from django.core.management.base import BaseCommand
from gallery.models import Photo
from deepface import DeepFace
import numpy as np

# دالة التوحيد المهمة جداً (بدونها الأرقام تخرب)
def l2_normalize(v):
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    return (v / n) if n != 0 else v

class Command(BaseCommand):
    help = "أداة فحص يدوية لمقارنة صورة من الحاسبة مع قاعدة البيانات"

    def add_arguments(self, parser):
        parser.add_argument('--image', type=str, required=True, help='مسار الصورة الجديدة')

    def handle(self, *args, **options):
        new_image_path = options['image']
        self.stdout.write(f"🔎 جاري فحص الصورة: {new_image_path}")

        try:
            # استخدام نفس إعدادات الموقع SSD لضمان التطابق
            reps = DeepFace.represent(
                img_path=new_image_path, 
                model_name='Facenet', 
                detector_backend='ssd',  # مهم جداً
                enforce_detection=False
            )
            
            # تطبيق النورمالايز
            new_encoding = l2_normalize(reps[0]['embedding'])

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ فشل تحليل الصورة: {e}"))
            return

        photos = Photo.objects.exclude(encoding__isnull=True)
        similarities = []

        for photo in photos:
            # تحويل البيانات المخزنة إلى مصفوفة وتوحيدها
            if isinstance(photo.encoding, str):
                # في حال كانت مخزنة كنص خطأ
                try:
                    db_arr = np.array(eval(photo.encoding), dtype=float)
                except:
                    continue
            else:
                db_arr = np.array(photo.encoding, dtype=float)

            # مهم: تطبيق النورمالايز على بيانات الداتا بيس أيضاً إذا لم تكن كذلك
            # لكن بما أننا خزنناها وهي معمولة، نفترض أنها جاهزة، ولكن للاحتياط:
            # db_encoding = l2_normalize(db_arr) 
            # سنستخدمها مباشرة لأننا خزنناها صحيحة في السكربت السابق
            db_encoding = db_arr

            distance = np.linalg.norm(new_encoding - db_encoding)
            similarities.append((photo.path, distance))

        # ترتيب النتائج من الأقرب للأبعد
        similarities.sort(key=lambda x: x[1])

        self.stdout.write(self.style.SUCCESS("\n📸 النتائج (الأقل رقماً هو الأقرب):"))
        self.stdout.write("-" * 50)
        
        count = 0
        for path, dist in similarities[:5]: # عرض أول 5 نتائج
            result_str = f"الملف: {path} \n المسافة: {dist:.4f}"
            
            if dist < 0.50:
                self.stdout.write(self.style.SUCCESS(result_str + " (✅ تطابق)"))
            else:
                self.stdout.write(self.style.WARNING(result_str + " (❌ غير مطابق)"))
            
            self.stdout.write("-" * 20)
            count += 1