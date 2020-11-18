#!/usr/bin/env python


import time
import math
import cv2
import os
from niryo_one_tcp_client import *
from niryo_one_camera import *
import utils

robot_ip_address = "192.168.1.202"  # Replace by robot ip address
workspace = "workspace_1"  # Name of your workspace
observation_pose = PoseObject(  # position for the robot to watch the workspace
    x=0.20, y=0, z=0.4,
    roll=0.0, pitch=math.pi / 2 + 0.05, yaw=0.0,
)


def labelling(client, name):
    try:
        os.mkdir("./data/" + name)
    except:
        pass
    print("label ", name)
    a, img_work = utils.take_workspace_img(client)

    mask = utils.objs_mask(img_work)

    debug = concat_imgs([img_work, mask], 1)
    if __name__ == '__main__':
        show_img("robot view", debug, wait_ms=1)
    objs = utils.extract_objs(img_work, mask)
    if len(objs) != 0:
        print(str(len(objs)) + " object detected")
        objs[0].img = resize_img(objs[0].img, width=64, height=64)
        if __name__ == '__main__':
            show_img("robot view2", img_work, wait_ms=50)
        print("saved", name)
        cv2.imwrite("./data/" + name + "/" + str(time.time()) + ".jpg", img_work)
    else:
        print(str(len(objs)) + " object detected")
    return img_work


if __name__ == '__main__':
    def Nothing(val):
        pass

    # Connecting to robot
    client = NiryoOneClient()
    client.connect(robot_ip_address)
    try:
        client.calibrate(CalibrateMode.AUTO)
        client.change_tool(RobotTool.VACUUM_PUMP_1)
    except:
        print("calibration failed")
    name = input("object name :")
    client.move_pose(*observation_pose.to_list())
    try:
        os.mkdir("./data")
    except:
        pass
    try:
        os.mkdir("./data/" + name)
    except:
        pass
    a, img_work = utils.take_workspace_img(client)
    show_img("robot view", img_work, wait_ms=50)
    cv2.createTrackbar("threshold", "robot view", 130, 256, Nothing)
    while "user doesn't quit":
        input("press enter to take picture")
        labelling(client, name)
