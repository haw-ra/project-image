import base64
import numpy as np
import time
from PIL import Image
from django.http import JsonResponse
from django.shortcuts import render
from deepface import DeepFace
from gallery.models import Photo
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSerializer, PhotoSerializer
import os

# دالة التوحيد
def l2_normalize(v):
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    return (v / n) if n != 0 else v

def index(request):
    return render(request, 'gallery/index.html')

def search_faces(request):
    if request.method != "POST" or "image" not in request.FILES:
        return JsonResponse([], safe=False)

    print("\n--- 🚀 بدأ طلب بحث جديد ---") # طباعة للمراقبة
    start_time = time.time()

    try:
        # 1. قراءة الصورة
        uploaded_file = request.FILES["image"]
        img = Image.open(uploaded_file).convert("RGB")
        img_arr = np.array(img)

        # 🔥 تعديل الألوان (مهم جداً)
        img_arr = img_arr[:, :, ::-1]

        # 2. استخراج البصمة
        reps = DeepFace.represent(
            img_path=img_arr,
            model_name="Facenet",
            detector_backend="ssd", 
            enforce_detection=False
        )
        
        if not reps:
             print("❌ لم يتم العثور على وجه في الصورة المرفوعة")
             return JsonResponse({"error": "No face detected"}, status=400)

        new_encoding = l2_normalize(reps[0]['embedding'])

        # 3. المقارنة
        photos = Photo.objects.exclude(encoding__isnull=True)
        results = []

        for photo in photos:
            # تحويل البيانات
            db_encoding = np.array(photo.encoding, dtype=float)
            # حساب المسافة
            distance = np.linalg.norm(new_encoding - db_encoding)
            
            results.append({
                "photo_obj": photo,
                "distance": distance
            })

        # ترتيب النتائج
        results.sort(key=lambda x: x["distance"])

        if not results:
            return JsonResponse([], safe=False)

        # أفضل نتيجة
        best_result = results[0]
        best_match = best_result["photo_obj"]
        best_dist = best_result["distance"]

        # طباعة النتيجة في الشاشة السوداء لتعرف ماذا يحدث
        print(f"✅ أقرب صورة: {best_match.path}")
        print(f"📊 مسافة الاختلاف: {best_dist:.4f}")

        # 🔥 التعديل هنا: غيرنا الرقم من 0.50 إلى 0.60
        # هذا سيسمح بقبول اللحية وتغييرات الشعر
        THRESHOLD = 0.68

        if best_dist < THRESHOLD:
            thumb_b64 = ""
            try:
                with open(best_match.path, "rb") as f:
                    thumb_b64 = base64.b64encode(f.read()).decode('utf-8')
            except:
                pass

            print(f"🎉 النتيجة مقبولة! (أقل من {THRESHOLD})")
            print(f"⏱ الوقت المستغرق: {time.time() - start_time:.2f} ثانية")

            return JsonResponse([{
                "path": best_match.path,
                "distance": float(best_dist),
                "thumbnail": thumb_b64
            }], safe=False)
        else:
            print(f"⛔ النتيجة مرفوضة (أكبر من {THRESHOLD}) - يعتبر شخصاً مختلفاً")
            return JsonResponse([], safe=False)

    except Exception as e:
        print(f"❌ Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# API Views for Mobile App

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user_id': user.id})
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

class PhotoUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. حفظ الصورة مؤقتاً أو إنشاء الكائن
        photo = Photo.objects.create(user=request.user, image=file_obj)
        
        # 2. استخراج البصمة باستخدام DeepFace
        try:
            img_path = photo.image.path
            reps = DeepFace.represent(
                img_path=img_path,
                model_name="Facenet",
                detector_backend="ssd",
                enforce_detection=False
            )
            
            if reps:
                encoding = l2_normalize(reps[0]['embedding'])
                photo.encoding = encoding.tolist()
                photo.save()
                return Response(PhotoSerializer(photo).data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "No face detected, but photo saved"}, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({"error": str(e), "photo_id": photo.id}, status=status.HTTP_201_CREATED)

class PhotoListView(generics.ListAPIView):
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Photo.objects.filter(user=self.request.user).order_by('-added_at')
    