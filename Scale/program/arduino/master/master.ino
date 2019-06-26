/* Including librairies */
#include <PCF8574.h>
#include <Wire.h>

/* Set I2C extender address */
PCF8574 pcf8574_button(0x20); // Expander buttons
PCF8574 pcf8574_robot1(0x21); // Expander robot 1
PCF8574 pcf8574_robot2(0x22); // Expander robot 2

void setup() {
  Serial.begin(9600); // Used for debug

  /* Initialize expanders */
  pcf8574_button.begin();
  pcf8574_robot1.begin();
  pcf8574_robot2.begin();

  initializeRobot1();
  initializeRobot2();
  
  Serial.println("Ready"); // Used for debug
}

void loop() {
  Serial2.begin(9600); // Open Serial2 (bluetooth)
  delay(200);
  int button_pressed = 0;
  int bluetooth_choice = 0;
  int weight = 0;
  int box  = 0;
  if((pcf8574_robot1.readButton(4) == LOW) && 
     (pcf8574_robot2.readButton(3) == LOW)) { // If the 2 robots are ready and are not executing any command
    button_pressed = readButtons();
    if(Serial2.available()){ // If you are connected to the application in bluetooth
      bluetooth_choice = getBluetooth();
      if(bluetooth_choice > 0){
        moveRobot1(bluetooth_choice);
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
    }else if(button_pressed > 0){
      moveRobot1(button_pressed);
      button_pressed = 0;

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
  pcf8574_robot1.write(2, LOW); // Pin 1C of robot 1
  pcf8574_robot1.write(3, LOW); // Pin 2A of robot 1
  pcf8574_robot1.write(4, LOW); // Pin 2B of robot 1
}

void initializeRobot2() {
  pcf8574_robot2.write(0, LOW); // Pin 1A of robot 2  
  pcf8574_robot2.write(1, LOW); // Pin 1B of robot 2
  pcf8574_robot2.write(2, LOW); // Pin 1C of robot 2
  pcf8574_robot2.write(3, LOW); // Pin 2A of robot 2
}

int getBluetooth () {  
  String mychoice = "";
  String prdt1="Product1";
  String prdt2="Product2";
  String prdt3="Product3";
  String prdt4="Product4";
  int numchoice=0;

  mychoice=Serial2.readString();
  if(mychoice.equals(prdt1)) numchoice=1;
  if(mychoice.equals(prdt2)) numchoice=2;
  if(mychoice.equals(prdt3)) numchoice=3;
  if(mychoice.equals(prdt4)) numchoice=4;

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
  if((pcf8574_button.readButton(0) == HIGH) && 
     (pcf8574_button.readButton(1) == LOW) && 
     (pcf8574_button.readButton(2) == LOW) && 
     (pcf8574_button.readButton(3) == LOW)) { // Button 1 is pressed
    Serial.println("Button 1 is pressed");
    return 1;
  }else if((pcf8574_button.readButton(0) == LOW) && 
           (pcf8574_button.readButton(1) == HIGH) && 
           (pcf8574_button.readButton(2) == LOW) && 
           (pcf8574_button.readButton(3) == LOW)) { // Button 2 is pressed
    Serial.println("Button 2 is pressed");
    return 2;
  }else if((pcf8574_button.readButton(0) == LOW) && 
           (pcf8574_button.readButton(1) == LOW) && 
           (pcf8574_button.readButton(2) == HIGH) && 
           (pcf8574_button.readButton(3) == LOW)) { // Button 3 is pressed
    Serial.println("Button 3 is pressed");
    return 3;
  }else if((pcf8574_button.readButton(0) == LOW) && 
           (pcf8574_button.readButton(1) == LOW) && 
           (pcf8574_button.readButton(2) == LOW) && 
           (pcf8574_button.readButton(3) == HIGH)) { // Button 4 is pressed
    Serial.println("Button 4 is pressed");
    return 4;
  }else {
    return 0; 
  }
}

/* Move robot 1 to the position defined by the button */
void moveRobot1(int button_pressed) {
  switch (button_pressed) {
    case 1 :
      pcf8574_robot1.write(0, HIGH); // Pos 1
      delay(50);
      while(pcf8574_robot1.readButton(4) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(0, LOW); // Stop sending the command
      break;
    case 2 :
      pcf8574_robot1.write(1, HIGH); // Pos 2
      delay(50);
      while(pcf8574_robot1.readButton(4) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(1, LOW); // Stop sending the command
      break;
    case 3 :
      pcf8574_robot1.write(2, HIGH); // Pos 3
      delay(50);
      while(pcf8574_robot1.readButton(4) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(2, LOW); // Stop sending the command
      break;
    case 4 :
      pcf8574_robot1.write(3, HIGH); // Pos 4
      delay(50);
      while(pcf8574_robot1.readButton(4) == LOW) {
        // Wait until robot 1 has finished is command 
      }
      pcf8574_robot1.write(3, LOW); // Stop sending the command
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

