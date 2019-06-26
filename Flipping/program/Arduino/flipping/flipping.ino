/* Pins definition */
#define robot1_bit_0 33 //pin 1A of the robot 1
#define robot1_bit_1 35 //pin 1B of the robot 1
#define robot1_bit_2 37 //pin 1C of the robot 1
#define robot1_state 39 //pin 2A of the robot 1

#define robot2_bit_0 41 //pin 1A of the robot 2
#define robot2_bit_1 43 //pin 1B of the robot 2
#define robot2_bit_2 45 //pin 1C of the robot 2
#define robot2_state 47 //pin 2A of the robot 2

#define led_robot_1 30
#define led_robot_2 12

#define start_button 13

int first_move = false;

void setup() {
  Serial.begin(9600); // Start serial communication

  /**** Set all pins as inputs or outputs ****/
  pinMode(robot1_bit_0, OUTPUT);
  pinMode(robot1_bit_1, OUTPUT);
  pinMode(robot1_state, INPUT);
  pinMode(robot2_bit_0, OUTPUT);
  pinMode(robot2_bit_1, OUTPUT);
  pinMode(robot2_state, INPUT);

  pinMode(led_robot_1, OUTPUT);
  pinMode(led_robot_2, OUTPUT);

  pinMode(start_button, INPUT);

  initialiseRobot1();
  initialiseRobot2();

  Serial.println("Ready"); // Used for debug 
}

void loop() {
  digitalWrite(led_robot_1, HIGH);
  delay(10);
  digitalWrite(led_robot_1, LOW);
  delay(10);
  digitalWrite(led_robot_2, HIGH);
  delay(10);
  digitalWrite(led_robot_2, LOW);
  delay(10);

  while((digitalRead(start_button) == LOW) && 
        (first_move == false)) {
  }
  moveFromRobot1ToRobot2();

  while((digitalRead(start_button) == LOW) && 
        (first_move == true)) {
  }
  moveFromRobot2ToRobot1();
}

void initialiseRobot1() {
  /**** Set all pins to communicate with the robot LOW ****/
  digitalWrite(robot1_bit_0, LOW);
  digitalWrite(robot1_bit_1, LOW);
  digitalWrite(robot1_state, LOW);  
}

void initialiseRobot2() {
  /**** Set all pins to communicate with the robot LOW ****/
  digitalWrite(robot2_bit_0, LOW);
  digitalWrite(robot2_bit_1, LOW);
  digitalWrite(robot2_state, LOW);  
}

void moveFromRobot1ToRobot2() {
  if((digitalRead(robot1_state) == LOW) && 
     (digitalRead(robot2_state) == LOW)) {
    /* Move robot 1 */
    digitalWrite(led_robot_1, HIGH);
    digitalWrite(led_robot_2, LOW);
    digitalWrite(robot1_bit_0, HIGH);
    delay(50);
    while(digitalRead(robot1_state) == LOW) {
      //Wait
    }
    digitalWrite(robot1_bit_0, LOW);
    delay(50);
    
    /* Move robot 2 */
    digitalWrite(led_robot_1, LOW);
    digitalWrite(led_robot_2, HIGH);
    digitalWrite(robot2_bit_0, HIGH);
    delay(50);
    while(digitalRead(robot2_state) == LOW) {
      //Wait
    }
    digitalWrite(robot2_bit_0, LOW);
    delay(50);

    /* Open gripper robot 1 */
    digitalWrite(led_robot_1, HIGH);
    digitalWrite(led_robot_2, LOW);
    digitalWrite(robot1_bit_1, HIGH);
    delay(50);
    while(digitalRead(robot1_state) == LOW) {
      //Wait
    }
    digitalWrite(robot1_bit_1, LOW);
    delay(50);
    
    /* Close gripper robot 2 */
    digitalWrite(led_robot_1, LOW);
    digitalWrite(led_robot_2, HIGH);
    digitalWrite(robot2_bit_1, HIGH);
    delay(50);
    while(digitalRead(robot2_state) == LOW) {
      //Wait
    }
    digitalWrite(robot2_bit_1, LOW);
    delay(50); 
  }

  first_move = true;
}

void moveFromRobot2ToRobot1() {
  first_move = false;
}

