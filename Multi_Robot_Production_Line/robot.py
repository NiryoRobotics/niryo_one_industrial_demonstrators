#!/usr/bin/env python

import os
import sys
import math
import copy
import random
import time
import threading
from threading import *
from niryo_one_tcp_client import *
from niryo_one_camera import *

# robot 1
robot1_ip_address = "192.168.1.202"  # Replace by robot ip address
client1_tool = RobotTool.GRIPPER_2
workspace1 = "workspace_loop"  # Name of your workspace
observation_pose = PoseObject(  # position for the robot to watch the conveyor
    x=0.10, y=-0.1, z=0.4,
    roll=math.pi / 2, pitch=math.pi / 2, yaw=0.0,
)

# robot 2
robot2_ip_address = "192.168.1.20"  # Replace by robot ip address
client2_tool = RobotTool.VACUUM_PUMP_1

# conveyor
conveyor_speed = 100  # speed of the conveyor between 0 and 100
conveyor_place_interval = 1.5  # minimal interval between conveyor places  (in seconds)
rand_drop = 1  # value between 0 and 1 how much random is use to determine the drop position


# main loop for the two robots
class RobotsMains:
    def __init__(self, client1, client2, workspace, data):
        self.data = data
        self.client1 = client1
        self.client2 = client2
        self.slope_evt = threading.Event()
        self.slope_evt.set()
        self.workspace = workspace
        self.stock = 0
        self.conveyor_move_time = 0

    # starting a thread of each robot
    def run(self):
        robot1_thread = self.RobotLoop(self.client1, self.workspace, 1, self.slope_evt, self.data, self)
        robot2_thread = self.RobotLoop(self.client2, "", 2, self.slope_evt, self.data, self)
        robot1_thread.start()
        robot2_thread.start()

    #this class correpond to a robot, this class is run on a separate thread and permit multiple robots to move simultaneously
    class RobotLoop(threading.Thread):
        def __init__(self, client, workspace, n, slope_evt, data, parent):
            self.data = data
            self.client = client
            self.workspace = workspace
            self.slope_evt = slope_evt
            self.n = n
            self.parent = parent
            Thread.__init__(self)  # init this class has a thread

        def run(self):
            client1.calibrate(CalibrateMode.AUTO)
            self.client.move_joints(*sleep_joints)  # grab
            if self.n == 1:
                self.robot_loop1()
            elif self.n == 2:
                self.robot_loop2()

        # wait for an object to comme on the workspace
        def wait_obj(self):
            self.client.move_pose(*observation_pose.to_list())  # observation
            b, obj_found, pos, shape, color = self.client.detect_object(workspace1, Shape.ANY, Color.ANY)
            if obj_found and pos[0] < 0.90:
                return
            self.client.control_conveyor(ConveyorID.ID_1, True, conveyor_speed, ConveyorDirection.BACKWARD)
            while obj_found is False or pos[0] > 0.90:
                T = time.time()
                success, obj_found, pos, shape, color = self.client.detect_object(workspace1, Shape.ANY, Color.ANY)
                self.parent.conveyor_move_time += time.time() - T
            self.client.control_conveyor(ConveyorID.ID_1, False, conveyor_speed, ConveyorDirection.BACKWARD)

        def robot_loop1(self):
            print("robot1 loop start")
            client1.change_tool(client1_tool)
            client1.set_conveyor(ConveyorID.ID_1, True)
            client1.open_gripper(RobotTool.GRIPPER_2, 500)
            client1.control_conveyor(ConveyorID.ID_1, False, conveyor_speed, ConveyorDirection.BACKWARD)

            while 1:
                # run the conveyor until a pawns get in the workspace
                while 1:
                    success, obj_found, *c = self.client.vision_pick(workspace1, -0.01, Shape.ANY, Color.ANY)
                    if success and obj_found:
                        break
                    self.wait_obj()

                self.slope_evt.wait()  # waiting for the trajectory to be clear
                self.slope_evt.clear()
                self.client.move_joints(*self.data.data[0])  # up
                self.slope_evt.set() # set the trajectory to clear
                self.client.move_joints(*self.data.data[1])  # drop
                self.client.open_gripper(RobotTool.GRIPPER_2, 500)
                self.parent.stock += 1

        def robot_loop2(self):
            print("robot2 loop start")
            client2.change_tool(client2_tool)
            client2.push_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)
            self.client.push_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)

            while 1:
                while 1:
                    print("stock", self.parent.stock, "move_time", self.parent.conveyor_move_time)
                    if self.parent.stock > 0:
                        break
                    time.sleep(0.1)

                self.slope_evt.wait()  # waiting for the trajectory to be clear
                self.slope_evt.clear()  # set the trajectory to clear
                self.client.move_joints(*self.data.data[3])  # up
                self.client.move_joints(*self.data.data[2])  # grab
                self.client.pull_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)
                self.parent.stock -= 1

                while 1:
                    self.client.move_joints(*self.data.data[3])  # up
                    tmp = copy.deepcopy(self.data.data[4])
                    tmp[2] += (random.randrange(1000) / 1000.0 - 0.5) / 4.0 * rand_drop
                    tmp[5] += (random.randrange(1000) / 1000.0 - 0.5) * 0.5 * math.pi * rand_drop
                    a = self.client.move_joints(*tmp)  # drop
                    if a[0]:
                        break
                self.slope_evt.set()

                while 1:
                    print("stock", self.parent.stock, "move_time", self.parent.conveyor_move_time)
                    if self.parent.conveyor_move_time > conveyor_place_interval:
                        break
                    time.sleep(0.1)

                self.client.push_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)
                self.parent.conveyor_move_time = 0


# all the data saved in the files
class SavedData:
    def __init__(self):
        self.names = []
        self.data = []

    def save_array(self, name, array, f):
        f.write(name)
        for x in array:
            f.write(" " + str(x))
        f.write("\n")

    # save all the data to a filename
    def save(self, filename):
        f = open(filename, "x")
        for x in range(len(self.names)):
            self.save_array(self.names[x], self.data[x], f)
            f.close()
            return True

    def load_array(self, string):
        string = string.split(" ")
        array = []
        for x in range(1, len(string)):
            array.append(float(string[x]))
        return array

    # load all the data from a filename
    def load(self, filename):
        f = open(filename, "r")
        str1 = f.read()
        f.close()
        str1 = str1.split("\n")
        self.data = []
        for x in range(len(str1) - 1):
            self.data.append(self.load_array(str1[x]))


def ask_position(data):
    client1.move_joints(*sleep_joints)
    client2.move_joints(*sleep_joints)
    client1.set_learning_mode(True)
    client2.set_learning_mode(True)

    # the text displayed for each ask
    questions = ["client1 intermediate pos",
                 "drop positions of client1",
                 "pick positions of client2",
                 "client1 intermediate pos",
                 "drop positions of client2"]

    # name of the position (cannot contain spaces)
    data.names = ["client1_intermediate_pos",
                  "drop_positions_of_client1",
                  "pick_positions_of_client2",
                  "client1_intermediate_pos",
                  "drop_positions_of_client2"]

    # function execute when position is given [function, args...]
    function = [[nothing],
                [client1.open_gripper, RobotTool.GRIPPER_2, 500],
                [client2.pull_air_vacuum_pump, RobotTool.VACUUM_PUMP_1],
                [nothing],
                [client2.push_air_vacuum_pump, RobotTool.VACUUM_PUMP_1]]

    # client from witch the position is taken
    client = [client1, client1, client2, client2, client2]

    for x in range(len(questions)):
        input(questions[x])
        data.data.append(client[x].get_joints()[1])
        function[x][0](*function[x][1:])
        client[x].set_learning_mode(True)

    client1.move_joints(*sleep_joints)
    client2.move_joints(*sleep_joints)
    client2.set_learning_mode(True)
    client1.set_learning_mode(True)


# load all the robots pose or ask for new ones
def load_data():
    files_name = os.listdir(".")
    data = SavedData()
    if "data.txt" in files_name:
        data.load("data.txt")  # load saved pose from file
    else:
        ask_position(data)  # ask for new pose
        data.save("data.txt")
    return data


def main():
    data = load_data()  # load all the robots pose

    client1.open_gripper(RobotTool.GRIPPER_2, 500)
    client2.push_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)

    main_loops = RobotsMains(client1, client2, workspace1, data)
    main_loops.run()


def nothing(*args):
    pass


# START FLAGS
def reset():  # delete saved pose
    print("reset saved positions")
    if "data.txt" in os.listdir("."):
        os.remove("data.txt")
# END FLAGS

flags = {
    "--reset": reset
}

if __name__ == '__main__':
    # argument parsing
    for av in sys.argv[1:]:
        if av in flags:
            flags[av]()
        else:
            print("unknown flag: ", av)

    # connect to robot1
    client1 = NiryoOneClient()
    client1.connect(robot1_ip_address)

    # connect to robot2
    client2 = NiryoOneClient()
    client2.connect(robot2_ip_address)

    sleep_joints = [0.0, 0.55, -1.2, 0.0, 0.0, 0.0]
    main()
