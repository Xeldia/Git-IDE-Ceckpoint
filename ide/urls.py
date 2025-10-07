from django.urls import path
from . import views
from .views import chat_view
from .views.java_execution import execute_java, submit_java_job, get_job_status, get_job_result

urlpatterns = [
    path("", views.index, name="index"),
    path("python-ide/", views.python_ide, name="python_ide"),
    path("java-ide/", views.java_ide, name="java_ide"),
    path('execute/', views.execute_java_code, name='execute_java'),
    
    # New Java execution API endpoints
    path('api/java/run/', execute_java, name='api_execute_java'),
    path('api/java/submit/', submit_java_job, name='api_submit_java_job'),
    path('api/java/status/<str:job_id>/', get_job_status, name='api_get_job_status'),
    path('api/java/result/<str:job_id>/', get_job_result, name='api_get_job_result'),
]

