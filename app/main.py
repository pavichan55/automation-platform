from fastapi import FastAPI
from datetime import datetime
import socket
import os

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Automation Platform Running",
        "status": "success",
        "environment": os.getenv("ENVIRONMENT", "default")
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "hostname": socket.gethostname()
    }

@app.get("/run-test")
def run_test():
    return {
        "test_name": "sample_ui_test",
        "result": "PASSED",
        "execution_time": "5 seconds"
    }