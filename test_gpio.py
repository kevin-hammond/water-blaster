#!/usr/bin/env python3
"""
Simple test script to verify GPIO functionality with lgpio library
"""

import time
import lgpio

def test_gpio():
    """Test basic GPIO functionality."""
    print("Testing GPIO functionality...")
    
    try:
        # Open GPIO chip
        h = lgpio.gpiochip_open(0)
        print("✓ GPIO chip opened successfully")
        
        # Test claiming a pin for output (pin 18 for servo)
        SERVO_PIN = 18
        lgpio.gpio_claim_output(h, SERVO_PIN)
        print(f"✓ GPIO pin {SERVO_PIN} claimed for output")
        
        # Test PWM functionality
        print("Testing PWM (servo control)...")
        
        # Test different servo positions
        positions = [1000, 1500, 2000, 1500]  # microseconds
        
        for i, pos in enumerate(positions):
            print(f"  Setting servo position {i+1}/4: {pos}μs")
            lgpio.tx_servo(h, SERVO_PIN, pos, 50)  # 50Hz frequency
            time.sleep(1)
        
        print("✓ PWM test completed")
        
        # Clean up
        lgpio.tx_servo(h, SERVO_PIN, 0, 0)  # Stop PWM
        lgpio.gpiochip_close(h)
        print("✓ GPIO resources cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ GPIO test failed: {e}")
        return False

if __name__ == "__main__":
    if test_gpio():
        print("\n✓ GPIO test passed! The system is ready for servo control.")
    else:
        print("\n✗ GPIO test failed. Check your system configuration.") 