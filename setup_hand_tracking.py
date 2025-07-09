#!/usr/bin/env python3
"""
Setup script for hand tracking dependencies
Creates a virtual environment and installs dependencies
"""

import subprocess
import sys
import os
import venv

def create_virtual_environment():
    """Create a virtual environment for the project"""
    venv_path = "hand_tracking_venv"
    
    if os.path.exists(venv_path):
        print(f"Virtual environment '{venv_path}' already exists.")
        return venv_path
    
    print(f"Creating virtual environment at '{venv_path}'...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✓ Virtual environment created successfully!")
        return venv_path
    except Exception as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return None

def get_venv_python_path(venv_path):
    """Get the Python executable path in the virtual environment"""
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")

def install_dependencies_in_venv(venv_path):
    """Install required dependencies in the virtual environment"""
    
    python_path = get_venv_python_path(venv_path)
    
    print("Installing dependencies in virtual environment...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install from requirements.txt
        subprocess.check_call([python_path, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ All dependencies installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    return True

def create_activation_script(venv_path):
    """Create a script to easily activate the environment and run the program"""
    
    if sys.platform == "win32":
        script_name = "run_hand_tracking.bat"
        script_content = f"""@echo off
call {venv_path}\\Scripts\\activate.bat
python minimal_camera_servo.py
pause
"""
    else:
        script_name = "run_hand_tracking.sh"
        script_content = f"""#!/bin/bash
source {venv_path}/bin/activate
python3 minimal_camera_servo.py
"""
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    if sys.platform != "win32":
        os.chmod(script_name, 0o755)
    
    print(f"✓ Created activation script: {script_name}")
    return script_name

def main():
    """Main setup function"""
    
    print("=== Hand Tracking Setup ===")
    print("This script will create a virtual environment and install dependencies.")
    print()
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    if not venv_path:
        print("Setup failed at virtual environment creation.")
        return False
    
    # Install dependencies
    if not install_dependencies_in_venv(venv_path):
        print("Setup failed at dependency installation.")
        return False
    
    # Create activation script
    script_name = create_activation_script(venv_path)
    
    print()
    print("=== Setup Complete! ===")
    print()
    print("To run the hand tracking script, you have two options:")
    print()
    print("Option 1 - Use the activation script:")
    if sys.platform == "win32":
        print(f"  {script_name}")
    else:
        print(f"  ./{script_name}")
    print()
    print("Option 2 - Manually activate the virtual environment:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate.bat")
    else:
        print(f"  source {venv_path}/bin/activate")
    print("  python3 minimal_camera_servo.py")
    print()
    print("Note: The virtual environment contains all required dependencies.")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check your Python installation and try again.") 