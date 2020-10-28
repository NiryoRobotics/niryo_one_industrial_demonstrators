
## Introduction

Time has come to fight a worthy opponent, the Niryo One, at Tic-Tac-Toe.

### Demonstrator video:
[![Vision Tic-Tac-Toe Niryo One](https://img.youtube.com/vi/f4utZ7zoycw/maxresdefault.jpg)](https://www.youtube.com/watch?v=f4utZ7zoycw)

This demonstrator uses our API TCP Python, the Niryo One as well as our Vision Set.

The image processing allows the robot to detect every object on the workspace, used as the game board, and the AI makes the Niryo One a fearsome opponent, depending on the level of difficulty chosen at the beginning of every game. 



## Required equipment:

*The Niryo One 
*A vacuum pump
*Five blue pawns and five red pawns
*The Vision Set as well as the workspace
*Optional: the slope from the Education Conveyor Belt.

You can also customize your own workspace.



## Set-up

### Setting up the robot

Start by calibrating the workspace thanks to the Niryo One Studio. The workspace’s name must be the same one as the one you wrote in the robot’s program (named by defaults “workspace_1”).

If your workspace is not in front of the robot, you will have to modify the “observation_pose” variable so as to make the robot detect the four landmarks on the workspace. 

It is very important to firmly attach your robot, the slope and the workspace.


### Setting up the slope

It is absolutely necessary to locate the slope in order to use it before your first use of it. So as to do it:

Place the robot’s suction cup on the pawn at the bottom of the slope.
Press enter
In order to modify the slope’s position, you can also use the --reset (python3 morpion_vision.py --reset ...) or use the menu by using the --menu argument.



Note: If the slope’s position has changed since your last game, it will be necessary to submit its new position to the robot.



## How it works

To implement Tic-Tac-Toe with the Niryo One, we are using the Vision Set to photograph the workspace. Then, the objects’ positions in the workspace are extracted thanks to the image processing functions. Finally, objects are placed in a 3x3 matrix used as a game board. 


With the algorithm and depending on the chosen difficulty, the robot will calculate its next move.

A command will then be sent to the robot so as to make it place the pawn in the right position.


## Features
When you launch the script, you can open a menu by using the --menu command in which you can choose a bunch of settings. These settings will offer you the possibility to change the way the game is played by the robot. Our AI also has the following features:

The program is able to see if the Human player is cheating. In this case, it will launch an animation and will then play its turn.
The difficulty can be adapted, from a never losing AI to an AI playing in a random way (cf. the list of commands).
If the --noslope option is chosen, the robot will automatically clean the workspace before each game or else the robot will put the pawns out of the workspace.
Each time the robot analyzes the workspace, a window opens and shows the image processing that the robot does to locate the pawns. 


## List of commands
{--menu | -m}

This command displays the settings menu.



{NUMBER}

Number is a whole number between 0 and 1000. This command allows you to adjust the AI’s random side. The AI is unbeatable if you set the difficulty to 0, and it plays in an absolutely random way if the difficulty is set to 1000. 



{--loop | -l}

This command triggers the relaunch of any ended game.



{--button | -b}

This command allows you to announce to the robot that your turn is done by pushing on a button plugged in the Niryo One’s GPIO port.



{--noslope | -s}

This command gives you the possibility to use the workspace to store the robot’s pawns rather than on the slope. Before using this command, you must place the robot’s blue pawns on the workspace at the beginning of the game (you can also add them in the storing slope during the game). When this setting is on, the robot will automatically tidy the workspace up at the beginning of each game. Nevertheless, it only works with round pawns as the square ones are too big to be placed on the workspace. 



## Launching a game


### Launching a game with standard settings

Start by putting five blue pawns on the Niryo One’s slope, then, launch the script: “python3 morpion_vision.py”.

Note: When you play for the first time, or when the slope has been moved, the robot will have to know its new position. Check the “Setting-up the slope” part of this demonstration to know how to do so.

The robot will then scan the workspace before going back to its standby position before the beginning of the game.

#### You start the game:

Place a pawn on the workspace wherever you want.
Once the pawn is placed on the workspace, slightly move the robot’s arm to indicate your turn is over.
The robot will scan the workspace and play its turn. You can also connect a button in the robot’s GPIO-input to indicate your turn is over.

Repeat the operation until the end of the game.
When the game is over, the robot will go back to its standby position.



#### The robot starts the game:
In order to indicate that it is the robot’s turn, slightly move its arm. It will then scan the workspace and place its pawn. Once your pawn is on the workspace, move the robot’s arm again and so on, until the end of the game.

[Check out our website for more details](https://niryo.com/docs/niryo-one/niryo-one-industrial-demonstrators/vision-tic-tac-toe/)


