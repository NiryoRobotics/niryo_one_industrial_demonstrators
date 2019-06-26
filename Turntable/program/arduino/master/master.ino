/* Including librairies */
#include <PCF8574.h>
#include <Wire.h>

/* Set I2C extender address */
PCF8574 pcf8574_button(0x20); // Expander buttons
PCF8574 pcf8574_robot1(0x21); // Expander robot 1
PCF8574 pcf8574_robot2(0x22); // Expander robot 2

/* Pins definition */
const int smDirectionPin = 2;
const int smStepPin = 3;
int smEnablePin = 7;

void setup() {
  Serial.begin(9600); // Used for debug

  /* Initialize expanders */
  pcf8574_button.begin();
  pcf8574_robot1.begin();
  pcf8574_robot2.begin();

  initializeRobot1();
  initializeRobot2();
  initializeMotor();
  
  Serial.println("Ready"); // Used for debug
}

void loop() {
  Serial2.begin(9600); //ouverture du serial 2 (bluetooth)
  delay(200);
  int button_pressed = -1;
  int bluetooth_choice = -1;
  int weight = 0;
  int box = 0;
  if((pcf8574_robot1.readButton(1) == LOW) && (pcf8574_robot2.readButton(3) == LOW)) { // If the 2 robots are ready and are not executing any command
    button_pressed = readButtons();
    if(Serial2.available()){ // If you are connected to the application in bluetooth
      bluetooth_choice = getBluetooth();
      if(bluetooth_choice >= 0){
        robot1Pick(bluetooth_choice);
        /* Read the scales value */
        Serial1.begin(9600); // Open serial 1 to catch the weight value
        Serial1.flush(); // Waits for the transmission of outgoing serial data to complete.
        delay(1500); // Wait for the weight to stabilize
        weight = getBalanceWeight();
        Serial.println(weight); // Debug
        Serial1.end();

        box = chooseBox(weight);

        moveRobot2(box);
      }
    }else if(button_pressed >= 0){
      robot1Pick(button_pressed);
      button_pressed = -1;

      /* Read the scales value */
      Serial1.begin(9600); // Open serial 1 to catch the weight value
      Serial1.flush(); // Waits for the transmission of outgoing serial data to complete.
      delay(1500); // Wait for the weight to stabilize
      weight = getBalanceWeight();
      Serial.println(weight); // Debug
      Serial1.end();

      box = chooseBox(weight);

      moveRobot2(box);
    }
  }

}

void initializeRobot1() {
  pcf8574_robot1.write(0, LOW); // Pin 1A of robot 1  
  pcf8574_robot1.write(1, LOW); // Pin 1B of robot 1
}

void initializeRobot2() {
  pcf8574_robot2.write(0, LOW); // Pin 1A of robot 2  
  pcf8574_robot2.write(1, LOW); // Pin 1B of robot 2
  pcf8574_robot2.write(2, LOW); // Pin 1C of robot 2
  pcf8574_robot2.write(3, LOW); // Pin 2A of robot 2
}

void initializeMotor() {
  pinMode(smDirectionPin, OUTPUT);
  pinMode(smStepPin, OUTPUT);
  pinMode(smEnablePin, OUTPUT);
 
  digitalWrite(smEnablePin, HIGH); //Disbales the motor, so it can rest untill it is called uppond
}

int getBluetooth () {  
  String mychoice = "";
  String prdt1="Product1";
  String prdt2="Product2";
  String prdt3="Product3";
  String prdt4="Product4";
  String prdt5="Product5";
  String prdt6="Product6";
  String prdt7="Product7";
  String prdt8="Product8";
  String prdt9="Product9";
  String prdt10="Product10";
  String prdt11="Product11";
  String prdt12="Product12";
  int numchoice= -1;

  mychoice=Serial2.readString();
  if(mychoice.equals(prdt1)) numchoice=0;
  if(mychoice.equals(prdt2)) numchoice=1;
  if(mychoice.equals(prdt3)) numchoice=2;
  if(mychoice.equals(prdt4)) numchoice=3;
  if(mychoice.equals(prdt5)) numchoice=4;
  if(mychoice.equals(prdt6)) numchoice=5;
  if(mychoice.equals(prdt7)) numchoice=6;
  if(mychoice.equals(prdt8)) numchoice=7;
  if(mychoice.equals(prdt9)) numchoice=8;
  if(mychoice.equals(prdt10)) numchoice=9;
  if(mychoice.equals(prdt11)) numchoice=10;
  if(mychoice.equals(prdt12)) numchoice=11;

  if(numchoice>0){
    Serial.print("num choix bluetooth :");
    Serial.println(numchoice);
  }
  Serial2.end();
  return numchoice;
}

int getBalanceWeight() {
  int weight = Serial1.parseInt(); // Read the int value received in serial 1
  delay(100);
  return weight;
}

/* Read which button is pressed */
int readButtons() {
  if((pcf8574_button.readButton(0) == HIGH) && (pcf8574_button.readButton(1) == LOW) && (pcf8574_button.readButton(2) == LOW) && (pcf8574_button.readButton(3) == LOW)) { // Button 1 is pressed
    Serial.println("Button 1 is pressed");
    return 0;
  }else if((pcf8574_button.readButton(0) == LOW) && (pcf8574_button.readButton(1) == HIGH) && (pcf8574_button.readButton(2) == LOW) && (pcf8574_button.readButton(3) == LOW)) { // Button 2 is pressed
    Serial.println("Button 2 is pressed");
    return 3;
  }else if((pcf8574_button.readButton(0) == LOW) && (pcf8574_button.readButton(1) == LOW) && (pcf8574_button.readButton(2) == HIGH) && (pcf8574_button.readButton(3) == LOW)) { // Button 3 is pressed
    Serial.println("Button 3 is pressed");
    return 6;
  }else if((pcf8574_button.readButton(0) == LOW) && (pcf8574_button.readButton(1) == LOW) && (pcf8574_button.readButton(2) == LOW) && (pcf8574_button.readButton(3) == HIGH)) { // Button 4 is pressed
    Serial.println("Button 4 is pressed");
    return 9;
  }else {
    return -1; 
  }
}

/* Move robot 1 to the position defined by the button */
void robot1Pick(int button_pressed) {
  switch (button_pressed) {
    case 0 : //Pos 0
      rotate(button_pressed*107);      
      pcf8574_robot1.write(0, HIGH);
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107);
      break;
    case 1 : //Pos 1
      rotate(button_pressed*107);      
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 2 : //Pos 2
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 3 : //Pos 3
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 4 : //Pos 4
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 5 : //Pos 5
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 6 : //Pos 6
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 7 : //Pos 7
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 8 : //Pos 8
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 9 : //Pos 9
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 10 : //Pos 10
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;
    case 11 : //Pos 11
      rotate(button_pressed*107); 
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(1) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      rotate(-button_pressed*107); 
      break;  
  }
}

/* Define in which box the object has to be place */
int chooseBox(int weight) {
  if(weight <= 50) {
    return 1;
  } else if(weight <= 100) {
    return 2;
  }else {
    return 3;
  }
}

/* Move robot 2 to the position defined by the weight */
void moveRobot2(int box) {
  switch (box) {
    case 1 :
      pcf8574_robot2.write(0, HIGH); // Box 1
      delay(50);
      while(pcf8574_robot2.readButton(3) == LOW) {
        // Wait until robot 2 has finished is command 
      }
      pcf8574_robot2.write(0, LOW); // Stop sending the command
      break;
    case 2 :
      pcf8574_robot2.write(1, HIGH); // Box 2
      delay(50);
      while(pcf8574_robot2.readButton(3) == LOW) {
        // Wait until robot 2 has finished is command 
      }
      pcf8574_robot2.write(1, LOW); // Stop sending the command
      break;
    case 3 :
      pcf8574_robot2.write(2, HIGH); // Box 3
      delay(50);
      while(pcf8574_robot2.readButton(3) == LOW) {
        // Wait until robot 2 has finished is command 
      }
      pcf8574_robot2.write(2, LOW); // Stop sending the command
      break;
  }
}

void rotate(int steps) {
  digitalWrite(smEnablePin, LOW); //Enabling the motor, so it will move when asked to
  
  /*This section looks at the 'steps' argument and stores 'HIGH' in the 'direction' variable if */
  /*'steps' contains a positive number and 'LOW' if it contains a negative.*/
  int direction;
 
  if (steps > 0){
    direction = HIGH;
  }else{
    direction = LOW;
  }
 
  
  steps = abs(steps); //Stores the absolute value of the content in 'steps' back into the 'steps' variable
 
  digitalWrite(smDirectionPin, direction); //Writes the direction (from our if statement above), to the EasyDriver DIR pin
 
  /*Steppin'*/
  for (int i = 0; i < steps; i++){
    digitalWrite(smStepPin, HIGH);
    delayMicroseconds(700);
    digitalWrite(smStepPin, LOW);
    delayMicroseconds(700);
  }

  digitalWrite(smEnablePin, HIGH); //Disbales the motor, so it can rest untill the next time it is called uppond
}

