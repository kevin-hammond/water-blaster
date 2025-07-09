#!/usr/bin/env python3
"""
Minimal Camera and Servo Control for Raspberry Pi 5 with Arducam 64MP OV64A40
This script demonstrates basic camera capture and servo motor control.
"""

import time
import cv2
import lgpio
from picamera2 import Picamera2
import datetime

# Configuration
SERVO_PIN = 18              # GPIO pin for servo (PWM)
SERVO_MIN_PULSE = 800       # Minimum pulse width in microseconds
SERVO_MAX_PULSE = 2200      # Maximum pulse width in microseconds
SERVO_CENTER = (SERVO_MIN_PULSE + SERVO_MAX_PULSE) // 2

# Camera settings
FRAME_WIDTH = 1920          # Use higher resolution for Arducam 64MP
FRAME_HEIGHT = 1080

def main():
    # Initialize GPIO
    try:
        h = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(h, SERVO_PIN)
        print("GPIO initialized successfully")
    except Exception as e:
        print(f"Failed to initialize GPIO: {e}")
        return

    # Initialize Camera
    try:
        picam2 = Picamera2()
        
        # Configure camera for the Arducam 64MP OV64A40
        config = picam2.create_video_configuration(
            main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"},
            controls={
                "FrameRate": 30,
                "ExposureTime": 10000,  # 10ms exposure
                "AnalogueGain": 1.0
            }
        )
        picam2.configure(config)
        picam2.start()
        print("Camera initialized successfully")
        
        # Allow camera to warm up
        time.sleep(2)
        
    except Exception as e:
        print(f"Failed to initialize camera: {e}")
        lgpio.gpiochip_close(h)
        return

    # Set servo to center position
    lgpio.tx_servo(h, SERVO_PIN, SERVO_CENTER, 50)
    print(f"Servo set to center position ({SERVO_CENTER}μs)")
    
    try:
        print("Starting camera preview and servo control...")
        print("Controls:")
        print("- 'a' key: Move servo left")
        print("- 'd' key: Move servo right")
        print("- 'c' key: Center servo")
        print("- 's' key: Save photo")
        print("- 'f' key: Toggle autofocus")
        print("- 'q' key: Quit")
        
        servo_position = SERVO_CENTER
        autofocus_enabled = True
        
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            # Add timestamp and servo position to frame
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"Time: {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Servo: {servo_position}μs", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Autofocus: {'ON' if autofocus_enabled else 'OFF'}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Convert RGB to BGR for OpenCV display
            display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Resize for display (optional - makes window more manageable)
            display_frame = cv2.resize(display_frame, (1280, 720))
            
            cv2.imshow("Arducam 64MP OV64A40 - Press 'q' to quit", display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('a'):  # Move servo left
                servo_position = max(SERVO_MIN_PULSE, servo_position - 100)
                lgpio.tx_servo(h, SERVO_PIN, servo_position, 50)
                print(f"Servo moved left to {servo_position}μs")
            elif key == ord('d'):  # Move servo right
                servo_position = min(SERVO_MAX_PULSE, servo_position + 100)
                lgpio.tx_servo(h, SERVO_PIN, servo_position, 50)
                print(f"Servo moved right to {servo_position}μs")
            elif key == ord('c'):  # Center servo
                servo_position = SERVO_CENTER
                lgpio.tx_servo(h, SERVO_PIN, servo_position, 50)
                print(f"Servo centered at {servo_position}μs")
            elif key == ord('s'):  # Save photo
                filename = f"photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                # Save full resolution image
                full_frame = picam2.capture_array()
                bgr_frame = cv2.cvtColor(full_frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(filename, bgr_frame)
                print(f"Photo saved as {filename}")
            elif key == ord('f'):  # Toggle autofocus
                autofocus_enabled = not autofocus_enabled
                if autofocus_enabled:
                    picam2.set_controls({"AfMode": 2})  # Continuous autofocus
                    print("Autofocus enabled")
                else:
                    picam2.set_controls({"AfMode": 0})  # Manual focus
                    print("Autofocus disabled")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error during operation: {e}")
    
    finally:
        # Cleanup
        print("Cleaning up...")
        lgpio.tx_servo(h, SERVO_PIN, 0, 0)  # Disable servo PWM
        lgpio.gpiochip_close(h)
        picam2.stop()
        cv2.destroyAllWindows()
        print("Done!")

if __name__ == "__main__":
    main() 