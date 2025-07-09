#! /usr/bin/env python3

# This code runs on a Raspberry Pi 5 to control a targeting servo and water
# relay to create a motion-controlled water-blaster. The primary purpose is
# to discourage deer from eating our roses! The system uses the Raspberry Pi
# Camera Module 3 for night or day use.

# Uses the cv2 image processing library (OpenCV), the picamera2 camera library,
# and the rpi-lgpio library to read images, find moving objects, aim a servo,
# and fire a water valve relay.

# Start the code from your terminal: python3 water_blaster_rpi5.py
# A monitor window will open to show the targeting video. On startup, a
# reference frame is captured. When a new object is detected, a green targeting
# rectangle appears, and the state changes to "Occupied". If the target
# remains still for MIN_AQUIRE_TIME seconds, a picture is saved to the
# 'trigger_pictures' directory, and the water valve is opened for a few seconds.

# To prevent false triggers from gradual changes (like clouds), the reference
# frame is updated periodically. If too many triggers occur, a refresh is forced.

# Logs all activity to a file named "log_<date_time>.txt".

# The code uses the rpi-lgpio library, which provides stable servo control via
# the 'lgd' daemon.

# Original script by dlf 8/18/2017
# Modernized for Raspberry Pi 5 by AI Assistant 10/26/2023

# Import the necessary packages
import datetime
from datetime import timedelta
import time
import cv2
import lgpio
import os
from picamera2 import Picamera2

# --- Configuration Constants ---

# Pin definitions (using BCM numbering)
TRIGGER = 17                # The pin that will drive the trigger relay
SERVO = 18                  # The PWM pin that controls the tracking servo
DEBUG_SWITCH = 23           # A pin for a switch to enable/disable firing

# Timing constants
MIN_AQUIRE_TIME = 2         # Target must be stationary for this many seconds before shooting
MAX_SHOTS = 3               # Max shots allowed between reference frame updates
REF_FRAME_TIME_LIMIT = 120  # Seconds before the reference frame is automatically updated
MIN_TIME_FROM_LAST_REF_FRAME_UPDATE = 10 # Seconds after a frame update before a shot is allowed

# Video and Motion Detection constants
FRAME_WIDTH = 640           # Video frame width in pixels
FRAME_HEIGHT = 480          # Video frame height in pixels
MIN_CONTOUR_AREA = 500      # Ignore motion contours smaller than this area
TARGET_MOVEMENT_THRESHOLD = 50 # How many pixels a target can move and still be "stationary"
THRESHOLD_SENSITIVITY = 25  # Object detection sensitivity (1-100). Lower is more sensitive.
BLUR_SIZE = 21              # Blur kernel size to smooth image and reduce noise

# Servo constants
SERVO_MAX_RANGE = 2200      # Max pulse width in microseconds (us) for servo
SERVO_MIN_RANGE = 800       # Min pulse width in microseconds (us) for servo
SERVO_CENTER_ADJ = 0        # Fine-tune servo center alignment (us)
SERVO_TRIGGER_SWEEP = 100   # How far (in us) to sweep the servo when shooting
SERVO_CENTER = int((SERVO_MIN_RANGE + SERVO_MAX_RANGE) / 2 + SERVO_CENTER_ADJ)

# --- Initialization ---

# Set up logging
startTime = datetime.datetime.now()
log_filename = "log_" + startTime.strftime("%Y_%m_%d__%H_%M_%S") + ".txt"
logfile = open(log_filename, "w")

def log_message(message):
    """Prints a message to the console and writes it to the log file."""
    print(message)
    logfile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    logfile.flush() # Ensure message is written immediately

log_message("Starting Water Blaster System...")

# Set up a directory to save pictures to
os.makedirs("trigger_pictures", exist_ok=True)

# Initialize GPIO
try:
    h = lgpio.gpiochip_open(0) # Get a handle to the GPIO chip
    lgpio.gpio_claim_output(h, TRIGGER)
    lgpio.gpio_claim_output(h, SERVO)
    # Claim debug switch pin as input with an internal pull-up resistor
    lgpio.gpio_claim_input(h, DEBUG_SWITCH, lgpio.SET_PULL_UP)

    lgpio.gpio_write(h, TRIGGER, 0) # Ensure relay is off
except Exception as e:
    log_message(f"FATAL: Could not initialize GPIO. Is lgd running? Error: {e}")
    exit()

# Initialize Camera
try:
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"})
    picam2.configure(config)
    picam2.start()
    log_message("Camera initialized. Warming up...")
    time.sleep(2.0) # Allow camera to stabilize
except Exception as e:
    log_message(f"FATAL: Could not initialize camera. Is it connected properly? Error: {e}")
    lgpio.gpiochip_close(h)
    exit()

# Initialize servo to the center position
lgpio.tx_servo(h, SERVO, SERVO_CENTER, 50) # 50Hz is standard for servos
time.sleep(1)

# Initialize state variables
firstFrame = None
refFrameTime = datetime.datetime.now()
monitorText = "Unoccupied"
targetFirstAquiredTime = datetime.datetime.fromtimestamp(0) # Use a valid old date
shotsSinceRefresh = 0
totalShots = 0
lastTargetX = 0
lastTargetY = 0
forceRefresh = False

# --- Main Loop ---
try:
    while True:
        # Check the debug switch. If switch is grounded, debug is on (no firing).
        debugging = lgpio.gpio_read(h, DEBUG_SWITCH) == 0

        # Grab the current frame from the camera
        frame = picam2.capture_array()
        
        # Convert to grayscale and blur for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (BLUR_SIZE, BLUR_SIZE), 0)

        # If reference frame is old or a refresh is forced, update it
        if firstFrame is None or (datetime.datetime.now() - refFrameTime).seconds > REF_FRAME_TIME_LIMIT or forceRefresh:
            log_message("Updating video reference frame.")
            firstFrame = gray
            refFrameTime = datetime.datetime.now()
            shotsSinceRefresh = 0
            forceRefresh = False
            continue

        # Compute the difference between the current and reference frames
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, THRESHOLD_SENSITIVITY, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours of moving objects
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find the largest moving object
        largest_contour = None
        max_area = 0
        for c in contours:
            area = cv2.contourArea(c)
            if area > MIN_CONTOUR_AREA and area > max_area:
                max_area = area
                largest_contour = c

        target_found = largest_contour is not None
        
        if target_found:
            (x, y, w, h) = cv2.boundingRect(largest_contour)
            centerX = x + w // 2
            centerY = y + h // 2
            
            # Draw targeting box on the live feed
            cv2.rectangle(frame, (centerX - 20, centerY - 20), (centerX + 20, centerY + 20), (0, 255, 0), 2)

            # Check if the target is stationary
            movement = abs(lastTargetX - centerX) + abs(lastTargetY - centerY)
            if movement < TARGET_MOVEMENT_THRESHOLD:
                if monitorText != "Acquired":
                    targetFirstAquiredTime = datetime.datetime.now()
                monitorText = "Acquired"
            else:
                monitorText = "Tracking"
                targetFirstAquiredTime = datetime.datetime.fromtimestamp(0) # Reset timer
            
            lastTargetX = centerX
            lastTargetY = centerY
            
            # Aim the servo
            # Scale target's X position to the servo's pulse width range
            duty = SERVO_MIN_RANGE + (centerX / FRAME_WIDTH) * (SERVO_MAX_RANGE - SERVO_MIN_RANGE)
            lgpio.tx_servo(h, SERVO, int(duty), 50)

        else: # No target found
            monitorText = "Unoccupied"
            targetFirstAquiredTime = datetime.datetime.fromtimestamp(0)
            lgpio.tx_servo(h, SERVO, SERVO_CENTER, 50) # Return servo to center

        # --- Firing Logic ---
        if monitorText == "Acquired":
            time_acquired = (datetime.datetime.now() - targetFirstAquiredTime).seconds
            time_since_refresh = (datetime.datetime.now() - refFrameTime).seconds

            if time_acquired >= MIN_AQUIRE_TIME:
                if time_since_refresh < MIN_TIME_FROM_LAST_REF_FRAME_UPDATE and totalShots > 0:
                    log_message("Acquired too soon after refresh. Forcing new reference frame.")
                    forceRefresh = True
                    continue

                if shotsSinceRefresh < MAX_SHOTS and not debugging:
                    totalShots += 1
                    shotsSinceRefresh += 1
                    
                    log_message(f"Shot {shotsSinceRefresh}/{MAX_SHOTS} at X:{lastTargetX} Y:{lastTargetY}. Total shots: {totalShots}")
                    
                    # Save a picture of the target
                    img_path = f"trigger_pictures/trigger_{startTime.strftime('%Y%m%d_%H%M%S')}_{totalShots}.jpg"
                    # Convert to BGR for saving with OpenCV
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(img_path, bgr_frame)

                    # Fire the water valve and sweep the servo
                    lgpio.gpio_write(h, TRIGGER, 1)
                    current_duty = lgpio.tx_servo(h, SERVO, 0, 0)[0] # Get current pulse width
                    
                    for i in range(5): # Sweep 5 times
                        lgpio.tx_servo(h, SERVO, int(current_duty + SERVO_TRIGGER_SWEEP), 50)
                        time.sleep(0.2)
                        lgpio.tx_servo(h, SERVO, int(current_duty - SERVO_TRIGGER_SWEEP), 50)
                        time.sleep(0.2)
                    
                    lgpio.gpio_write(h, TRIGGER, 0)
                    targetFirstAquiredTime = datetime.datetime.fromtimestamp(0) # Reset timer to prevent rapid re-fire

                    if shotsSinceRefresh >= MAX_SHOTS:
                        log_message(f"Max shot limit ({MAX_SHOTS}) reached. Forcing reference frame update.")
                        forceRefresh = True
                
                elif debugging:
                    log_message("Target acquired, but DEBUG mode is ON. Not firing.")
                    # Reset timer to avoid spamming the log
                    targetFirstAquiredTime = datetime.datetime.fromtimestamp(0)


        # --- Display Video Feed ---
        # Draw status text on the frame
        status_text = f"Status: {monitorText}"
        if debugging:
            status_text += " (DEBUG MODE)"
        cv2.putText(frame, status_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Convert back to BGR for display with cv2.imshow
        display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Water Blaster Feed", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            log_message("'q' key pressed. Exiting.")
            break

finally:
    # --- Cleanup ---
    log_message("Shutting down...")
    logfile.close()
    
    # Safely close GPIO resources
    if 'h' in locals():
        lgpio.gpio_write(h, TRIGGER, 0) # Make sure valve is off
        lgpio.tx_servo(h, SERVO, 0, 0)   # Disable servo PWM
        lgpio.gpiochip_close(h)
    
    # Stop camera and close windows
    if 'picam2' in locals():
        picam2.stop()
    cv2.destroyAllWindows()
    log_message("System stopped.")