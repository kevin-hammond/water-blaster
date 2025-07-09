#!/usr/bin/env python3
"""
Hand Tracking Camera and Servo Control for Raspberry Pi 5 with Arducam 64MP OV64A40
This script demonstrates hand tracking with camera capture and servo motor control.
The servo will follow your hand movements automatically.
"""

import time
import cv2
import lgpio
from picamera2 import Picamera2
import datetime
import mediapipe as mp
import numpy as np

# Configuration
SERVO_PIN = 18              # GPIO pin for servo (PWM)
SERVO_MIN_PULSE = 800       # Minimum pulse width in microseconds
SERVO_MAX_PULSE = 2200      # Maximum pulse width in microseconds
SERVO_CENTER = (SERVO_MIN_PULSE + SERVO_MAX_PULSE) // 2

# Camera settings
FRAME_WIDTH = 1920          # Use higher resolution for Arducam 64MP
FRAME_HEIGHT = 1080

# Hand tracking settings
HAND_TRACKING_CONFIDENCE = 0.5
HAND_DETECTION_CONFIDENCE = 0.5
SMOOTHING_FACTOR = 0.2      # Lower = more smoothing, higher = more responsive

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=HAND_DETECTION_CONFIDENCE,
            min_tracking_confidence=HAND_TRACKING_CONFIDENCE
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.last_servo_position = SERVO_CENTER
        
    def process_frame(self, frame):
        """Process frame for hand detection and return hand position"""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hand_center = None
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Get hand center (using wrist landmark)
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                hand_center = (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0]))
                
                # Draw circle at hand center
                cv2.circle(frame, hand_center, 10, (0, 255, 0), -1)
                
        return hand_center, frame
    
    def calculate_servo_position(self, hand_center, frame_width):
        """Calculate servo position based on hand center position"""
        if hand_center is None:
            return self.last_servo_position
        
        # Map hand x-position to servo range
        # Left side of frame = minimum pulse, right side = maximum pulse
        hand_x = hand_center[0]
        
        # Normalize hand position (0.0 to 1.0)
        normalized_x = hand_x / frame_width
        
        # Map to servo range
        servo_range = SERVO_MAX_PULSE - SERVO_MIN_PULSE
        target_position = SERVO_MIN_PULSE + (normalized_x * servo_range)
        
        # Apply smoothing
        smoothed_position = (
            self.last_servo_position * (1 - SMOOTHING_FACTOR) + 
            target_position * SMOOTHING_FACTOR
        )
        
        # Clamp to servo limits
        smoothed_position = max(SERVO_MIN_PULSE, min(SERVO_MAX_PULSE, smoothed_position))
        
        self.last_servo_position = smoothed_position
        return int(smoothed_position)

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

    # Initialize hand tracker
    hand_tracker = HandTracker()
    
    # Set servo to center position
    lgpio.tx_servo(h, SERVO_PIN, SERVO_CENTER, 50)
    print(f"Servo set to center position ({SERVO_CENTER}μs)")
    
    try:
        print("Starting hand tracking camera and servo control...")
        print("Controls:")
        print("- 't' key: Toggle hand tracking mode")
        print("- 'a' key: Move servo left (manual mode)")
        print("- 'd' key: Move servo right (manual mode)")
        print("- 'c' key: Center servo")
        print("- 's' key: Save photo")
        print("- 'f' key: Toggle autofocus")
        print("- 'q' key: Quit")
        print("\nHand tracking is ENABLED by default")
        
        servo_position = SERVO_CENTER
        autofocus_enabled = True
        hand_tracking_enabled = True
        
        while True:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert RGB to BGR for OpenCV display and hand tracking
            display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Process hand tracking if enabled
            hand_center = None
            if hand_tracking_enabled:
                hand_center, display_frame = hand_tracker.process_frame(display_frame)
                
                # Update servo position based on hand tracking
                if hand_center is not None:
                    servo_position = hand_tracker.calculate_servo_position(hand_center, FRAME_WIDTH)
                    lgpio.tx_servo(h, SERVO_PIN, servo_position, 50)
            
            # Add information overlay
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(display_frame, f"Time: {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Servo: {servo_position}μs", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Autofocus: {'ON' if autofocus_enabled else 'OFF'}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Hand Tracking: {'ON' if hand_tracking_enabled else 'OFF'}", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if hand_center and hand_tracking_enabled:
                cv2.putText(display_frame, f"Hand: ({hand_center[0]}, {hand_center[1]})", (10, 190), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add tracking status indicator
            status_color = (0, 255, 0) if hand_center else (0, 0, 255)
            status_text = "TRACKING" if hand_center else "NO HAND"
            cv2.putText(display_frame, status_text, (FRAME_WIDTH - 200, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 3)
            
            # Resize for display (optional - makes window more manageable)
            display_frame = cv2.resize(display_frame, (1280, 720))
            
            cv2.imshow("Hand Tracking - Arducam 64MP OV64A40", display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('t'):  # Toggle hand tracking
                hand_tracking_enabled = not hand_tracking_enabled
                print(f"Hand tracking {'enabled' if hand_tracking_enabled else 'disabled'}")
            elif key == ord('a') and not hand_tracking_enabled:  # Move servo left (manual mode only)
                servo_position = max(SERVO_MIN_PULSE, servo_position - 100)
                lgpio.tx_servo(h, SERVO_PIN, servo_position, 50)
                print(f"Servo moved left to {servo_position}μs")
            elif key == ord('d') and not hand_tracking_enabled:  # Move servo right (manual mode only)
                servo_position = min(SERVO_MAX_PULSE, servo_position + 100)
                lgpio.tx_servo(h, SERVO_PIN, servo_position, 50)
                print(f"Servo moved right to {servo_position}μs")
            elif key == ord('c'):  # Center servo
                servo_position = SERVO_CENTER
                hand_tracker.last_servo_position = SERVO_CENTER  # Reset smoothing
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