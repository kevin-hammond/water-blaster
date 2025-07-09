#!/usr/bin/env python3
"""
Setup script for Arducam 64MP OV64A40 camera on Raspberry Pi 5
This script helps configure the camera and install dependencies.
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
        
        # Extract version numbers
        version_parts = kernel_version.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1])
        patch = int(version_parts[2].split('-')[0])
        
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
    packages = [
        'picamera2',
        'opencv-python',
        'lgpio',
        'numpy'
    ]
    
    for package in packages:
        if not run_command(f"pip3 install {package}", f"Installing {package}"):
            print(f"  Warning: Failed to install {package}")
    
    return True

def check_lgd_daemon():
    """Check if lgd daemon is running."""
    result = subprocess.run("systemctl is-active lgd", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ lgd daemon is running")
        return True
    else:
        print("✗ lgd daemon is not running")
        print("  Starting lgd daemon...")
        if run_command("sudo systemctl start lgd", "Starting lgd daemon"):
            if run_command("sudo systemctl enable lgd", "Enabling lgd daemon"):
                print("✓ lgd daemon is now running and enabled")
                return True
        return False

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