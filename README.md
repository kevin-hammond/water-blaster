# Arducam 64MP OV64A40 Camera with Servo Control

This project provides Python scripts to control the Arducam 64MP OV64A40 camera and servo motor on Raspberry Pi 5.

## Hardware Requirements

- Raspberry Pi 5
- Arducam 64MP OV64A40 Camera Module (SKU: B0483)
- Standard servo motor (SG90 or similar)
- 15-pin to 22-pin FPC cable (for Pi 5 connection)
- Jumper wires for servo connection

## Hardware Connections

### Camera Connection

- Connect the Arducam 64MP OV64A40 to the **CAM1 port** on your Raspberry Pi 5
- Use the 15-pin to 22-pin FPC cable that should come with your camera
- Make sure the cable is inserted with the correct orientation (gold contacts facing down)

### Servo Motor Connection

- **Signal wire** (usually orange/yellow) → GPIO 18
- **VCC/Power wire** (usually red) → 5V pin
- **Ground wire** (usually brown/black) → GND pin

## Software Setup

### 1. Handle "Externally Managed Environment" Error

If you encounter "externally managed environment" errors when installing Python packages, you have several options:

**Option A: Use System Packages (Recommended)**

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-opencv python3-lgpio python3-numpy
```

**Option B: Use Virtual Environment**

```bash
python3 setup_venv.py
source activate_camera_env.sh
```

**Option C: Use --break-system-packages (Use with caution)**

```bash
pip3 install --break-system-packages numpy opencv-python lgpio picamera2
```

### 2. Run the Setup Script

The automated setup script handles the above issues automatically:

```bash
chmod +x setup_arducam.py
sudo python3 setup_arducam.py
```

This script will:

- Update your system
- Check kernel compatibility (requires 6.1.73+)
- Install required Python packages (trying multiple methods)
- Configure the camera in `/boot/firmware/config.txt`
- Handle lgd daemon setup

### 3. Reboot Your Pi

After the setup script completes successfully, reboot your Raspberry Pi:

```bash
sudo reboot
```

### 4. Test the Camera

After rebooting, test if the camera is working:

```bash
libcamera-still -t 5000 -o test.jpg
```

## Usage

### Minimal Camera and Servo Control

Run the minimal script to test both camera and servo:

```bash
python3 minimal_camera_servo.py
```

**Controls:**

- `a` - Move servo left
- `d` - Move servo right
- `c` - Center servo
- `s` - Save photo
- `f` - Toggle autofocus
- `q` - Quit

### Full Water Blaster System

Your existing `water_blaster_pi5.py` should work with the Arducam camera after the setup. The camera configuration is compatible with `picamera2`.

## Camera Features

The Arducam 64MP OV64A40 supports:

- **Resolution**: Up to 9248×6944 (64MP)
- **Video modes**: 1080p30, 720p60, 480p90
- **Autofocus**: Continuous and single-shot modes
- **Manual focus**: Adjustable lens position
- **Long exposure**: Up to 19+ minutes depending on resolution

## Troubleshooting

### Camera Not Detected

1. Check physical connections
2. Verify camera is enabled in config.txt:
   ```bash
   cat /boot/firmware/config.txt | grep ov64a40
   ```
3. Check if camera is detected:
   ```bash
   libcamera-hello --list-cameras
   ```

### Servo Not Moving

1. Check GPIO connections
2. Verify lgd daemon is running:
   ```bash
   systemctl status lgd
   ```
3. Test GPIO manually:
   ```bash
   sudo lgpio-test
   ```

### Permission Errors

Make sure you're running the scripts with appropriate permissions:

```bash
sudo usermod -a -G gpio $USER
```

Then log out and back in.

## Camera Configuration Options

The camera supports two link frequencies:

- **360000000**: Lower speed, more stable for extensions
- **456000000**: Higher speed, better performance (default)

To change the link frequency, edit `/boot/firmware/config.txt`:

```
dtoverlay=ov64a40,link-frequency=360000000
```

## Advanced Usage

### Using with OpenCV

The scripts use OpenCV for image processing and display. You can extend functionality by:

- Adding motion detection
- Implementing object tracking
- Adding image filters
- Creating time-lapse photography

### Autofocus Control

```python
# Enable continuous autofocus
picam2.set_controls({"AfMode": 2})

# Manual focus at specific position
picam2.set_controls({"AfMode": 0, "LensPosition": 5.0})
```

### High-Resolution Capture

```python
# Capture full 64MP image
config = picam2.create_still_configuration(main={"size": (9248, 6944)})
picam2.configure(config)
```

## Files

- `minimal_camera_servo.py` - Basic camera and servo control
- `setup_arducam.py` - Automated setup script
- `setup_venv.py` - Virtual environment setup script
- `test_gpio.py` - GPIO functionality test script
- `water_blaster_pi5.py` - Your existing water blaster system
- `camera.md` - Arducam documentation

## Links

- [Arducam 64MP OV64A40 Product Page](https://www.arducam.com/product/arducam-1-1-32-64mp-autofocus-camera-module-for-raspebrry-pi/)
- [Official Documentation](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/64MP-OV64A40/)
- [Picamera2 Documentation](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
