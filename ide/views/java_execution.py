from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from ..services.java_executor import JavaExecutorService

@csrf_exempt
@require_http_methods(["POST"])
def execute_java(request):
    """Execute Java code synchronously and return the result."""
    try:
        # Parse request body
        data = json.loads(request.body)
        code = data.get('code', '')
        stdin = data.get('stdin', '')
        
        if not code:
            return JsonResponse({
                'error': 'No code provided'
            }, status=400)
        
        # Execute code
        result = JavaExecutorService.execute_java(code, stdin)
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submit_java_job(request):
    """Submit a job for asynchronous execution and return the job ID."""
    try:
        # Parse request body
        data = json.loads(request.body)
        code = data.get('code', '')
        stdin = data.get('stdin', '')
        
        if not code:
            return JsonResponse({
                'error': 'No code provided'
            }, status=400)
        
        # Submit job
        result = JavaExecutorService.submit_job(code, stdin)
        
        if 'error' in result:
            return JsonResponse({
                'error': result['error']
            }, status=500)
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_job_status(request, job_id):
    """Get the status of a job."""
    try:
        # Get job status
        result = JavaExecutorService.get_job_status(job_id)
        
        if 'error' in result:
            return JsonResponse({
                'error': result['error']
            }, status=500)
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_job_result(request, job_id):
    """Get the result of a completed job."""
    try:
        # Get job result
        result = JavaExecutorService.get_job_result(job_id)
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)