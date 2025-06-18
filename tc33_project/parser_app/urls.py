# parser_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    # Add other paths as needed, e.g., for download confirmation
]