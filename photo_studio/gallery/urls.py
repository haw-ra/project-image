from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('search/', views.search_faces, name='search_face'),
    
    # API Endpoints
    path('api/register/', views.RegisterView.as_view(), name='api_register'),
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    path('api/upload/', views.PhotoUploadView.as_view(), name='api_upload'),
    path('api/photos/', views.PhotoListView.as_view(), name='api_photos'),
]
