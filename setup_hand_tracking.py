#!/usr/bin/env python3
"""
Setup script for hand tracking dependencies
"""

import subprocess
import sys

def install_dependencies():
    """Install required dependencies for hand tracking"""
    
    print("Installing dependencies for hand tracking...")
    
    try:
        # Install from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ All dependencies installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if install_dependencies():
        print("\nSetup complete! You can now run the hand tracking script with:")
        print("python3 minimal_camera_servo.py")
    else:
        print("\nSetup failed. Please check the error messages above.") 