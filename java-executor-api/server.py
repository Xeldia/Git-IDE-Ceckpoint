import os
import uuid
import hmac
import hashlib
import tempfile
import subprocess
import shutil
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json

# API Security Configuration
API_SECRET = os.environ.get("API_SECRET", "REPLACE_WITH_STRONG_SECRET")
DOCKER_AVAILABLE = shutil.which("docker") is not None
MAX_EXECUTION_TIME = 5  # seconds
MAX_CODE_SIZE = 50000  # characters
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Job storage (in-memory for simplicity, use Redis/DB in production)
jobs = {}

app = FastAPI(title="Java Execution API", 
              description="Secure API for executing Java code",
              version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CodeRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_SIZE)
    stdin: Optional[str] = Field(None, max_length=1000)
    class_name: Optional[str] = None
    timeout: Optional[int] = MAX_EXECUTION_TIME

class CodeResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float

class JobResponse(BaseModel):
    job_id: str

class JobStatus(BaseModel):
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

# Security middleware
async def verify_signature(request: Request, authorization: Optional[str] = Header(None), x_signature: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.replace("Bearer ", "")
    if token != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # For GET requests, we don't verify body signature
    if request.method == "GET":
        return True
    
    # For POST/PUT, verify HMAC signature
    if not x_signature:
        raise HTTPException(status_code=401, detail="X-Signature header missing")
    
    body = await request.body()
    computed_signature = hmac.new(
        API_SECRET.encode(), 
        body, 
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(computed_signature, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True

# Helper functions
def extract_class_name(code: str) -> str:
    """Extract the class name from Java code or use Main as default."""
    import re
    match = re.search(r"public\s+class\s+(\w+)", code)
    if match:
        return match.group(1)
    return "Main"

def wrap_code_if_needed(code: str, class_name: str) -> str:
    """Wrap code in a class if it doesn't have one."""
    if "class" not in code:
        return f"""
public class {class_name} {{
    public static void main(String[] args) {{
        {code}
    }}
}}
"""
    return code

def execute_java_docker(code: str, class_name: str, stdin: Optional[str] = None, timeout: int = MAX_EXECUTION_TIME) -> Dict:
    """Execute Java code inside Docker container."""
    # Create temp directory for this run
    run_id = str(uuid.uuid4())
    temp_dir = os.path.join(TEMP_DIR, run_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Write code to file
        java_file = os.path.join(temp_dir, f"{class_name}.java")
        with open(java_file, "w") as f:
            f.write(code)
        
        # Write stdin to file if provided
        stdin_file = None
        if stdin:
            stdin_file = os.path.join(temp_dir, "input.txt")
            with open(stdin_file, "w") as f:
                f.write(stdin)
        
        # Run Docker container
        start_time = datetime.now()
        
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",  # No network access
            "--memory", "256m",   # Limit memory
            "--cpus", "0.5",      # Limit CPU
            "--pids-limit", "64", # Limit processes
            "-v", f"{temp_dir}:/code",
            "-w", "/code",
            "openjdk:17-slim",
            "bash", "-c", f"javac {class_name}.java && java {class_name} < {stdin_file if stdin_file else '/dev/null'}"
        ]
        
        process = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exit_code": process.returncode,
            "execution_time": execution_time
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out",
            "exit_code": 124,
            "execution_time": timeout
        }
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

def execute_java_local(code: str, class_name: str, stdin: Optional[str] = None, timeout: int = MAX_EXECUTION_TIME) -> Dict:
    """Execute Java code locally (fallback if Docker not available)."""
    # Create temp directory for this run
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write code to file
        java_file = os.path.join(temp_dir, f"{class_name}.java")
        with open(java_file, "w") as f:
            f.write(code)
        
        # Compile
        start_time = datetime.now()
        compile_process = subprocess.run(
            ["javac", java_file],
            capture_output=True,
            text=True
        )
        
        if compile_process.returncode != 0:
            return {
                "stdout": "",
                "stderr": compile_process.stderr,
                "exit_code": compile_process.returncode,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
        
        # Run
        try:
            run_process = subprocess.run(
                ["java", "-cp", temp_dir, class_name],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "stdout": run_process.stdout,
                "stderr": run_process.stderr,
                "exit_code": run_process.returncode,
                "execution_time": execution_time
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Execution timed out",
                "exit_code": 124,
                "execution_time": timeout
            }

# Routes
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "docker_available": DOCKER_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/run", response_model=CodeResponse, dependencies=[Depends(verify_signature)])
async def run_java(request: CodeRequest):
    """Synchronously run Java code and return results."""
    # Extract or use provided class name
    class_name = request.class_name or extract_class_name(request.code)
    
    # Wrap code if needed
    code = wrap_code_if_needed(request.code, class_name)
    
    # Execute code
    if DOCKER_AVAILABLE:
        result = execute_java_docker(code, class_name, request.stdin, request.timeout or MAX_EXECUTION_TIME)
    else:
        result = execute_java_local(code, class_name, request.stdin, request.timeout or MAX_EXECUTION_TIME)
    
    return result

@app.post("/submit", response_model=JobResponse, dependencies=[Depends(verify_signature)])
async def submit_job(request: CodeRequest):
    """Submit a job for asynchronous execution."""
    job_id = str(uuid.uuid4())
    
    # Store job
    jobs[job_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "request": request.dict(),
        "result": None,
        "error": None
    }
    
    # In a real implementation, you would queue this job for background processing
    # For simplicity, we'll process it immediately
    try:
        # Extract or use provided class name
        class_name = request.class_name or extract_class_name(request.code)
        
        # Wrap code if needed
        code = wrap_code_if_needed(request.code, class_name)
        
        # Update job status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # Execute code
        if DOCKER_AVAILABLE:
            result = execute_java_docker(code, class_name, request.stdin, request.timeout or MAX_EXECUTION_TIME)
        else:
            result = execute_java_local(code, class_name, request.stdin, request.timeout or MAX_EXECUTION_TIME)
        
        # Update job with result
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["result"] = result
    except Exception as e:
        # Update job with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["error"] = str(e)
    
    return {"job_id": job_id}

@app.get("/status/{job_id}", response_model=JobStatus, dependencies=[Depends(verify_signature)])
async def get_job_status(job_id: str):
    """Get the status of a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "status": job["status"],
        "created_at": job["created_at"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error")
    }

@app.get("/result/{job_id}", response_model=CodeResponse, dependencies=[Depends(verify_signature)])
async def get_job_result(job_id: str):
    """Get the result of a completed job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {job['status']}")
    
    if not job.get("result"):
        raise HTTPException(status_code=500, detail="Job completed but no result found")
    
    return job["result"]

# Clean up old jobs periodically (in a real app, use a background task)
@app.on_event("startup")
async def startup_event():
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8081, reload=True)