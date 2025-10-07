import os
import requests
import json
import hmac
import hashlib
import sys

# Configuration
JAVA_API_URL = os.environ.get("JAVA_API_URL", "http://localhost:8081")
JAVA_API_SECRET = os.environ.get("JAVA_API_SECRET", "REPLACE_WITH_STRONG_SECRET")

def generate_headers(body):
    """Generate authentication headers for API requests."""
    headers = {
        "Authorization": f"Bearer {JAVA_API_SECRET}",
        "Content-Type": "application/json"
    }
    
    # Add HMAC signature
    signature = hmac.new(
        JAVA_API_SECRET.encode(),
        json.dumps(body).encode(),
        hashlib.sha256
    ).hexdigest()
    headers["X-Signature"] = signature
    
    return headers

def test_connection():
    """Test connection to Java API server."""
    print("Testing connection to Java API server...")
    
    # Simple Java code to test
    code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Connection test successful!");
    }
}
"""
    
    body = {
        "code": code,
        "timeout": 5
    }
    
    try:
        # First, check health endpoint
        health_response = requests.get(f"{JAVA_API_URL}/health")
        if health_response.status_code != 200:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        
        print(f"✅ Health check successful: {health_response.json()}")
        
        # Test execution
        response = requests.post(
            f"{JAVA_API_URL}/run",
            json=body,
            headers=generate_headers(body)
        )
        
        if response.status_code != 200:
            print(f"❌ Connection test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ Connection test successful!")
        print(f"Output: {result.get('stdout', '')}")
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {JAVA_API_URL}")
        print("Make sure the Java API server is running and the URL is correct.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)