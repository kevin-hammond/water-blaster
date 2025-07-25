#!/usr/bin/env python3
"""
Setup script for Arducam 64MP OV64A40 camera on Raspberry Pi 5
This script helps configure the camera and install dependencies.
"""

import subprocess
import sys
import os
import re

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"✗ {description} failed")
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"✗ {description} failed with exception: {e}")
        return False

def check_kernel_version():
    """Check if the kernel version is compatible."""
    try:
        result = subprocess.run("uname -r", shell=True, capture_output=True, text=True)
        kernel_version = result.stdout.strip()
        print(f"Current kernel version: {kernel_version}")
        
        # Extract version numbers more robustly
        # Handle formats like "6.1.34+rpt" or "6.1.34-rpi" 
        version_parts = kernel_version.split('.')
        
        if len(version_parts) < 3:
            print("✗ Unexpected kernel version format")
            return False
        
        major = int(version_parts[0])
        minor = int(version_parts[1])
        
        # Extract patch version by removing non-numeric characters
        patch_str = version_parts[2]
        # Remove everything after +, -, or first non-digit character
        patch_match = re.match(r'(\d+)', patch_str)
        if patch_match:
            patch = int(patch_match.group(1))
        else:
            # If we can't parse patch, assume it's 0
            patch = 0
        
        print(f"Parsed version: {major}.{minor}.{patch}")
        
        # Check if version is 6.1.73 or later
        if major > 6 or (major == 6 and minor > 1) or (major == 6 and minor == 1 and patch >= 73):
            print("✓ Kernel version is compatible")
            return True
        else:
            print("✗ Kernel version is too old. Please update with 'sudo apt update && sudo apt upgrade'")
            return False
    except Exception as e:
        print(f"✗ Could not check kernel version: {e}")
        return False

def configure_camera():
    """Configure the camera in config.txt."""
    config_file = "/boot/firmware/config.txt"
    
    if not os.path.exists(config_file):
        print(f"✗ Config file {config_file} not found")
        return False
    
    print(f"\nConfiguring camera in {config_file}...")
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        # Check if camera is already configured
        camera_configured = False
        for line in lines:
            if 'dtoverlay=ov64a40' in line:
                camera_configured = True
                break
        
        if camera_configured:
            print("✓ Camera is already configured in config.txt")
            return True
        
        # Add camera configuration
        print("Adding camera configuration...")
        
        # Find [all] section or add it
        all_section_found = False
        insert_index = len(lines)
        
        for i, line in enumerate(lines):
            if line.strip() == '[all]':
                all_section_found = True
                insert_index = i + 1
                break
        
        if not all_section_found:
            lines.append('\n[all]\n')
            insert_index = len(lines)
        
        # Insert camera configuration
        camera_config = [
            '# Arducam 64MP OV64A40 Camera Configuration\n',
            'dtoverlay=ov64a40,link-frequency=456000000\n',
            'camera_auto_detect=0\n',
            '\n'
        ]
        
        for i, config_line in enumerate(camera_config):
            lines.insert(insert_index + i, config_line)
        
        # Write back to file
        with open(config_file, 'w') as f:
            f.writelines(lines)
        
        print("✓ Camera configuration added to config.txt")
        print("  Note: A reboot is required for changes to take effect")
        return True
        
    except Exception as e:
        print(f"✗ Failed to configure camera: {e}")
        print("  You may need to run this script with sudo")
        return False

def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    
    # Install system packages first (recommended approach)
    system_packages = [
        'python3-picamera2',
        'python3-opencv',
        'python3-lgpio',
        'python3-numpy',
        'python3-pip'
    ]
    
    print("Installing system packages...")
    for package in system_packages:
        if not run_command(f"sudo apt install -y {package}", f"Installing {package}"):
            print(f"  Warning: Failed to install {package}")
    
    # Check if pip packages are needed (fallback)
    pip_packages = {
        'picamera2': 'picamera2',
        'opencv-python': 'cv2',
        'lgpio': 'lgpio',
        'numpy': 'numpy'
    }
    
    print("Checking if additional pip packages are needed...")
    for package, import_name in pip_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package} is available")
        except ImportError:
            print(f"ℹ {package} not found, attempting to install...")
            
            # Try different installation methods
            install_methods = [
                f"pip3 install {package}",
                f"pip3 install --user {package}",
                f"pip3 install --break-system-packages {package}"
            ]
            
            installed = False
            for method in install_methods:
                if run_command(method, f"Installing {package} via pip"):
                    installed = True
                    break
            
            if not installed:
                print(f"  Warning: Could not install {package}")
    
    return True

def check_lgd_daemon():
    """Check if lgd daemon is running or install it if needed."""
    # First check if the service exists
    result = subprocess.run("systemctl list-unit-files | grep lgd", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("ℹ lgd daemon not found. Installing...")
        # Try to install lgpio if not present
        if not run_command("sudo apt install -y python3-lgpio", "Installing lgpio package"):
            print("  Warning: Could not install lgpio package")
        
        # Check if lgd binary exists
        result = subprocess.run("which lgd", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("ℹ lgd binary not found. This is normal on some systems.")
            print("  The lgpio library should still work without the daemon.")
            return True
        
        # If lgd exists, try to create a service (this is optional)
        print("  Note: lgd daemon is optional on this system")
        return True
    
    # If the service exists, check if it's running
    result = subprocess.run("systemctl is-active lgd", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ lgd daemon is running")
        return True
    else:
        print("ℹ lgd daemon not running, attempting to start...")
        if run_command("sudo systemctl start lgd", "Starting lgd daemon"):
            if run_command("sudo systemctl enable lgd", "Enabling lgd daemon"):
                print("✓ lgd daemon is now running and enabled")
                return True
        else:
            print("  Note: lgd daemon failed to start, but GPIO may still work")
            return True  # Return True because GPIO might still work without daemon

def main():
    print("Arducam 64MP OV64A40 Setup Script for Raspberry Pi 5")
    print("=" * 50)
    
    # Check if running as root for config file modification
    if os.geteuid() != 0:
        print("Note: Some operations require root privileges")
        print("You may need to run: sudo python3 setup_arducam.py")
        print()
    
    # Step 1: Update system
    print("Step 1: Updating system...")
    run_command("sudo apt update && sudo apt upgrade -y", "System update")
    
    # Step 2: Check kernel version
    print("\nStep 2: Checking kernel version...")
    if not check_kernel_version():
        print("Please update your system and run this script again")
        return
    
    # Step 3: Install dependencies
    print("\nStep 3: Installing dependencies...")
    install_dependencies()
    
    # Step 4: Check lgd daemon
    print("\nStep 4: Checking lgd daemon...")
    check_lgd_daemon()
    
    # Step 5: Configure camera
    print("\nStep 5: Configuring camera...")
    if configure_camera():
        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Reboot your Raspberry Pi: sudo reboot")
        print("2. Connect your Arducam 64MP OV64A40 camera to the CAM1 port")
        print("3. Connect your servo motor to GPIO pin 18")
        print("4. Run the minimal script: python3 minimal_camera_servo.py")
        print("\nHardware connections:")
        print("- Camera: Connect to CAM1 port (22-pin connector)")
        print("- Servo: Connect signal wire to GPIO 18, VCC to 5V, GND to GND")
    else:
        print("\n✗ Setup failed. Please check the errors above and try again.")

if __name__ == "__main__":
    main() 