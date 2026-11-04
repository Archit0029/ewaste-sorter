"""
YOLOv8 Real-Time AI E-Waste & Object Detection with 3-Second Stability Analysis
-------------------------------------------------------------------------------
Workflow:
1. Continuous YOLOv8 item detection & distance monitoring (HC-SR04 via Arduino).
2. When an item is placed in front of the sensor (or camera), the system enters
   a 3-second ANALYZING phase with a live on-screen countdown timer.
3. Over the 3 seconds, the system aggregates predictions to ensure accurate,
   stable classification (E-Waste vs Normal Waste).
4. After 3 seconds, a FINAL LOCKED DECISION is made.
5. The command ('E' or 'N') is transmitted to the Arduino:
   - E-Waste -> Motor turns LEFT (0 deg), waits 1s, returns to center.
   - Normal Waste -> Motor turns RIGHT (180 deg), waits 1s, returns to center.
6. The system enters a COOLDOWN phase until the sorted item is cleared,
   preventing duplicate sorting.
"""

import os
import sys
import time
import threading
import argparse
from collections import Counter

# Set local directory for Ultralytics configuration
os.environ["YOLO_CONFIG_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ultralytics")

import cv2
import serial
import serial.tools.list_ports
from ultralytics import YOLO

# ==============================================================================
# Categories & Label Mapping
# ==============================================================================
E_WASTE_CLASSES = {
    "cell phone", "laptop", "mouse", "keyboard", "remote",
    "microwave", "toaster", "tv", "refrigerator", "clock",
    "tablet", "screen", "monitor", "charger", "pcb", "battery",
    "hard drive", "wire", "cable", "electronics"
}

NORMAL_WASTE_CLASSES = {
    "bottle", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut",
    "cake", "book", "vase", "scissors", "teddy bear", "toothbrush",
    "can", "plastic", "paper", "cardboard"
}

# UI Color constants (BGR)
COLOR_EWASTE = (0, 0, 255)       # Red / Coral (Left turn)
COLOR_NORMAL = (0, 200, 0)       # Green (Right turn)
COLOR_ANALYZING = (0, 165, 255)  # Orange for 3s analysis countdown
COLOR_WAITING = (200, 200, 200)  # Gray
COLOR_HUD_BG = (20, 20, 20)
COLOR_ACCENT = (255, 190, 0)


class ArduinoBridge:
    """Thread-safe serial interface to Arduino UNO."""

    def __init__(self, port=None, baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.lock = threading.Lock()
        self.latest_distance = None
        self.is_connected = False
        self.thread = None
        self.last_status = "Waiting"

    def find_arduino_port(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            desc = p.description.lower()
            hwid = p.hwid.lower()
            if "ch340" in desc or "arduino" in desc or "usb-serial" in desc or "ch340" in hwid:
                return p.device
        return ports[0].device if ports else None

    def connect(self):
        if not self.port:
            self.port = self.find_arduino_port()

        if not self.port:
            print("[Arduino] No COM port found. Running in simulation mode.")
            return False

        try:
            print(f"[Arduino] Connecting to {self.port} at {self.baudrate} baud...")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2.0)  # Wait for Arduino bootloader reset
            self.is_connected = True
            self.running = True
            self.thread = threading.Thread(target=self._reader_loop, daemon=True)
            self.thread.start()
            print(f"[Arduino] Successfully connected to {self.port}!")
            return True
        except Exception as e:
            print(f"[Arduino] Connection error on {self.port}: {e}")
            self.is_connected = False
            return False

    def _reader_loop(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                with self.lock:
                    if line.startswith("D:"):
                        try:
                            val = float(line[2:])
                            self.latest_distance = val if val >= 0 else None
                        except ValueError:
                            pass
                    elif line == "SORT:E_START":
                        self.last_status = "Motor turning LEFT (E-Waste)..."
                    elif line == "SORT:E_DONE":
                        self.last_status = "E-Waste sorted! (Motor returned to center)"
                    elif line == "SORT:N_START":
                        self.last_status = "Motor turning RIGHT (Normal Waste)..."
                    elif line == "SORT:N_DONE":
                        self.last_status = "Normal Waste sorted! (Motor returned to center)"
            except Exception:
                break

    def trigger_sort(self, decision_code):
        """Sends 'E' or 'N' command to Arduino to execute the physical motor rotation."""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            print(f"[Arduino Simulation] Motor commanded: {decision_code}")
            return
        try:
            with self.lock:
                self.ser.write(f"{decision_code}\n".encode('utf-8'))
                print(f"[Arduino] Sent sort command: {decision_code}")
        except Exception as e:
            print(f"[Arduino] Write failed: {e}")

    def close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.is_connected = False


def classify_entity(label):
    clean = label.lower().strip()
    if clean in E_WASTE_CLASSES or any(w in clean for w in ["phone", "laptop", "mouse", "keyboard", "battery", "cable", "circuit", "remote"]):
        return 'E', "E-WASTE", COLOR_EWASTE
    if clean in NORMAL_WASTE_CLASSES or any(w in clean for w in ["bottle", "cup", "can", "paper", "cardboard", "food", "plastic"]):
        return 'N', "NORMAL WASTE", COLOR_NORMAL
    return 'U', "OTHER ENTITY", COLOR_WAITING


def draw_hud(frame, fps, state, time_left, fixed_decision, distance_cm, arduino_status, last_action):
    h, w = frame.shape[:2]

    # Overlay banners
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 105), COLOR_HUD_BG, -1)
    cv2.rectangle(overlay, (0, h - 50), (w, h), COLOR_HUD_BG, -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

    # Title & FPS
    cv2.putText(frame, "AI E-WASTE SORTER (YOLOv8 + 3s ANALYSIS)", (16, 30), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 220, 255), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}", (w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Sub-header: Arduino connection & Ultrasonic distance
    conn_color = (0, 255, 0) if "Connected" in arduino_status else (0, 140, 255)
    cv2.putText(frame, f"Arduino: {arduino_status}", (16, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, conn_color, 1)

    dist_str = f"{distance_cm:.1f} cm" if distance_cm is not None else "Out of Range / N/A"
    dist_color = (0, 255, 255) if (distance_cm is not None and distance_cm <= 15.0) else (180, 180, 180)
    cv2.putText(frame, f"Distance: {dist_str}", (260, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, dist_color, 1)

    # Center/Right State & Decision Box
    box_w = 340
    box_x = w - box_w - 16
    if state == "IDLE":
        cv2.rectangle(frame, (box_x, 42), (w - 16, 95), (60, 60, 60), -1)
        cv2.putText(frame, "STATE: READY / WAITING FOR ITEM", (box_x + 10, 68), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(frame, "Place item within 15 cm", (box_x + 10, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

    elif state == "ANALYZING":
        cv2.rectangle(frame, (box_x, 42), (w - 16, 95), COLOR_ANALYZING, -1)
        cv2.putText(frame, f"ANALYZING: {time_left:.1f}s LEFT", (box_x + 12, 68), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 2)
        # Visual countdown progress bar
        progress = max(0.0, min(1.0, (3.0 - time_left) / 3.0))
        bar_len = int((box_w - 24) * progress)
        cv2.rectangle(frame, (box_x + 12, 78), (box_x + 12 + bar_len, 88), (0, 0, 0), -1)

    elif state == "DECIDED":
        badge_color = COLOR_EWASTE if fixed_decision == 'E' else COLOR_NORMAL
        cv2.rectangle(frame, (box_x, 42), (w - 16, 95), badge_color, -1)
        action_msg = "DECISION: E-WASTE (MOTOR LEFT)" if fixed_decision == 'E' else "DECISION: NORMAL WASTE (MOTOR RIGHT)"
        cv2.putText(frame, action_msg, (box_x + 8, 72), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 2)

    elif state == "COOLDOWN":
        cv2.rectangle(frame, (box_x, 42), (w - 16, 95), (100, 70, 0), -1)
        cv2.putText(frame, "SORT COMPLETED", (box_x + 12, 68), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(frame, "Remove item past 20 cm to reset", (box_x + 12, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)

    # Bottom status bar
    cv2.putText(frame, f"Status: {last_action}", (16, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, "[Q] Quit  |  [S] Reconnect Arduino", (w - 320, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def run_sorter(model_path="yolov8n.pt", camera_index=0, com_port=None, conf_threshold=0.45):
    print("=" * 70)
    print("   YOLOv8 AI Sorter: 3-Second Stability Analysis + Fixed Decision")
    print("=" * 70)

    # 1. Load YOLOv8
    print(f"[YOLOv8] Loading model weights from '{model_path}'...")
    try:
        model = YOLO(model_path)
        print("[YOLOv8] Model loaded successfully!")
    except Exception as e:
        print(f"[YOLOv8] Error loading model: {e}")
        return

    # 2. Connect Arduino
    arduino = ArduinoBridge(port=com_port, baudrate=9600)
    arduino.connect()

    # 3. Setup Camera
    print(f"[Camera] Opening capture index {camera_index}...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"[Camera] ERROR: Could not open camera {camera_index}.")
        arduino.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    cv2.namedWindow("YOLOv8 AI Sorter (3s Analysis)", cv2.WINDOW_NORMAL)

    # State Machine Variables
    # States: 'IDLE', 'ANALYZING', 'DECIDED', 'COOLDOWN'
    state = "IDLE"
    analysis_start_time = 0.0
    analysis_duration = 3.0  # 3 seconds fixed analysis
    analysis_samples = []    # Stores ('E' or 'N') during the 3 seconds
    fixed_decision = None
    decision_time = 0.0
    last_action = "System ready. Place item near sensor (within 15 cm)."

    prev_frame_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.02)
                continue

            current_time = time.time()
            fps = 1.0 / (current_time - prev_frame_time) if (current_time - prev_frame_time) > 0 else 30.0
            prev_frame_time = current_time

            # Read live ultrasonic distance from Arduino
            dist = arduino.latest_distance

            # Run YOLOv8 object detection
            results = model.predict(source=frame, conf=conf_threshold, verbose=False)
            boxes = results[0].boxes

            current_frame_category = None
            highest_conf = 0.0

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    label = model.names.get(cls_id, f"Class {cls_id}")

                    cat_code, cat_name, box_color = classify_entity(label)

                    if cat_code in ('E', 'N') and conf > highest_conf:
                        highest_conf = conf
                        current_frame_category = cat_code

                    # Draw stylish bounding boxes
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                    caption = f"{label.upper()} {conf * 100:.1f}% [{cat_name}]"
                    (tw, th), _ = cv2.getTextSize(caption, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 8, y1), box_color, -1)
                    cv2.putText(frame, caption, (x1 + 4, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # ------------------------------------------------------------------
            # State Machine: 3-Second Analysis & Servo Trigger
            # ------------------------------------------------------------------
            # Trigger item presence either via ultrasonic sensor (<=15cm) OR clear detection in camera
            item_present = (dist is not None and dist <= 15.0) or (dist is None and current_frame_category is not None)

            if state == "IDLE":
                if item_present and current_frame_category is not None:
                    # Item detected -> Start 3-second analysis!
                    state = "ANALYZING"
                    analysis_start_time = current_time
                    analysis_samples = [current_frame_category]
                    last_action = "Item detected! Analyzing stability for 3 seconds..."
                    print(f"\n[AI] Item detected. Starting 3-second analysis...")

            elif state == "ANALYZING":
                time_elapsed = current_time - analysis_start_time
                time_left = max(0.0, analysis_duration - time_elapsed)

                if current_frame_category is not None:
                    analysis_samples.append(current_frame_category)

                # Show prominent countdown timer in center of frame
                center_text = f"ANALYZING: {time_left:.1f}s"
                (tw, th), _ = cv2.getTextSize(center_text, cv2.FONT_HERSHEY_DUPLEX, 1.2, 3)
                cx, cy = (frame.shape[1] - tw) // 2, (frame.shape[0] + th) // 2
                cv2.rectangle(frame, (cx - 15, cy - th - 15), (cx + tw + 15, cy + 15), (0, 0, 0), -1)
                cv2.putText(frame, center_text, (cx, cy), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 200, 255), 3)

                if time_elapsed >= analysis_duration:
                    # 3 seconds complete: compute authoritative majority vote
                    if analysis_samples:
                        counts = Counter(analysis_samples)
                        winner = counts.most_common(1)[0][0]  # 'E' or 'N'
                    else:
                        winner = current_frame_category if current_frame_category else 'N'

                    fixed_decision = winner
                    state = "DECIDED"
                    decision_time = current_time

                    if fixed_decision == 'E':
                        last_action = "FIXED DECISION: E-WASTE! Motor commanded LEFT (0 deg)"
                        print("[AI] 3s Analysis Finished -> FIXED DECISION: E-WASTE! Turning motor LEFT.")
                    else:
                        last_action = "FIXED DECISION: NORMAL WASTE! Motor commanded RIGHT (180 deg)"
                        print("[AI] 3s Analysis Finished -> FIXED DECISION: NORMAL WASTE! Turning motor RIGHT.")

                    # Transmit motor command to Arduino
                    arduino.trigger_sort(fixed_decision)

            elif state == "DECIDED":
                # Give Arduino 1.8 seconds to complete servo movement
                if current_time - decision_time > 1.8:
                    state = "COOLDOWN"
                    last_action = "Sort complete! Waiting for item removal (> 20 cm) to reset..."
                    print("[AI] Motor completed move. Waiting for item removal...")

            elif state == "COOLDOWN":
                # Reset only after item has been cleared
                item_cleared = (dist is not None and dist > 20.0) or (dist is None and current_frame_category is None)
                if item_cleared:
                    state = "IDLE"
                    fixed_decision = None
                    last_action = "Ready for next item."
                    print("[AI] Sensor reset. Ready for next item.")

            # Calculate remaining time for HUD
            t_rem = 0.0
            if state == "ANALYZING":
                t_rem = max(0.0, analysis_duration - (current_time - analysis_start_time))

            # Render HUD
            status_conn = f"Connected ({arduino.port})" if arduino.is_connected else "Disconnected"
            draw_hud(
                frame=frame,
                fps=fps,
                state=state,
                time_left=t_rem,
                fixed_decision=fixed_decision,
                distance_cm=dist,
                arduino_status=status_conn,
                last_action=last_action
            )

            cv2.imshow("YOLOv8 AI Sorter (3s Analysis)", frame)

            # Keyboard triggers
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('s'):
                print("[System] Reconnecting Arduino...")
                arduino.close()
                arduino.connect()

    except KeyboardInterrupt:
        print("\n[System] Stopping on user interrupt...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        arduino.close()
        print("[System] Stopped cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLOv8 AI E-Waste Sorter with 3-Second Analysis")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Path to YOLOv8 model weights (.pt)")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--port", type=str, default=None, help="Arduino COM port (e.g., COM9)")
    parser.add_argument("--conf", type=float, default=0.45, help="Confidence threshold (default: 0.45)")

    args = parser.parse_args()
    run_sorter(model_path=args.model, camera_index=args.camera, com_port=args.port, conf_threshold=args.conf)
