#include <SerialCommand.h>

SerialCommand sCmd;
const int ledPin = 9;

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  
  sCmd.addCommand("PWM", setPWM);
  sCmd.addCommand("ON", ledOn);
  sCmd.addCommand("OFF", ledOff);
  
  Serial.println("Ready - Send: ON, OFF, or PWM 128");
}

void loop() {
  sCmd.readSerial();
}

void setPWM() {
  char *arg = sCmd.next();
  if (arg != NULL) {
    int pwmValue = atoi(arg);
    analogWrite(ledPin, pwmValue);
    Serial.print("PWM: ");
    Serial.println(pwmValue);
  }
}

void ledOn() {
  analogWrite(ledPin, 255);
  Serial.println("ON");
}

void ledOff() {
  analogWrite(ledPin, 0);
  Serial.println("OFF");
}
