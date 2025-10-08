from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import logging

logger = logging.getLogger(__name__)

def chat_view(request):
    logger.info("Accessing chat view")
    return render(request, "ide/chat.html")

def index(request):
    logger.info("Accessing index view")
    try:
        return render(request, "ide/index.html")
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)

def python_ide(request):
    return render(request, "ide/python-ide.html")

def java_ide(request):
    return render(request, "ide/java-ide.html")


# Run Python code using Piston API
@csrf_exempt
def execute_java_code(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code', '')
        stdin = data.get('stdin', '')  # for user input
        
        # Piston API endpoint
        url = 'https://emkc.org/api/v2/piston/execute'
        
        payload = {
            'language': 'java',
            'version': '15.0.2',
            'files': [
                {
                    'content': code
                }
            ],
            'stdin': stdin
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            run_data = result.get('run', {})
            output = run_data.get('stdout', '')
            error = run_data.get('stderr', '')
            
            return JsonResponse({
                'output': output if output else error,
                'success': run_data.get('code', 1) == 0
            })
        except requests.Timeout:
            return JsonResponse({'output': 'Execution timed out', 'success': False})
        except Exception as e:
            return JsonResponse({'output': f'Error: {str(e)}', 'success': False})
    
    return JsonResponse({'output': 'Invalid request', 'success': False}, status=400)