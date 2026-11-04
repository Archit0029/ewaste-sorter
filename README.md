# ♻️ Smart AI E-Waste & Recyclable Waste Sorting System

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Demo-brightgreen?logo=vercel&style=for-the-badge)](https://ewastesorter.vercel.app)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github&style=for-the-badge)](https://github.com/Archit0029/ewaste-sorter)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow?logo=python&style=for-the-badge)](https://www.python.org/)
[![Arduino UNO](https://img.shields.io/badge/Hardware-Arduino%20UNO-teal?logo=arduino&style=for-the-badge)](https://www.arduino.cc/)
[![YOLOv8](https://img.shields.io/badge/Computer%20Vision-YOLOv8-orange?style=for-the-badge)](https://github.com/ultralytics/ultralytics)

An end-to-end automated artificial intelligence waste segregation system that accurately detects and sorts **E-Waste** (electronic waste) versus **Normal Waste** (plastics, paper, organic materials). 

The system features **Ultralytics YOLOv8 real-time object detection**, an intelligent **3-second stability analysis window** with decision consensus, an interactive **Vercel-hosted Web Dashboard**, and physical actuation via an **Arduino UNO** microcontroller driving an HC-SR04 ultrasonic sensor and SG90 servo motor diverter flap.

---

## 🌐 Live Web Dashboard

Try the live browser edition with Web Serial and in-browser object detection:
👉 **[https://ewastesorter.vercel.app](https://ewastesorter.vercel.app)**

---

## 👥 Authors & Project Team

This project was developed by:

| Name | Role | GitHub Profile |
| :--- | :--- | :--- |
| **Archit Bishnoi** | Project Lead, Vision & Full-Stack System Design | [![GitHub](https://img.shields.io/badge/Archit0029-181717?style=flat&logo=github)](https://github.com/Archit0029) |
| **Atul Kumar Singh** | Hardware Integration & Testing | [![GitHub](https://img.shields.io/badge/atulsingh225-181717?style=flat&logo=github)](https://github.com/atulsingh225) |
| **Navneet Singh Saini** | Dataset Curation & Empirical Validation | [![GitHub](https://img.shields.io/badge/navneetsingh90-181717?style=flat&logo=github)](https://github.com/navneetsingh90) |

### 🔗 Connect with Archit Bishnoi:
- 🌐 **Portfolio Website**: [architbishnoi.me](https://architbishnoi.me) / [archit0029.vercel.app](https://archit0029.vercel.app)
- 💼 **LinkedIn**: [linkedin.com/in/archit-29bishnoi](https://www.linkedin.com/in/archit-29bishnoi)
- 🐙 **GitHub**: [github.com/Archit0029](https://github.com/Archit0029)
- 📸 **Instagram**: [@archit_bishnoi029](https://www.instagram.com/archit_bishnoi029/)
- 📘 **Facebook**: [facebook.com/architbishnoi29](https://www.facebook.com/architbishnoi29)
- 🛠️ **Other Live Projects**:
  - [Smart-Compiler Cloud IDE](https://smart-compiler.vercel.app)
  - [Price Predictions of Used Mobiles](https://github.com/Archit0029/Price_Predictions_of_used_mobiles)
  - [File Converter Web Application](https://github.com/Archit0029/File-Converter-Website)

---

## ⚡ How the 3-Second Stability Analysis Works

```
   [ Item Placed within 15 cm ]
               │
               ▼
   [ Trigger 3.0s Countdown HUD ]
               │
   ┌───────────┴────────────────────────────┐
   │ YOLOv8 Real-time Multi-Frame Sampling  │
   │ (Gathers predictions over 3000 ms)     │
   └───────────┬────────────────────────────┘
               │
               ▼
   [ Majority Consensus Decision ]
               │
       ┌───────┴───────┐
       ▼               ▼
   [ E-WASTE ]    [ NORMAL WASTE ]
   Motor LEFT      Motor RIGHT
   (0° for 1s)    (180° for 1s)
       │               │
       └───────┬───────┘
               ▼
   [ Servo Resets to 90° Neutral ]
               │
               ▼
   [ Cooldown until item > 20 cm ]
```

1. **Trigger Phase**: The HC-SR04 ultrasonic sensor detects an item entering the chute ($\le 15\text{ cm}$) or a prominent object appears in camera view.
2. **Analysis Window (3.0 seconds)**: The video feed displays an active **3.0s countdown HUD and progress bar**. YOLOv8 continuously runs multi-frame inferences to eliminate temporary false positives caused by hand movement or lighting changes.
3. **Fixed Decision Locking**: At $t = 0.0\text{s}$, a majority-vote consensus is locked.
4. **Motor Actuation**:
   - **E-Waste**: Commands `'E'` $\rightarrow$ Servo rotates **LEFT ($0^\circ$)** for 1.0 second, then returns to center ($90^\circ$).
   - **Normal Waste**: Commands `'N'` $\rightarrow$ Servo rotates **RIGHT ($180^\circ$)** for 1.0 second, then returns to center ($90^\circ$).
5. **Cooldown & Reset**: The system pauses in cooldown mode until the sorted item drops through and clears ($> 20\text{ cm}$), preventing duplicate triggers.

---

## 🛠️ Hardware Requirements & Wiring

### Bill of Materials (BOM)
* **Microcontroller**: Arduino UNO R3 (CH340 USB interface)
* **Sensor**: HC-SR04 Ultrasonic Distance Sensor
* **Actuator**: SG90 9g Micro Servo Motor
* **Power Supply**: 5V Regulated Power Module (HW-131) or 7.4V Li-ion battery pack with 5V step-down
* **Camera**: Standard USB Webcam or Mobile Camera (via Iriun/DroidCam)

### Circuit Wiring Pinout
| Component | Component Pin | Arduino UNO Pin | Notes |
| :--- | :--- | :--- | :--- |
| **HC-SR04** | VCC | 5V | Ultrasonic 5V rail |
| **HC-SR04** | GND | GND | Common ground |
| **HC-SR04** | TRIG | **Digital Pin 6** | Pulse trigger |
| **HC-SR04** | ECHO | **Digital Pin 7** | Echo duration |
| **SG90 Servo**| Signal (Orange/Yellow) | **Digital Pin 9** | PWM control |
| **SG90 Servo**| Power (Red) | Regulated 5V | **Do not power directly from Arduino 5V when under load** |
| **SG90 Servo**| Ground (Brown/Black) | Common GND | Connect external supply ground to Arduino GND |

---

## 🚀 How to Clone & Run This Project Locally

If you want to copy or replicate this project on your local machine, follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/Archit0029/ewaste-sorter.git
cd ewaste-sorter
```

### 2. Set Up the Arduino Hardware
1. Connect your Arduino UNO to your computer using a USB cable.
2. Open the Arduino IDE.
3. Open `arduino_sorter.ino`.
4. Select **Tools $\rightarrow$ Board $\rightarrow$ Arduino Uno** and choose the correct **COM Port** (e.g. `COM9`).
5. Click **Upload** (Verify).
6. **Important**: Close the Serial Monitor in the Arduino IDE so other applications can access the COM port.

---

### Option A: Run the High-Performance Python YOLOv8 Application (Recommended)

1. **Install Dependencies**:
   ```bash
   pip install ultralytics opencv-python pyserial torch torchvision
   ```

2. **Launch the Detector**:
   ```bash
   python yolo_detector.py
   ```

3. **Optional Flags**:
   ```bash
   python yolo_detector.py --camera 1        # Use external or mobile webcam index
   python yolo_detector.py --port COM9       # Specify Arduino COM port
   python yolo_detector.py --conf 0.50       # Custom confidence threshold
   python yolo_detector.py --model yolov8n.pt # Use custom trained weights (e.g., best.pt)
   ```

4. **Keyboard Shortcuts in Video Window**:
   - `q` or `ESC`: Quit detection safely
   - `s`: Reconnect / rescan for Arduino USB connection

---

### Option B: Run the Web Dashboard Locally

1. **Start a local HTTP server**:
   ```bash
   python -m http.server 8000
   ```

2. **Open your browser**:
   Navigate to `http://localhost:8000` (Google Chrome or Microsoft Edge recommended for Web Serial API support).

3. Click **Connect Arduino USB**, select your Arduino UNO's COM port, and click **Start Camera Feed**.

---

## ☁️ How to Deploy to Vercel

If you want to deploy your own version of the web dashboard to Vercel:

1. Fork or push your cloned repository to your GitHub account.
2. Visit **[vercel.com](https://vercel.com)** and log in.
3. Click **Add New... $\rightarrow$ Project**.
4. Import your GitHub repository.
5. Leave all build settings default and click **Deploy**.
6. Your web dashboard will be live with full HTTPS support!

---

## 📁 Repository Structure

```
ewaste_sorter/
├── .gitignore              # Ignores large model weights, Python cache, and temp files
├── arduino_sorter.ino      # Firmware for Arduino UNO (HC-SR04 & SG90 servo control)
├── index.html              # Vercel-ready Web Dashboard with in-browser YOLO object detection
├── metadata.json           # Class label metadata
├── model.json              # Model topology definition
├── README.md               # Complete project documentation & replication guide
├── vercel.json             # Vercel deployment and routing configuration
├── weights.bin             # Pre-trained browser model weights
└── yolo_detector.py        # Core Python YOLOv8 real-time detector with 3s analysis HUD
```

---

## 📜 License & Citation

This project is open-source and available under the **MIT License**. If you use this work in your research, university project, or product, please give credit to **Archit Bishnoi, Atul Kumar Singh, and Navneet Singh Saini**.
