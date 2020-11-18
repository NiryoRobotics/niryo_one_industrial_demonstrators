#!/usr/bin/env python

import numpy as np
import cv2
import os
import tensorflow as tf
from niryo_one_tcp_client import *
from niryo_one_camera import *
import utils

robot_ip_address = "192.168.1.202"  # Replace by robot ip address
workspace = "workspace_1"  # Name of your workspace
observation_pose = PoseObject(  # position for the robot to watch the workspace
    x=0.20, y=0, z=0.4,
    roll=0.0, pitch=math.pi / 2 + 0.05, yaw=0.0,
)

drop_pose = PoseObject(  # position for the robot to watch the workspace
    x=0.20, y=0.20, z=0.10,
    roll=0.0, pitch=math.pi / 2, yaw=0.0,
)

# Connecting to robot
client = NiryoOneClient()
client.connect(robot_ip_address)

objects_names = os.listdir("data/")
model = tf.keras.models.load_model('model')
font = cv2.FONT_HERSHEY_SIMPLEX

try:
    client.calibrate(CalibrateMode.AUTO)
except:
    print("calibration failed")

client.change_tool(RobotTool.GRIPPER_2)


while 1:
    #move to observation_pose
    client.move_pose(*observation_pose.to_list())
    a = False

    #take a picture of the workspace (infinite loop if the robot can't see the workspace)
    while not a:
        a, img_work = utils.take_workspace_img(client)

    img_work = utils.standardize_img(img_work)

    #calculate the mask for img_work (black and white image)
    mask = utils.objs_mask(img_work)
    #aply the mask to the image
    img_masked = cv2.bitwise_and(img_work, img_work, mask=mask)

    img_db = concat_imgs([img_work, mask, img_masked], 1)

    #get all opbject from the image
    objs = utils.extract_objs(img_work, mask)
    if len(objs) == 0:
        continue

    imgs = []
    #resize all objects img to 64*64 pixels
    for x in range(len(objs)):
        imgs.append(resize_img(objs[x].img, width=64, height=64))

    imgs = np.array(imgs)

    #predict all the images
    predictions = model.predict(imgs)

    #for all predictions find the corresponding name and print it on img_db
    for x in range(len(predictions)):
        obj = objs[x]
        pred = predictions[x].argmax()
        cv2.drawContours(img_db, [obj.box], 0, (0, 0, 255), 2)
        pos = [obj.square[0][1], obj.square[1][1]]
        img_db = cv2.putText(img_db, objects_names[pred], tuple(pos), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        pos[0] += img_db.shape[0]
        img_db = cv2.putText(img_db, objects_names[pred], tuple(pos), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    img_db = resize_img(img_db, width=1200, height=400)

    show_img("robot view", img_db, wait_ms=50)

    shape = img_work.shape

    print(objects_names)
    #ask to the user the name of the object he want
    string = input("what do you want? (", +str(objects_names)+")")

    #find an object with the same name in the model predictions
    for x in range(len(predictions)):
        pred = predictions[x].argmax()

        if objects_names[pred] == string:
            print("object find")
            #calculate the position of the object and grab it
            a, obj = client.get_target_pose_from_rel(workspace, -0.01, objs[x].x / shape[0], objs[x].y / shape[1],
                                                     objs[x].angle)
            client.pick_from_pose(*obj.to_list())
            client.place_from_pose(*drop_pose.to_list())
            break
