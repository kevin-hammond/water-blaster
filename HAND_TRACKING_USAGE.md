# Hand Tracking Camera Servo Control

This updated script now includes hand tracking functionality that allows the servo motor to automatically follow your hand movements.

## Features

### Hand Tracking

- **Automatic hand detection** using MediaPipe
- **Real-time servo control** based on hand position
- **Smooth servo movement** with configurable smoothing factor
- **Visual feedback** with hand landmarks and tracking status

### Control Modes

- **Hand Tracking Mode** (default): Servo follows your hand automatically
- **Manual Mode**: Traditional keyboard control for servo positioning

## Setup

1. Install dependencies:

   ```bash
   python3 setup_hand_tracking.py
   ```

2. Run the script:
   ```bash
   python3 minimal_camera_servo.py
   ```

## Controls

### Key Controls

- **'t'**: Toggle between hand tracking and manual mode
- **'a'**: Move servo left (manual mode only)
- **'d'**: Move servo right (manual mode only)
- **'c'**: Center servo position
- **'s'**: Save photo
- **'f'**: Toggle autofocus
- **'q'**: Quit

### Hand Tracking Behavior

- The servo will track the **horizontal position** of your hand
- Move your hand **left** → servo moves left
- Move your hand **right** → servo moves right
- The system tracks your **wrist position** as the reference point
- **Green circle** appears on your wrist when tracking is active

## Visual Indicators

### On-Screen Information

- **Time**: Current timestamp
- **Servo**: Current servo position in microseconds
- **Autofocus**: ON/OFF status
- **Hand Tracking**: ON/OFF status
- **Hand Position**: X,Y coordinates when hand is detected
- **Tracking Status**: "TRACKING" (green) or "NO HAND" (red)

### Hand Visualization

- **Hand landmarks**: Drawn as connected points on your hand
- **Wrist marker**: Green circle at the tracking reference point

## Configuration

You can adjust these settings in the script:

```python
# Hand tracking settings
HAND_TRACKING_CONFIDENCE = 0.5      # Tracking confidence threshold
HAND_DETECTION_CONFIDENCE = 0.5     # Detection confidence threshold
SMOOTHING_FACTOR = 0.2               # Servo smoothing (0.1 = smooth, 0.9 = responsive)
```

## Tips for Best Results

1. **Lighting**: Ensure good lighting for optimal hand detection
2. **Background**: Plain backgrounds work better than cluttered ones
3. **Distance**: Keep your hand at a reasonable distance from the camera
4. **Movement**: Smooth, deliberate movements work better than quick gestures
5. **Positioning**: Keep your hand within the camera frame for continuous tracking

## Troubleshooting

### No Hand Detection

- Check lighting conditions
- Ensure your hand is visible in the camera frame
- Try adjusting detection confidence settings

### Jittery Servo Movement

- Increase the `SMOOTHING_FACTOR` for smoother movement
- Check for stable hand positioning
- Ensure good lighting to improve tracking accuracy

### Manual Mode

- Press 't' to switch to manual mode if automatic tracking isn't working
- Use 'a' and 'd' keys to control servo manually
- Press 'c' to center the servo at any time
