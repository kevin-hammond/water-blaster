#!/usr/bin/env python3
"""
Simple setup script - installs dependencies directly
"""

import subprocess
import sys

def install_simple():
    """Install required packages simply"""
    
    print("Installing required packages...")
    
    packages = [
        "opencv-python",
        "mediapipe", 
        "lgpio"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
            print(f"✓ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    print("✓ All packages installed!")
    print("\nYou can now run:")
    print("python3 minimal_camera_servo.py")
    
    return True

if __name__ == "__main__":
    install_simple() 