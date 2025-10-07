import os
import hmac
import hashlib
import json
import requests
from django.conf import settings

# Configuration
JAVA_API_URL = os.environ.get("JAVA_API_URL", "http://localhost:8081")
JAVA_API_SECRET = os.environ.get("JAVA_API_SECRET", "REPLACE_WITH_STRONG_SECRET")
REQUEST_TIMEOUT = 10  # seconds

class JavaExecutorService:
    """Service to communicate with the Java Executor API."""
    
    @staticmethod
    def _get_headers(body=None):
        """Generate authentication headers for API requests."""
        headers = {
            "Authorization": f"Bearer {JAVA_API_SECRET}",
            "Content-Type": "application/json"
        }
        
        # Add HMAC signature for POST requests with body
        if body:
            signature = hmac.new(
                JAVA_API_SECRET.encode(),
                json.dumps(body).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Signature"] = signature
            
        return headers
    
    @classmethod
    def execute_java(cls, code, stdin=None, timeout=5):
        """Execute Java code synchronously and return the result."""
        endpoint = f"{JAVA_API_URL}/run"
        
        # Prepare request body
        body = {
            "code": code,
            "timeout": timeout
        }
        if stdin:
            body["stdin"] = stdin
            
        # Make API request
        try:
            response = requests.post(
                endpoint,
                json=body,
                headers=cls._get_headers(body),
                timeout=REQUEST_TIMEOUT
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "stdout": "",
                    "stderr": f"API Error: {response.status_code} - {response.text}",
                    "exit_code": -1,
                    "execution_time": 0
                }
        except requests.RequestException as e:
            return {
                "stdout": "",
                "stderr": f"Connection Error: {str(e)}",
                "exit_code": -1,
                "execution_time": 0
            }
    
    @classmethod
    def submit_job(cls, code, stdin=None, timeout=5):
        """Submit a job for asynchronous execution and return the job ID."""
        endpoint = f"{JAVA_API_URL}/submit"
        
        # Prepare request body
        body = {
            "code": code,
            "timeout": timeout
        }
        if stdin:
            body["stdin"] = stdin
            
        # Make API request
        try:
            response = requests.post(
                endpoint,
                json=body,
                headers=cls._get_headers(body),
                timeout=REQUEST_TIMEOUT
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API Error: {response.status_code} - {response.text}"
                }
        except requests.RequestException as e:
            return {
                "error": f"Connection Error: {str(e)}"
            }
    
    @classmethod
    def get_job_status(cls, job_id):
        """Get the status of a job."""
        endpoint = f"{JAVA_API_URL}/status/{job_id}"
        
        # Make API request
        try:
            response = requests.get(
                endpoint,
                headers=cls._get_headers(),
                timeout=REQUEST_TIMEOUT
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"API Error: {response.status_code} - {response.text}"
                }
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": f"Connection Error: {str(e)}"
            }
    
    @classmethod
    def get_job_result(cls, job_id):
        """Get the result of a completed job."""
        endpoint = f"{JAVA_API_URL}/result/{job_id}"
        
        # Make API request
        try:
            response = requests.get(
                endpoint,
                headers=cls._get_headers(),
                timeout=REQUEST_TIMEOUT
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "stdout": "",
                    "stderr": f"API Error: {response.status_code} - {response.text}",
                    "exit_code": -1,
                    "execution_time": 0
                }
        except requests.RequestException as e:
            return {
                "stdout": "",
                "stderr": f"Connection Error: {str(e)}",
                "exit_code": -1,
                "execution_time": 0
            }