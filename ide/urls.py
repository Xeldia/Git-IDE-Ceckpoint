from django.urls import path
from . import views
from .views import chat_view

urlpatterns = [
    path("", views.index, name="index"),
    path("python/", views.python_ide, name="python_ide"),
    path("java/", views.java_ide, name="java_ide"),
    path('execute/', views.execute_java_code, name='execute_java'),
]

