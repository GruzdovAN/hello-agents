#!/usr/bin/env python3
"""InnoCore AI — простой сценарий запуска
Yanchuang Intelligent Core — простой скрипт запуска"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Run the full InnoCore AI application"""
    print("Starting InnoCore AI...")
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Start server with the full API
    print("Server will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()