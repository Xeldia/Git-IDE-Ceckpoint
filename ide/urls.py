from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("python-ide/", views.python_ide, name="python_ide"),
    path("java-ide/", views.java_ide, name="java_ide"),
]
