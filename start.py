#!/usr/bin/env python3
"""
TalkToMe - Easy Startup Script
Chạy cả frontend và backend từ một command
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def setup_backend():
    """Setup backend environment"""
    print("\n" + "="*50)
    print("Setting up Backend...")
    print("="*50)
    
    os.chdir(BACKEND_DIR)
    
    # Install dependencies
    print("Installing backend dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("✅ Backend dependencies installed")
    else:
        print("❌ Failed to install dependencies")
        print(result.stderr.decode())
        return False
    
    return True


def setup_frontend():
    """Setup frontend environment"""
    print("\n" + "="*50)
    print("Setting up Frontend...")
    print("="*50)
    
    os.chdir(FRONTEND_DIR)
    
    # Install dependencies
    print("Installing frontend dependencies...")
    result = subprocess.run(
        ["npm", "install", "--legacy-peer-deps"],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("✅ Frontend dependencies installed")
    else:
        print("⚠️ NPM install had issues (may still work)")
    
    return True


def run_backend():
    """Run backend server"""
    print("\n" + "="*50)
    print("Starting Backend (Port 5000)...")
    print("="*50)
    
    os.chdir(BACKEND_DIR)
    
    # Set environment
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DATABASE_URL'] = 'sqlite:///talktome.db'
    os.environ['SECRET_KEY'] = 'dev-secret-key-12345'
    
    # Run Flask
    subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("✅ Backend started at http://localhost:5000")
    return True


def run_frontend():
    """Run frontend server"""
    print("\n" + "="*50)
    print("Starting Frontend (Port 3000)...")
    print("="*50)
    
    os.chdir(FRONTEND_DIR)
    
    # Set environment
    os.environ['REACT_APP_API_URL'] = 'http://localhost:5000'
    
    # Run npm start
    subprocess.Popen(
        ["npm", "start"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("✅ Frontend starting at http://localhost:3000")
    return True


def main():
    """Main startup sequence"""
    print("\n" + "🚀 "*20)
    print("TalkToMe - Easy Startup")
    print("🚀 "*20)
    
    # Setup
    if not setup_backend():
        print("❌ Backend setup failed")
        return
    
    if not setup_frontend():
        print("❌ Frontend setup failed")
        return
    
    # Run servers
    print("\n" + "="*50)
    print("Starting Servers...")
    print("="*50)
    
    run_backend()
    time.sleep(2)  # Wait for backend to start
    
    run_frontend()
    
    # Display info
    print("\n" + "="*50)
    print("✅ TalkToMe is Running!")
    print("="*50)
    print("\n📱 Access Application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:5000")
    print("\n🧪 Test Account:")
    print("   Email:    test@example.com")
    print("   Password: password123")
    print("\n📖 Workflow:")
    print("   1. Login at http://localhost:3000")
    print("   2. Create feedback session")
    print("   3. Copy UID code")
    print("   4. Visit http://localhost:3000/feedback/[UID]")
    print("   5. Submit feedback anonymously")
    print("   6. View analytics on dashboard")
    print("\n🛑 To stop:")
    print("   Press CTRL+C in terminal")
    print("\n" + "="*50 + "\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down TalkToMe...")
        print("✅ Done!")


if __name__ == "__main__":
    main()
