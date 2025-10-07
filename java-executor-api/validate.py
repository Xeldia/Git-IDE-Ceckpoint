import requests
import hmac
import hashlib
import json
import os
import time
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# Configuration
API_URL = os.environ.get("JAVA_API_URL", "http://localhost:8081")
API_SECRET = os.environ.get("API_SECRET", "REPLACE_WITH_STRONG_SECRET")

def print_header(text):
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f" {text}")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")

def generate_headers(body=None):
    """Generate authentication headers for API requests."""
    headers = {
        "Authorization": f"Bearer {API_SECRET}",
        "Content-Type": "application/json"
    }
    
    # Add HMAC signature for requests with body
    if body:
        body_str = json.dumps(body)
        signature = hmac.new(
            API_SECRET.encode(),
            body_str.encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Signature"] = signature
        
    return headers

def test_health_check():
    """Test the health check endpoint."""
    print_header("Testing Health Check Endpoint")
    
    try:
        response = requests.get(f"{API_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check successful: {data}")
            print_info(f"Docker available: {data.get('docker_available', False)}")
            return True
        else:
            print_error(f"Health check failed with status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error connecting to API: {str(e)}")
        return False

def test_java_execution():
    """Test Java code execution."""
    print_header("Testing Java Code Execution")
    
    # Simple Java code to test
    code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
        System.out.println("Current time: " + java.time.LocalDateTime.now());
        System.out.println("Java version: " + System.getProperty("java.version"));
    }
}
"""
    
    body = {
        "code": code,
        "timeout": 5
    }
    
    try:
        response = requests.post(
            f"{API_URL}/run",
            json=body,
            headers=generate_headers(body)
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Java execution successful")
            print_info(f"Stdout: {data.get('stdout', '')}")
            print_info(f"Stderr: {data.get('stderr', '')}")
            print_info(f"Exit code: {data.get('exit_code', -1)}")
            print_info(f"Execution time: {data.get('execution_time', 0)} seconds")
            return True
        else:
            print_error(f"Java execution failed with status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error executing Java code: {str(e)}")
        return False

def test_async_execution():
    """Test asynchronous Java code execution."""
    print_header("Testing Asynchronous Java Execution")
    
    # Simple Java code to test
    code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from async Java execution!");
        try {
            Thread.sleep(1000); // Sleep for 1 second
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println("Finished async execution");
    }
}
"""
    
    body = {
        "code": code,
        "timeout": 5
    }
    
    try:
        # Submit job
        submit_response = requests.post(
            f"{API_URL}/submit",
            json=body,
            headers=generate_headers(body)
        )
        
        if submit_response.status_code != 200:
            print_error(f"Job submission failed with status code {submit_response.status_code}")
            print_error(f"Response: {submit_response.text}")
            return False
        
        job_data = submit_response.json()
        job_id = job_data.get("job_id")
        
        if not job_id:
            print_error("No job ID returned")
            return False
        
        print_success(f"Job submitted successfully with ID: {job_id}")
        
        # Check job status
        max_attempts = 10
        for attempt in range(max_attempts):
            print_info(f"Checking job status (attempt {attempt + 1}/{max_attempts})...")
            
            status_response = requests.get(
                f"{API_URL}/status/{job_id}",
                headers=generate_headers()
            )
            
            if status_response.status_code != 200:
                print_error(f"Status check failed with status code {status_response.status_code}")
                print_error(f"Response: {status_response.text}")
                return False
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            print_info(f"Job status: {status}")
            
            if status == "completed":
                break
            elif status == "failed":
                print_error("Job failed")
                print_error(f"Error: {status_data.get('error', 'Unknown error')}")
                return False
            
            time.sleep(1)
        
        # Get job result
        result_response = requests.get(
            f"{API_URL}/result/{job_id}",
            headers=generate_headers()
        )
        
        if result_response.status_code != 200:
            print_error(f"Result retrieval failed with status code {result_response.status_code}")
            print_error(f"Response: {result_response.text}")
            return False
        
        result_data = result_response.json()
        print_success("Async job completed successfully")
        print_info(f"Stdout: {result_data.get('stdout', '')}")
        print_info(f"Stderr: {result_data.get('stderr', '')}")
        print_info(f"Exit code: {result_data.get('exit_code', -1)}")
        print_info(f"Execution time: {result_data.get('execution_time', 0)} seconds")
        
        return True
    except Exception as e:
        print_error(f"Error in async execution: {str(e)}")
        return False

def test_error_handling():
    """Test error handling with invalid Java code."""
    print_header("Testing Error Handling")
    
    # Invalid Java code
    code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("This code has an error);  // Missing closing quote
        int x = 10 / 0;  // Division by zero
    }
}
"""
    
    body = {
        "code": code,
        "timeout": 5
    }
    
    try:
        response = requests.post(
            f"{API_URL}/run",
            json=body,
            headers=generate_headers(body)
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("stderr") and data.get("exit_code", 0) != 0:
                print_success("Error handling working correctly")
                print_info(f"Stderr: {data.get('stderr', '')}")
                print_info(f"Exit code: {data.get('exit_code', -1)}")
                return True
            else:
                print_error("Error handling not working correctly - no error detected in invalid code")
                return False
        else:
            print_error(f"Request failed with status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error testing error handling: {str(e)}")
        return False

def main():
    print_header("Java Executor API Validation Script")
    print_info(f"API URL: {API_URL}")
    
    # Run tests
    health_check_success = test_health_check()
    
    if not health_check_success:
        print_error("Health check failed. Make sure the API server is running.")
        sys.exit(1)
    
    java_execution_success = test_java_execution()
    async_execution_success = test_async_execution()
    error_handling_success = test_error_handling()
    
    # Summary
    print_header("Validation Summary")
    print(f"Health Check: {'✓' if health_check_success else '✗'}")
    print(f"Java Execution: {'✓' if java_execution_success else '✗'}")
    print(f"Async Execution: {'✓' if async_execution_success else '✗'}")
    print(f"Error Handling: {'✓' if error_handling_success else '✗'}")
    
    if all([health_check_success, java_execution_success, async_execution_success, error_handling_success]):
        print_success("All tests passed! Your Java Executor API is working correctly.")
    else:
        print_error("Some tests failed. Please check the output above for details.")

if __name__ == "__main__":
    main()