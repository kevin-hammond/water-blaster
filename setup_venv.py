#!/usr/bin/env python3
"""
Setup script to create a virtual environment for the camera project
This avoids the "externally managed environment" issue
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return True
        else:
            print(f"✗ {description} failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description} failed with exception: {e}")
        return False

def create_virtual_environment():
    """Create and configure a virtual environment."""
    venv_name = "camera_env"
    
    print(f"Creating virtual environment: {venv_name}")
    
    # Create virtual environment
    if not run_command(f"python3 -m venv {venv_name}", "Creating virtual environment"):
        return False
    
    # Install packages in virtual environment
    packages = [
        'picamera2',
        'opencv-python',
        'lgpio',
        'numpy'
    ]
    
    for package in packages:
        if not run_command(f"{venv_name}/bin/pip install {package}", f"Installing {package}"):
            print(f"  Warning: Failed to install {package}")
    
    # Create activation script
    activation_script = f"""#!/bin/bash
# Activation script for camera environment
echo "Activating camera environment..."
source {venv_name}/bin/activate
echo "Virtual environment activated!"
echo "You can now run: python3 minimal_camera_servo.py"
echo "To deactivate, run: deactivate"
"""
    
    with open("activate_camera_env.sh", "w") as f:
        f.write(activation_script)
    
    os.chmod("activate_camera_env.sh", 0o755)
    
    print("\n" + "=" * 50)
    print("Virtual environment setup complete!")
    print("\nTo use the virtual environment:")
    print("1. Activate it: source activate_camera_env.sh")
    print("2. Run your scripts: python3 minimal_camera_servo.py")
    print("3. Deactivate when done: deactivate")
    print("\nAlternatively, run scripts directly:")
    print(f"  {venv_name}/bin/python3 minimal_camera_servo.py")
    
    return True

def main():
    print("Virtual Environment Setup for Camera Project")
    print("=" * 50)
    print("This creates a virtual environment to avoid 'externally managed' errors")
    
    if create_virtual_environment():
        print("\n✓ Setup completed successfully!")
    else:
        print("\n✗ Setup failed.")

if __name__ == "__main__":
    main() 