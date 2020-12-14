1.  ### Introduction:
    

Learn to simulate a production line in multi-robot (threading) with this new demonstrator. You will use the Vision Set, the Conveyor Belt, our TCP API and two robots.



2.  ### Requirements:
    
-   Two Niryo One
-   A Vacuum Pump for the Niryo One
-   A Large Gripper
-   Red, blue and green pawns
-   The Vision Set and a workspace for the Conveyor Belt
-   A Conveyor Belt
-   A slope from the Education Set.




3.  ### Set-up:

#####	Hardware:



Attach the front of the Conveyor Belt to the Niryo One equipped with the Large Gripper. Then, at the back of the Conveyor Belt, attach the robot with the Vacuum Pump.

Midway between the two robots, set the slope provided with the Education Set and attach the four landmarks of the workspace at the front of the Conveyor Belt as seen on the following picture :

Finally, calibrate the workspace.



##### 	Software:



Before launching the program, four variables have to be modified in the robot.py:

robot1_ip_address = [IP of the robot at the front]

workspace1 = [the workspace name]

observation_pose = [the observation pose of the workspace in meters]

robot2_ip_address = [IP of the robot at the back]

  

Then, launch the “python3 robot.py” program.



For the first launch, you need to give five positions to the program with the learning mode (press enter to confirm a position).

  

In that order:

  

Front robot:

-   A position a few centimeters above the slope
    
-   The position from which the robot can drop the pawn on the slope
    

  

Back robot:

-   The position from which the robot can grab the pawn at the bottom of the slope
    
-   A position a few centimeters above the previous position
    
-   A position at the middle of the Conveyor Belt where the robot can drop the pawn.
    

  

Go to Github to get the program to realize this demonstrator.



4.  ### Functioning:
    

Multithreading:



Multithreading allows us to perform several parts of the same program in parallel. You can then perform multiple instructions simultaneously within the same process. The communication of information between the threads is fast and easy, which makes multithreading very practical to control several Niryo One.

  

The program’s main thread launches a thread for each robot to control. Threads communicate with each other through shared variables and with the class threading.Event().

  

This helps in organizing interactions between the two robots as well as the control of the Conveyor Belt and the sharing of the slope.

  

Each thread has an instance of the “NiryoOneClient()” class that allows it to be connected to a robot and to control it.

  

Threads communicate together through variables located in the mother-class “RobotsMains”.



5.  ### Features:
    

The learning mode allows you to save positions. To get new positions, enter {--reset}.

  

The Conveyor Belt speed is adjustable. To do so, change the variable “conveyor_speed = [float from 0 to 100]”.

  

The distance between the pawns is adjustable. To do so, change the variable: “conveyor_place_interval = "[float in activation seconds of the Conveyor Belt]"

  

The width of pawns’ distribution on the Conveyor Belt is adjustable. To do so, change the variable: “rand drop = <float from 0 to 1>”



6.  ### List of the flags:
    

{--reset} : Deletes the saved positions and launches the acquisition of new positions (that is similing to delete or rename the data.txt file)



7.  ### FAQ:
    

Why does the robot not detect the objects on the Conveyor Belt ? (The Conveyor Belt does not stop).

If the robot does not detect the objects placed on the Conveyor Belt, this might be due to the robot’s camera which cannot see the four landmarks of the workspace. Therefore, adjust the observation pose so the robot can see the four landmarks.


The Conveyor Belt doesn’t stop at the end of the program.

  

In that case, relaunch the program and stop it again when the Conveyor Belt stops.





[Check out our website for more details.](https://niryo.com/docs/niryo-one/niryo-one-industrial-demonstrators/multi-robot-production-line/)