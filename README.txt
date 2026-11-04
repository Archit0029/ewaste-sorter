HOW THE 3-SECOND ANALYSIS & SORTING WORKS:
------------------------------------------
1. Standby: The system monitors the camera feed and ultrasonic sensor.
2. Trigger: When an item enters front detection (<= 15 cm or camera target),
   the 3-second analysis countdown triggers automatically.
3. Analysis Phase (3.0s):
   - A live countdown timer and progress bar display on the video feed.
   - YOLOv8 samples the entity over the full 3 seconds to avoid transient false positives.
4. Fixed Decision & Motor Actuation:
   - Once 3 seconds elapse, a majority-vote final decision is locked.
   - E-Waste -> Motor turns LEFT (0° position) for 1 second, then resets to 90°.
   - Normal Waste -> Motor turns RIGHT (180° position) for 1 second, then resets to 90°.
5. Reset: The system enters Cooldown until the sorted item is cleared (> 20 cm)
   so the same item won't trigger duplicate motor turns.
Uses state-of-the-art YOLOv8 object detection with OpenCV, direct Arduino COM
port integration, live ultrasonic distance readout, and professional HUD:

1) Connect your Arduino UNO via USB (e.g. COM9).
2) Ensure arduino_sorter.ino is flashed to the Arduino UNO.
3) Run the Python YOLOv8 detector:
     python yolo_detector.py
   
   Optional options:
     python yolo_detector.py --camera 0          # Change camera index (0, 1, etc.)
     python yolo_detector.py --port COM9         # Force specific COM port
     python yolo_detector.py --conf 0.45         # Adjust confidence threshold
     python yolo_detector.py --model yolov8n.pt  # Custom trained weights (e.g., best.pt)

4) Interactive controls in the video window:
   - 'q' or 'ESC' : Quit detection
   - 's'          : Reconnect / scan for Arduino

============================================================
METHOD 2: BROWSER WEB DASHBOARD (YOLO OBJECT DETECTION ENGINE)
============================================================
The web dashboard now features in-browser object detection with real-time
bounding boxes, 3-second stability analysis countdown, and Web Serial:

1) Start a local HTTP server in PowerShell:
     python -m http.server 8000
2) Open Google Chrome or Microsoft Edge and navigate to:
     http://localhost:8000
3) The browser will load the YOLO vision engine (COCO-SSD / MobileNet).
4) Click "Connect Arduino USB" to link your Arduino UNO (COM9).
5) Click "Start Camera Feed" to initiate real-time bounding boxes and 3s sorting.
5) Upload arduino_sorter.ino to the Arduino UNO using Arduino IDE.
6) Close Arduino IDE Serial Monitor.
7) Click Connect Arduino USB and select the UNO's COM port.
8) Select your mobile webcam from the camera list and click Start camera.
9) Put an object within 15 cm of the HC-SR04. E-waste commands 0 degrees; normal waste commands 180 degrees.
10) Remove the item until distance is greater than 20 cm to reset.

WIRING
HC-SR04 VCC -> Arduino 5V
HC-SR04 GND -> Arduino GND
HC-SR04 TRIG -> D6
HC-SR04 ECHO -> D7
SG90 yellow/orange signal -> D9
SG90 brown/black -> common GND
SG90 red -> suitable regulated 5V servo supply only after verifying the supply.

SAFETY
First test the camera, model and distance readings with servo red power disconnected.
Never connect the SG90 directly to the 7.4V battery. Servo supply ground must connect to Arduino GND.
Do not connect HW-131 5V rail to Arduino 5V while UNO is powered by USB.
Servo left/right depends on mounting. Test with no load and fingers clear.
The model can misclassify objects; test varied items before relying on it.
Use current Chrome/Edge on Windows. Web Serial requires localhost and camera permission.
