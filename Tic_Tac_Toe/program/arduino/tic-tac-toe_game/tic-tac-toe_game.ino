/**** Pins definition ****/
#define robot_turn_led 23 //led to indicate it's robot turn
#define player_turn_led 25 //led to indicate it's player turn
#define robot_win_led 27 //led to indicate the robot win
#define player_win_led 29 //led to indicate the player win
#define draw_led 31 //led to indicate it's draw

#define robot_bit_0 33 //pin 1A of the robot
#define robot_bit_1 35 //pin 1B of the robot
#define robot_bit_2 37 //pin 1C of the robot
#define robot_bit_3 39 //pin 2A of the robot
#define robot_state 41 //pin 2B of the robot

#define reset_button 40 //button to reset the game

const int sensor[3][3] = { //IR sensors to detect pawn
  {22, 24, 26},
  {28, 30, 32},
  {34, 36, 38}
};

/**** Global constants ****/
#define arduino_delay 1000 // How long the Arduino waits before playing (simulates thought)
#define calibration_time 10 //Time for the sensors to calibrate

const int win[8][3][3] = { //4D array defines all possible winning combinations
  {
    {1, 1, 1},
    {0, 0, 0},
    {0, 0, 0}
  },
  {
    {0, 0, 0},
    {1, 1, 1},
    {0, 0, 0}
  },
  {
    {0, 0, 0},
    {0, 0, 0},
    {1, 1, 1}
  },
  {
    {1, 0, 0},
    {1, 0, 0},
    {1, 0, 0}
  },
  {
    {0, 1, 0},
    {0, 1, 0},
    {0, 1, 0}
  },
  {
    {0, 0, 1},
    {0, 0, 1},
    {0, 0, 1}
  },
  {
    {1, 0, 0},
    {0, 1, 0},
    {0, 0, 1}
  },
  {
    {0, 0, 1},
    {0, 1, 0},
    {1, 0, 0}
  }
};

/**** Global variables ****/
int game_play[3][3] = { //To hold the current game
  {0, 0, 0},
  {0, 0, 0},
  {0, 0, 0}
};

int squares_left = 9; //Number of free squares left on the board

bool player_played = false;
bool robot_played = false;

void setup() {
  Serial.begin(9600); //Start serial communication
  randomSeed(analogRead(0));

  /**** Set all pins as inputs or outputs ****/
  pinMode(robot_turn_led, OUTPUT);
  pinMode(player_turn_led, OUTPUT);
  pinMode(robot_win_led, OUTPUT);
  pinMode(player_win_led, OUTPUT);
  pinMode(draw_led, OUTPUT);

  pinMode(robot_bit_0, OUTPUT);
  pinMode(robot_bit_1, OUTPUT);
  pinMode(robot_bit_2, OUTPUT);
  pinMode(robot_bit_3, OUTPUT);
  pinMode(robot_state, INPUT);

  pinMode(reset_button, INPUT);

  /**** Define sensors as inputs ****/
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      pinMode(sensor[i][j], INPUT);
    }
  }

  /**** Calibration of the sensors ****/
  Serial.print("Calibration ");
  for (int i = 0; i < calibration_time; i++) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("Calibration succeed");

  initialise();

  Serial.println("Ready");
}

void loop() {
  if(!player_played) {
    playersTurn();
  }else if(!robot_played) {
    robotsTurn();
  }
}

void initialise() {
  /**** Reset variables ****/
  squares_left = 9;
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      game_play[i][j] = 0;
    }
  }

  player_played = false;
  

  /**** Set all pins to communicate with the robot LOW ****/
  digitalWrite(robot_bit_0, LOW);
  digitalWrite(robot_bit_1, LOW);
  digitalWrite(robot_bit_2, LOW);
  digitalWrite(robot_bit_3, LOW);
  digitalWrite(robot_state, LOW);

  /**** Test all Leds ****/
  digitalWrite(robot_turn_led, HIGH);
  delay(100);
  digitalWrite(robot_turn_led, LOW);

  digitalWrite(player_turn_led, HIGH);
  delay(100);
  digitalWrite(player_turn_led, LOW);

  digitalWrite(robot_win_led, HIGH);
  delay(100);
  digitalWrite(robot_win_led, LOW);

  digitalWrite(player_win_led, HIGH);
  delay(100);
  digitalWrite(player_win_led, LOW);

  digitalWrite(draw_led, HIGH);
  delay(100);
  digitalWrite(draw_led, LOW);
}

void playersTurn() {
  digitalWrite(player_turn_led, HIGH); //Turn on player_turn_led

  /**** Check if a sensor is activate (state LOW) ****/
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      if((digitalRead(sensor[i][j]) == LOW) && 
         (game_play[i][j] == 0)) { //If a sensor is activate and the position is free, indicate that the player has played and update the game

        /**** Indicate which sensor has been activated ****/
        Serial.print("Sensor activate ");
        Serial.print(i);
        Serial.println(j);

        game_play[i][j] = 1; //Note the square played (1 for player)
        squares_left--; //Update number of squares left
        player_played = true; //Indicate that the player has played
        robot_played = false;

        printGame(); //Print the game to the serial monitor
        checkGame(); //Check if there is a winner
        digitalWrite(player_turn_led, LOW); //Turn off player_turn_led
      }

      delay(5);
    }
  }
}

void robotsTurn() {
  digitalWrite(robot_turn_led, HIGH); //Turn on robot_turn_led
  Serial.println("Robot's turn ...");

  if (!checkPossibilities()) { //Check to see if a winning move can be played
    if (!checkBlockers()) { //Check to see if we can block a win
      randomPlay(); //If there is no winning move to play nor block, pick a random square
    }
  }

  squares_left--; //Update number of squares left
  printGame(); //Print the game to the serial monitor
  checkGame(); //Check for a winner
  digitalWrite(robot_turn_led, LOW);
  initializeRobotBit();
  
}

bool checkPossibilities() { //Check rows, then columns, then diagonals to see if there are two robot's pawns and a free square to make a line of three
  int count = 0; //Used to count the number of robot's pawns aligned
  bool space = false; //Used to indicate if there is a free square
  int x, y = 0; // Used to save the position to play
  
  /**** Check rows ****/
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      if (game_play[i][j] == 2) { //There is a robot's pawn
        count++;
      }
      if (game_play[i][j] == 0) { //There is a free square
        space = true;
        x = i; //Save the x position
        y = j; //Save the y position
      }
      if ((count == 2) && 
          (space)) { //There are 2 robot's pawns on a row and a free square
        Serial.print("Found an obvious row : ");
        Serial.print(x);
        Serial.println(y);

        playPos(x,y); //Tell the robot to play on this position
        return true;
      }
    }
    /**** Reset variables ****/
    count = 0;
    x = 0;
    y = 0;
    space = false;
  }

  /**** Check columns ****/
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      /**** Reverse i and j to check the columns ****/
      if (game_play[j][i] == 2) { //There is a robot's pawn
        count++;
      }
      if (game_play[j][i] == 0) { //There is a free square
        space = true;
        x = j; //Save the x position
        y = i; //Save the y position
      }
      if ((count == 2) && 
          (space) && 
          (!robot_played)) { //There are 2 robot's pawns on a column, a free square and the robot didn't play yet
        Serial.print("Found an obvious column : ");
        Serial.print(x);
        Serial.println(y);

        playPos(x,y); //Tell the robot to play on this position
        return true;
      }
    }
    /**** Reset variables ****/
    count = 0;
    x = 0;
    y = 0;
    space = false;
  }

  /**** Check crosses ****/
  for (int i = 0; i < 3; i++) {
    /**** Check diagonal from top left to bottom right ****/
    if (game_play[i][i] == 2) { //There is a robot's pawn
      count++;
    }
    if (game_play[i][i] == 0) { //There is a free square
      space = true;
      x = i; //Save the x position
      y = i; //Save the y position
    }
    if ((count == 2) && 
        (space) && 
        (!robot_played)) { //There are 2 robot's pawns on the diagonal, a free square and the robot didn't play yet
      Serial.print("Found an obvious diagonal : ");
      Serial.print(x);
      Serial.println(y);

      playPos(x,y); //Tell the robot to play on this position
      return true;
    }
  }
  /**** Reset variables ****/
  count = 0;
  x = 0;
  y = 0;
  space = false;

  /**** Check diagonal from top right to bottom left ****/
  int row = 0; //Used to count up the rows
  for (int i = 2; i >= 0; i--) { //We count down the columns
    if (game_play[row][i] == 2) { //There is a robot's pawn
      count++;
    }
    if (game_play[row][i] == 0) { //There is a free square
      space = true;
      x = row; //Save the x position
      y = i; //Save the y position
    }
    if ((count == 2) && 
        (space) && 
        (!robot_played)) { //There are 2 robot's pawns on the diagonal, a free square and the robot didn't play yet
      Serial.print("Found an obvious diagonal : ");
      Serial.print(x);
      Serial.println(y);

      playPos(x,y); //Tell the robot to play on this position
      return true;
    }
    row ++; //Increment the row
  }
  /**** Reset variables ****/
  count = 0;
  x = 0;
  y = 0;
  space = false;

  return false;
  
}

bool checkBlockers() { //Check if there is a player winning position to block it
  int count = 0; //Used to count the number of player's pawns aligned
  bool space = false; //Used to indicate if there is a free square
  int x, y = 0; // Used to save the position to play
  
  /**** Check rows ****/
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      if (game_play[i][j] == 1) { //There is a player's pawn
        count++;
      }
      if (game_play[i][j] == 0) { //There is a free square
        space = true;
        x = i; //Save the x position
        y = j; //Save the y position
      }
      if ((count == 2) && 
          (space) && 
          (!robot_played)) { //There are 2 player's pawns on a row, a free square, and the robot didn't play yet
        Serial.print("Found a blocker row : ");
        Serial.print(x);
        Serial.println(y);

        playPos(x,y); //Tell the robot to play on this position
        return true;
      }
    }
    /**** Reset variables ****/
    count = 0;
    x = 0;
    y = 0;
    space = false;
  }

  /**** Check columns ****/
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      /**** Reverse i and j to check the columns ****/
      if (game_play[j][i] == 1) { //There is a player's pawn
        count++;
      }
      if (game_play[j][i] == 0) { //There is a free square
        space = true;
        x = j; //Save the x position
        y = i; //Save the y position
      }
      if ((count == 2) && 
          (space) && 
          (!robot_played)) { //There are 2 player's pawns on a column, a free square and the robot didn't play yet
        Serial.print("Found a blocker column : ");
        Serial.print(x);
        Serial.println(y);

        playPos(x,y); //Tell the robot to play on this position
        return true;
      }
    }
    /**** Reset variables ****/
    count = 0;
    x = 0;
    y = 0;
    space = false;
  }

  /**** Check crosses ****/
  for (int i = 0; i < 3; i++) {
    /**** Check diagonal from top left to bottom right ****/
    if (game_play[i][i] == 1) { //There is a player's pawn
      count++;
    }
    if (game_play[i][i] == 0) { //There is a free square
      space = true;
      x = i; //Save the x position
      y = i; //Save the y position
    }
    if ((count == 2) && 
        (space) && 
        (!robot_played)) { //There are 2 player's pawns on the diagonal, a free square and the robot didn't play yet
      Serial.print("Found a blocker diagonal : ");
      Serial.print(x);
      Serial.println(y);

      playPos(x,y); //Tell the robot to play on this position
      return true;
    }
  }
  /**** Reset variables ****/
  count = 0;
  x = 0;
  y = 0;
  space = false;

  /**** Check diagonal from top right to bottom left ****/
  int row = 0; //Used to count up the rows
  for (int i = 2; i >= 0; i--) { //We count down the columns
    if (game_play[row][i] == 1) { //There is a player's pawn
      count++;
    }
    if (game_play[row][i] == 0) { //There is a free square
      space = true;
      x = row; //Save the x position
      y = i; //Save the y position
    }
    if ((count == 2) && 
        (space) && 
        (!robot_played)) { //There are 2 player's pawns on the diagonal, a free square and the robot didn't play yet
      Serial.print("Found a blocker diagonal : ");
      Serial.print(x);
      Serial.println(y);

      playPos(x,y); //Tell the robot to play on this position
      return true;
    }
    row ++; //Increment the row
  }
  /**** Reset variables ****/
  count = 0;
  x = 0;
  y = 0;
  space = false;

  return false;
}

void randomPlay() { //Play a random square
  Serial.println("Chosing randomly...");
  int choice = 0;
  int count = 0;
  bool state = true;

  while(state) {
    choice = random(1,squares_left+1);
    count = 0;
    Serial.print("The robot chose : ");
    Serial.println(choice);
    for (int i = 0; i < 3; i++) {
      for (int j = 0; j < 3; j++) {
        if (game_play[i][j] == 0) {
          count++;
        }
        if((game_play[i][j] == 0) && (choice ==  count)) {
          playPos(i,j);
          state = false;
        }
      }
    }
  }
}

void initializeRobotBit() {
  digitalWrite(robot_bit_0, LOW);
  digitalWrite(robot_bit_1, LOW);
  digitalWrite(robot_bit_2, LOW);
  digitalWrite(robot_bit_3, LOW);
}

void playPos(int x, int y) {
  delay(arduino_delay); //Simulate robot's thought
  Serial.println("Robot played ...");
  Serial.print(x);
  Serial.println(y);

  /**** Send command to the robot ****/
  switch (x) {
    case 0 :
      switch (y) {
        case 0 :
          digitalWrite(robot_bit_0, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_0, LOW);
          Serial.println("Robot play square 1");
          break;
        case 1 :
          digitalWrite(robot_bit_1, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_1, LOW);
          Serial.println("Robot play square 2");
          break;
        case 2 :
          digitalWrite(robot_bit_0, HIGH);
          digitalWrite(robot_bit_1, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_0, LOW);
          digitalWrite(robot_bit_1, LOW);
          Serial.println("Robot play square 3");
          break;        
      }
      break;
    case 1 :
      switch (y) {
        case 0 :
          digitalWrite(robot_bit_2, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
             
          }
          digitalWrite(robot_bit_2, LOW);
          break;
        case 1 :
          digitalWrite(robot_bit_0, HIGH);
          digitalWrite(robot_bit_2, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_0, LOW);
          digitalWrite(robot_bit_2, LOW);
          break;
        case 2 :
          digitalWrite(robot_bit_1, HIGH);
          digitalWrite(robot_bit_2, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_1, LOW);
          digitalWrite(robot_bit_2, LOW);
          break;
      }
      break;
    case 2 :
      switch (y) {
        case 0 :
          digitalWrite(robot_bit_0, HIGH);
          digitalWrite(robot_bit_1, HIGH);
          digitalWrite(robot_bit_2, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_0, LOW);
          digitalWrite(robot_bit_1, LOW);
          digitalWrite(robot_bit_2, LOW);
          break;
        case 1 :
          digitalWrite(robot_bit_3, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_3, LOW);
          break;
        case 2 :
          digitalWrite(robot_bit_0, HIGH);
          digitalWrite(robot_bit_3, HIGH);
          delay(50);
          while (digitalRead(robot_state) == LOW) {
            
          }
          digitalWrite(robot_bit_0, LOW);
          digitalWrite(robot_bit_3, LOW);
          break;
      }
      break;
  }
  
  game_play[x][y] = 2; //Update the game play array
  robot_played = true;
  player_played = false;
}

void printGame() { //Print the game to the serial monitor
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
      Serial.print(game_play[i][j]);
      Serial.print(" ");
    }
    Serial.println("");
  }
  Serial.print(squares_left);
  Serial.println(" squares left");
}

void checkGame() { //Check the game for a winner
  int player = 0;
  int winner  = 0;
  Serial.println("Check for a winner");

  /**** Check if the player has won ****/
  player  = 1; //Squares played by player are at 1
  winner = 0;

  for (int i = 0; i < 8; i++) { //We cycle through all winning combinations int the 4D array and check if one of them correspond to the current game
    int win_check = 0;
    for (int j = 0; j < 3; j++) {
      for (int k = 0; k < 3; k++) {
        if ((win[i][j][k] == 1) && 
           (game_play[j][k] == player)) { //If a square played correspond to one in the winning combinations, we increment win_check
          win_check ++;
        }
      }
    }
    if (win_check == 3) { //It means that the player played three squares that matches with winning combinations
      winner = 1;
      Serial.print("Player won the game ");
      Serial.println(i); //Indicate with wich combination he won
      endGame(1); //Pass 1 to the endGame function to indicate that the player has won
    }
  }

  /**** Check if the robot has won ****/
  player = 2; //Squares played by the robot are at 2
  winner  = 0;
  for (int i = 0; i < 8; i++) { //We cycle through all winning combinations int hte 4D array and check if one of them correspond to the current game
    int win_check = 0;
    for (int j = 0; j < 3; j++) {
      for (int k = 0; k < 3; k++) {
        if ((win[i][j][k] == 1) && 
            (game_play[j][k] == player)) { //If a square played correspond to one in the winning combinations, we increment win_check
          win_check ++;
        }
      }
    }
    if (win_check == 3) { //It means that the robot played three squares that matches with winning combinations
      winner = 1;
      Serial.print("Robot won the game ");
      Serial.println(i); //Indicate with wich combination he won
      endGame(2); //Pass 2 to the endGame function to indicate that the robot has won
    }
  }

  /**** Check if there are no squares left ****/
  if (squares_left == 0) {
    endGame(0); //Pass 0 to the endGame function to indicate that it's a draw
  }
}

void endGame(int winner) { //Function called when there is a winner or no more squares left
  
  digitalWrite(player_turn_led, LOW);
  digitalWrite(robot_turn_led, LOW);
  digitalWrite(draw_led, LOW);
  digitalWrite(player_win_led, LOW);
  digitalWrite(robot_win_led, LOW);
  
  switch (winner) {
    case 0: //It's a draw
      digitalWrite(draw_led, HIGH);
      Serial.println("It's a draw !");
      break;
    case 1: //Player has won
      digitalWrite(player_win_led, HIGH);
      Serial.println("Player won !");
      break;
    case 2: //Robot has won
      digitalWrite(robot_win_led, HIGH);
      Serial.println("Robot won !");
      break;
  }
  while (digitalRead(reset_button) == HIGH) { //Wait until the reset_button is pushed
  }
  Serial.println("RESET");
  initialise(); //Start a new game
}

