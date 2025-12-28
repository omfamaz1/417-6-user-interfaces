#include <SerialCommand.h>

SerialCommand sCmd;

// Motor control pins
const int enablePin = 9;
const int in1Pin = 7;
const int in2Pin = 8;

int currentSpeed = 0;  // Mevcut hızı sakla

void setup() {
  Serial.begin(9600);
  
  pinMode(enablePin, OUTPUT);
  pinMode(in1Pin, OUTPUT);
  pinMode(in2Pin, OUTPUT);
  
  sCmd.addCommand("SPEED", setSpeed);
  sCmd.addCommand("CW", rotateClockwise);
  sCmd.addCommand("CCW", rotateCounterClockwise);
  sCmd.addCommand("STOP", stopMotor);
  sCmd.addCommand("BRAKE", brakeMotor);
  
  stopMotor();
  
  Serial.println("DC Motor Control Ready");
}

void loop() {
  sCmd.readSerial();
}

void setSpeed() {
  char *arg = sCmd.next();
  if (arg != NULL) {
    int speedValue = atoi(arg);
    speedValue = constrain(speedValue, 0, 255);
    currentSpeed = speedValue;
    analogWrite(enablePin, currentSpeed);
    Serial.print("Speed: ");
    Serial.println(currentSpeed);
  } else {
    Serial.println("Error: Speed value required");
  }
}

void rotateClockwise() {
  digitalWrite(in1Pin, HIGH);
  digitalWrite(in2Pin, LOW);
  analogWrite(enablePin, currentSpeed);  // Mevcut hızı uygula
  Serial.println("Direction: CW");
}

void rotateCounterClockwise() {
  digitalWrite(in1Pin, LOW);
  digitalWrite(in2Pin, HIGH);
  analogWrite(enablePin, currentSpeed);  // Mevcut hızı uygula
  Serial.println("Direction: CCW");
}

void stopMotor() {
  digitalWrite(in1Pin, LOW);
  digitalWrite(in2Pin, LOW);
  currentSpeed = 0;
  analogWrite(enablePin, 0);
  Serial.println("Motor STOPPED");
}

void brakeMotor() {
  digitalWrite(in1Pin, HIGH);
  digitalWrite(in2Pin, HIGH);
  analogWrite(enablePin, 0);
  Serial.println("Motor BRAKE");
}