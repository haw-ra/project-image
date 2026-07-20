from django.db import models
from django.contrib.auth.models import User

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    image = models.ImageField(upload_to='uploaded_photos/', null=True, blank=True)
    # المسار الحقيقي للصورة على القرص أو الفلاش
    path = models.CharField(max_length=500, unique=True, null=True, blank=True) 
    # بصمة الوجه (Vector)
    encoding = models.JSONField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo {self.id} - {self.user.username if self.user else 'No User'}"
