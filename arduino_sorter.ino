#include <Servo.h>

const byte TRIG_PIN = 6;
const byte ECHO_PIN = 7;
const byte SERVO_PIN = 9;

// Distance thresholds
const float DETECT_CM = 15.0; // Item detected within 15 cm
const float RESET_CM = 20.0;  // Reset once item is removed past 20 cm

Servo sorter;
unsigned long lastReport = 0;

float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 25000);
  if (duration == 0) return -1.0;
  return duration * 0.0343 / 2.0;
}

void triggerServo(char cmd) {
  if (cmd == 'E') {
    // E-Waste -> Turn Left (0 deg)
    Serial.println("SORT:E_START");
    sorter.write(0);
    delay(1000);
    sorter.write(90); // Return to neutral
    Serial.println("SORT:E_DONE");
  } else if (cmd == 'N') {
    // Normal Waste -> Turn Right (180 deg)
    Serial.println("SORT:N_START");
    sorter.write(180);
    delay(1000);
    sorter.write(90); // Return to neutral
    Serial.println("SORT:N_DONE");
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  sorter.attach(SERVO_PIN);
  sorter.write(90); // Neutral center position
  Serial.println("READY");
}

void loop() {
  // Check for execution commands from Python:
  // 'E' = Execute E-waste turn (Left: 0 deg)
  // 'N' = Execute Normal waste turn (Right: 180 deg)
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == 'E' || c == 'N') {
      triggerServo(c);
    }
  }

  // Periodic distance reading sent to Python
  float distance = readDistance();
  if (millis() - lastReport >= 100) {
    if (distance >= 0) {
      Serial.print("D:");
      Serial.println(distance, 1);
    } else {
      Serial.println("D:-1");
    }
    lastReport = millis();
  }

  delay(20);
}
