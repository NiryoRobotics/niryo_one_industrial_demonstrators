import numpy as np
import cv2
import os
import math
import ctypes
import time
import copy

import pygame
import pygame_menu
import tensorflow as tf

from niryo_one_tcp_client import *
from niryo_one_camera import *

import utils
import labelling
import training

robot_ip_address = "192.168.0.63"  # Replace by robot ip address
workspace = "workspace_1"  # Name of your workspace
observation_pose = PoseObject(  # position for the robot to watch the workspace
    x=0.20, y=0, z=0.4,
    roll=0.0, pitch=math.pi / 2 + 0.05, yaw=0.0,
)

drop_pose = PoseObject(  # position for the robot to drop the object
    x=0.20, y=0.20, z=0.10,
    roll=0.0, pitch=math.pi / 2, yaw=0.0,
)

sleep_joints = [0.0, 0.55, -1.2, 0.0, 0.0, 0.0]

z_offset = -0.00
model = None


class MyButton(pygame_menu.widgets.Button):  # override pygame_menu.widgets.Button for one click activation
    def _focus(self):
        super()._focus()
        super().apply()
        self.get_menu()._select(0)
        self.set_selected(False)


pygame_menu.widgets.Button = MyButton

# Connecting to robot
client = NiryoOneClient()
client.connect(robot_ip_address)
client.calibrate(CalibrateMode.AUTO)
client.change_tool(RobotTool.GRIPPER_2)
client.move_pose(*observation_pose.to_list())

font = cv2.FONT_HERSHEY_SIMPLEX

pygame.init()
logo = None
logo_big = None
try:
    logo = pygame.image.load('Niryo_logo/logo.png')
    logo_big = pygame.image.load('Niryo_logo/logo_big.png')
    pygame.display.set_icon(logo)
except:
    pass

if os.name == 'nt':
    ctypes.windll.user32.SetProcessDPIAware()
    window_x, window_y = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
    surface = pygame.display.set_mode((window_x, window_y), pygame.NOFRAME | pygame.FULLSCREEN)
else:
    infoObject = pygame.display.Info()
    window_x, window_y = infoObject.current_w, infoObject.current_h
    print(window_x, window_y)
    window_x, window_y = 1920, 1080
    surface = pygame.display.set_mode((window_x, window_y), pygame.NOFRAME)
font_size = int(window_y / 20)

pygame.display.set_caption("tensorflow & niryo_one")
logo_big_size = logo_big.get_size()
ratio = (window_x - window_y) / logo_big_size[0] * 0.8

pygame.transform.smoothscale(logo_big, (int(logo_big_size[0] * ratio), int(logo_big_size[1] * ratio)))


def draw_background(img):
    # graphical debug
    surface.fill((0x20, 0x35, 0x67))
    if logo_big is not None:
        surface.blit(logo_big, ((window_x - window_y - logo_big.get_size()[0]) / 2, window_y / 8))
    img = cv2.resize(img, (window_y, window_y))
    img = np.flip(img[:][:])  # BGR to RGB
    img = np.rot90(img, 1, (1, 0))
    img = np.flip(img, 0)

    surf = pygame.surfarray.make_surface(img)
    surface.blit(surf, (window_x - window_y, 0))
    cv2.destroyAllWindows()


def get_all_objs():
    a, img_work = utils.take_workspace_img(client)
    img_work = utils.standardize_img(img_work)

    if not a:
        a, img_work = debug_markers(img_work)
        return img_work, None
    mask = utils.objs_mask(img_work)
    objs = utils.extract_objs(img_work, mask)
    if len(objs) == 0:
        return img_work, []
    imgs = []
    if model is None:
        return img_work, objs
    for x in range(len(objs)):
        imgs.append(cv2.resize(objs[x].img, (64, 64)))

    imgs = np.array(imgs)
    predictions = model.predict(imgs)
    for x in range(len(predictions)):
        obj = objs[x]
        obj.type = predictions[x].argmax()

        # graphical debug
        cv2.drawContours(img_work, [obj.box], 0, (0, 0, 255), 2)
        pos = [obj.square[0][1], obj.square[1][1]]
        img_work = cv2.putText(img_work, objects_names[obj.type], tuple(pos), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        pos[0] += img_work.shape[0]
        img_work = cv2.putText(img_work, objects_names[obj.type], tuple(pos), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

    return img_work, objs


def pick_by_name(name):
    if model is None:
        return
    img_work, objs = get_all_objs()
    if objs is None:
        return
    shape = img_work.shape
    for x in range(len(objs)):
        if objects_names[objs[x].type] == name:
            print("object find")
            a, obj = client.get_target_pose_from_rel(workspace, z_offset, objs[x].x / shape[0], objs[x].y / shape[1], objs[x].angle)
            client.pick_from_pose(*obj.to_list())
            client.place_from_pose(*drop_pose.to_list())
            break
    client.move_pose(*observation_pose.to_list())


def background():
    if model:
        img_work, ok = get_all_objs()
        if ok is None:
            ok = False
        draw_background(img_work)
    else:
        ok, img = utils.take_workspace_img(client)
        draw_background(img)

    if not ok:
        client.move_pose(*observation_pose.to_list())


def close_aplication():
    client.move_joints(*sleep_joints)
    client.set_learning_mode(True)
    exit(0)


def wait_key_pressed(t):
    for x in range(int(t * 30) + 1):
        time.sleep(1.0 / 30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONUP:
                return 1
    return 0


def change_observation_pose():
    while 1:
        client.set_learning_mode(True)
        pygame.event.get()
        while not wait_key_pressed(0):
            a, mtx, dist = client.get_calibration_object()
            a, img_compressed = client.get_img_compressed()
            img_raw = uncompress_image(img_compressed)
            img = undistort_image(img_raw, mtx, dist)
            a, img2 = debug_markers(img)
            color = [255, 0, 0]
            if a:
                img = img2
                color = [0, 255, 0]
            pygame.draw.rect(surface, color, [0, 0, window_x - window_y, window_y])
            img = np.flip(img[:][:])  # BGR to RGB
            img = cv2.resize(img, (window_y, window_y))
            img = np.rot90(img, 1, (1, 0))
            img = np.flip(img, 0)
            surf = pygame.surfarray.make_surface(img)
            surface.blit(surf, (window_x - window_y, 0))
            pygame.display.flip()
        pose = client.get_pose()[1]
        client.set_learning_mode(False)
        client.move_pose(*pose.to_list())
        a, mtx, dist = client.get_calibration_object()
        a, img_compressed = client.get_img_compressed()
        img_raw = uncompress_image(img_compressed)
        img = undistort_image(img_raw, mtx, dist)
        a, img2 = debug_markers(img)
        if a:
            observation_pose.x = pose.x
            observation_pose.y = pose.y
            observation_pose.z = pose.z
            observation_pose.roll = pose.roll
            observation_pose.pitch = pose.pitch
            observation_pose.yaw = pose.yaw
            return


def change_droping_pos():
    color = [0, 255, 0]
    pygame.draw.rect(surface, color, [0, 0, window_x - window_y, window_y])
    pygame.display.flip()
    client.set_learning_mode(True)
    pygame.event.get()
    while not wait_key_pressed(0.25):
        pass
    pose2 = client.get_pose()[1]
    client.set_learning_mode(False)
    drop_pose.x = pose2.x
    drop_pose.y = pose2.y
    drop_pose.z = pose2.z
    drop_pose.roll = pose2.roll
    drop_pose.pitch = pose2.pitch
    drop_pose.yaw = pose2.yaw
    time.sleep(1)
    client.move_pose(*observation_pose.to_list())


def labelling_event(client, widget):
    labelling.labelling(client, widget.get_value())
    surface.fill((int(0xFF / 2), int(0xFF / 2), int(0xFF / 2)))
    pygame.display.flip()
    time.sleep(1 / 30)


def training_event():
    global model
    model = training.training()
    init_all()


def labbeling_menu_event():
    labbeling_menu.mainloop(surface, background)
    labbeling_menu.enable()


def select_menu_event(x):
    select_menu[x].enable()
    select_menu[x].mainloop(surface, background)


def settings_menu_event():
    settings_menu.mainloop(surface, background)
    settings_menu.enable()


def menu_back_1(menu):
    print("reset", menu)
    menu._back()


def menu_close(menu):
    print("close", menu)
    menu._close()


def event_change_objname(choice, menu):
    print(choice, " | ", menu)
    menu.get_widget("objname").set_value(choice[0])


def event_quit_select_menu():
    for menu in select_menu:
        menu.disable()


def add_logo(name):
    objects_logo = os.listdir("logo/")
    if not ((name + ".jpg") in objects_logo):
        print(name, "logo not found")
        img_names = None
        try:
            img_names = os.listdir("./data_mask/" + name)
        except:
            pass
        if img_names is None or len(img_names) == 0:
            img_logo = np.zeros((64, 64, 3), np.float32)
        else:
            img_logo = cv2.imread("./data_mask/" + name + "/" + img_names[0])
        cv2.imwrite("./logo/" + name + ".jpg", img_logo)


menu_size = [window_y, window_x - window_y]
menu_pos = [0, 0]

main_menu = None
select_menu = []
labbeling_menu = None
settings_menu = None
objects_names = None
model = None
select_menu_height = 6
select_menu_enabled = True

niryo_theme = pygame_menu.themes.Theme(
    title_font=pygame_menu.font.FONT_OPEN_SANS,
    title_font_color=(0x20, 0x35, 0x67),
    title_background_color=(0xFF, 0xFF, 0xFF),

    widget_font=pygame_menu.font.FONT_OPEN_SANS,
    widget_font_color=(0xFF, 0xFF, 0xFF),
    background_color=(0xFF, 0xFF, 0xFF, 0x0),

    widget_alignment=pygame_menu.locals.ALIGN_CENTER,
    widget_margin=(0, 0))


def init_all():
    global main_menu
    global labbeling_menu
    global select_menu
    global select_menu_height
    global settings_menu
    global objects_names
    global model

    select_menu = []

    # test observation_pose
    client.move_pose(*observation_pose.to_list())
    a, img = utils.take_workspace_img(client)
    if not a:
        change_observation_pose()

    # test data folder and model folder
    try:
        os.mkdir("./data")
    except:
        pass
    try:
        objects_names = os.listdir("data/")
    except:
        objects_names = []

    if len(objects_names) == 0:
        objects_names = [" "]

    try:
        model = tf.keras.models.load_model('model')
        if len(model.predict(np.zeros((1, 64, 64, 3), np.float32))[0]) != len(objects_names):
            model = None
    except:
        pass

    # labbeling menu
    labbeling_menu = pygame_menu.Menu(*menu_size, 'Labelling',
                                      theme=niryo_theme,
                                      menu_position=menu_pos,
                                      onclose=pygame_menu.events.BACK)
    objects_names_plus = copy.deepcopy(objects_names)
    n = 1
    while ("obj_" + str(n)) in objects_names:
        n += 1

    objects_names_plus.append("obj_" + str(n))
    objects_names_ziped = list(zip(objects_names_plus, [labbeling_menu] * (len(objects_names) + 1)))

    labbeling_menu.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
    labbeling_menu.add_selector("name: ", objects_names_ziped, onchange=event_change_objname,
                                selector_id="objinputname", font_size=font_size, shadow=True, shadow_offset=2)
    widget_text = labbeling_menu.add_text_input("name: ", default='obj_name', textinput_id='objname', onchange=None,
                                                font_size=font_size, shadow=True, shadow_offset=2)
    labbeling_menu.add_button("add img", labelling_event, client, widget_text, font_size=font_size, shadow=True,
                              shadow_offset=2)
    labbeling_menu.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
    labbeling_menu.add_button("Back", menu_back_1, labbeling_menu, font_size=font_size, shadow=True, shadow_offset=2)

    # settings_menu
    settings_menu = pygame_menu.Menu(*menu_size, 'Settings',
                                     theme=niryo_theme,
                                     menu_position=menu_pos,
                                     onclose=pygame_menu.events.BACK)

    settings_menu.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
    settings_menu.add_button("Observation Pose", change_observation_pose, font_size=font_size, shadow=True,
                             shadow_offset=2)
    settings_menu.add_button("Drop pose", change_droping_pos, font_size=font_size, shadow=True, shadow_offset=2)
    settings_menu.add_button(labbeling_menu.get_title(), labbeling_menu_event, font_size=font_size, shadow=True,
                             shadow_offset=2)
    settings_menu.add_button("Train", training_event, font_size=font_size, shadow=True, shadow_offset=2)
    settings_menu.add_button("Update", init_all, font_size=font_size, shadow=True, shadow_offset=2)
    settings_menu.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
    settings_menu.add_button("Back", menu_back_1, settings_menu, font_size=font_size, shadow=True, shadow_offset=2)

    # select_menus
    try:
        os.mkdir("./logo")
    except:
        pass

    print('len', int(len(objects_names) / select_menu_height + 1), len(objects_names))
    select_menu_nbs = int(len(objects_names) / select_menu_height + 1)
    for menu_id in range(int(len(objects_names) / select_menu_height + 1)):
        select_menu.append(pygame_menu.Menu(*menu_size, 'Play',
                                            theme=niryo_theme,
                                            menu_position=menu_pos,
                                            columns=2,
                                            rows=select_menu_height + 5,
                                            onclose=pygame_menu.events.BACK
                                            ))
        select_menu_x = select_menu[-1]
        select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
        select_menu_x.add_vertical_margin(logo_big.get_size()[1])
        if 0 != menu_id:
            select_menu_x.add_button("<==", menu_back_1, select_menu_x, font_size=font_size, shadow=True,
                                     shadow_offset=2)
        else:
            select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)

        for name in objects_names:
            add_logo(name)

        all_button = []
        for x in range(select_menu_height):
            x += select_menu_height * menu_id
            if x >= len(objects_names):
                select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
            else:
                button = select_menu_x.add_button(objects_names[x], pick_by_name, objects_names[x], font_size=font_size,
                                                  shadow=True, shadow_offset=2)
                all_button.append(button)
        select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
        select_menu_x.add_button("Back", event_quit_select_menu, font_size=font_size, shadow=True, shadow_offset=2)
        select_menu_x.add_button("", None, font_size=font_size, shadow=True, shadow_offset=2)
        select_menu_x.add_vertical_margin(logo_big.get_size()[1])
        if menu_id != select_menu_nbs - 1:
            select_menu_x.add_button("==>", select_menu_event, menu_id + 1, font_size=font_size, shadow=True,
                                     shadow_offset=2)
        else:
            select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)

        for x in range(select_menu_height):
            xx = x + menu_id * select_menu_height
            if xx >= len(objects_names):
                select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
            else:
                img_logo = cv2.imread("./logo/" + objects_names[xx] + ".jpg")
                scale = all_button[x].get_rect().height / img_logo.shape[1]
                widget_img = select_menu_x.add_image("./logo/" + objects_names[xx] + ".jpg", scale=(scale, scale),
                                                     scale_smooth=True)
                img = cv2.imread("./logo/" + objects_names[xx] + ".jpg")
                img = cv2.resize(img, widget_img._image._surface.get_size())

                color_hsl = [[0, 0, 0], [256, 20, 256]]
                mask = cv2.bitwise_not(utils.threshold_hls(img, *color_hsl))
                img_masked = cv2.bitwise_and(img, img, mask=mask)

                img_masked = np.flip(img_masked[:][:])  # BGR to RGB
                img_masked = np.rot90(img_masked, 1, (1, 0))
                img_masked = np.flip(img_masked, 0)

                surf = pygame.surfarray.make_surface(img_masked)
                widget_img._image._surface.blit(surf, (0, 0))

            widget_img._image._surface.set_colorkey((0, 0, 0))
            widget_img._image.checkpoint()

        select_menu_x.add_button(str(menu_id + 1) + "/" + str(select_menu_nbs), None, font_size=font_size, shadow=True,
                                 shadow_offset=2)
        select_menu_x.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)



init_all()
main_menu = pygame_menu.Menu(*menu_size, 'Welcome',
                             theme=niryo_theme,
                             menu_position=menu_pos,
                             onclose=close_aplication)
main_menu.add_button('', None, font_size=font_size, shadow=True, shadow_offset=2)
main_menu.add_button(select_menu[0].get_title(), select_menu_event, 0, font_size=font_size, shadow=True,
                     shadow_offset=2)
main_menu.add_button(settings_menu.get_title(), settings_menu_event, font_size=font_size, shadow=True, shadow_offset=2)
main_menu.add_button('Quit', close_aplication, font_size=font_size, shadow=True, shadow_offset=2)

main_menu.mainloop(surface, background)

client.move_joints(*move_joints)
