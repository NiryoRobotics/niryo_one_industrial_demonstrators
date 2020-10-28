# ./python3 morpion_vision.py <randomness> [loop, green]
# randomness between 0 and 100

from niryo_one_tcp_client import *
from niryo_one_camera import *
import time
import math
import numpy as np
import cv2
import sys
import random
import copy

robot_ip_address = "10.10.10.10"  # Replace by robot ip addresss
workspace = "workspace_1"  # Name of your workspace
observation_pose = PoseObject(  # position for the robot to watch the workspace
    x=0.25, y=0, z=0.4,
    roll=0.0, pitch=math.pi / 2, yaw=0.0,
)

button_pin = RobotPin.GPIO_1A  # GPIO of the button only if you use the --button or -b flags


# Connecting to robot
client = NiryoOneClient()
client.connect(robot_ip_address)

slope_pos = []
cheat_pose = copy.deepcopy(observation_pose)
cheat_pose.pitch = 0
global_z_offset = 0.00

sleep_joints = [0.0, 0.55, -1.2, 0.0, 0.0, 0.0]
grid_size = [4, 4]


class Object:
    def __init__(self, pose, shape, color, angle, cx_rel, cy_rel, cx, cy):
        self.obj_pos = pose  # pos relative to the arm
        self.shape = shape  # ObjectShape.SQUARE || ObjectShape.CIRCLE
        self.color = color  # Color.<color>
        self.angle = angle  # angle relative to the arm
        self.cx_rel = cx_rel  # pos relative to workspace
        self.cy_rel = cy_rel
        self.cx = cx
        self.cy = cy


# this function draw a debug grid on an image
def draw_debug(img):
    db_cnt = 3
    sx, sy, *sz = img.shape
    seg = int(sx / grid_size[0])
    off_x = 0

    if grid_size == [4, 4]:
        # blue circle stock
        img[0:sx, seg * 0:seg * 0 + db_cnt] = [255, 0, 0]
        img[0:sx, seg * 1 - db_cnt:seg * 1] = [255, 0, 0]
        img[seg * 0:seg * 0 + db_cnt, 0:seg] = [255, 0, 0]
        for x in range(1, 4):
            img[seg * x - db_cnt:seg * x + db_cnt, 0:seg] = [255, 0, 0]
    elif grid_size == [3, 3]:
        off_x = 1

    # green play area
    img[0:seg * 3, seg * (1 - off_x):seg * (1 - off_x) + db_cnt] = [0, 255, 0]
    img[0:seg * 3, seg * (4 - off_x) - db_cnt:seg * (4 - off_x)] = [0, 255, 0]
    img[seg * 0:seg * 0 + db_cnt, seg * (1 - off_x):sy] = [0, 255, 0]
    img[seg * 3 - db_cnt:seg * 3, seg * (1 - off_x):sy] = [0, 255, 0]
    for x in range(2 - off_x, 4 - off_x):
        img[0:seg * 3, seg * x - db_cnt:seg * x + db_cnt] = [0, 255, 0]
    for x in range(1, 3):
        img[seg * x - db_cnt:seg * x + db_cnt, seg * (1 - off_x):sx] = [0, 255, 0]


# get to observation_pose and scan the workplace
# return an array of shape
def get_all_object():
    while 1:
        # take a photo and extract the workspace
        client.move_pose(*observation_pose.to_list())
        a, mtx, dist = client.get_calibration_object()
        a, img_compressed = client.get_img_compressed()
        img_raw = uncompress_image(img_compressed)
        img = undistort_image(img_raw, mtx, dist)
        img_work = extract_img_workspace(img, workspace_ratio=1)

        # if the workspace extraction failed
        if img_work is None:
            print("get_all_object failed")
            img = resize_img(img, width=600, height=600)
            show_img("robot view", img)
            continue
        break

    img_threshold_rgb = []
    img_erode_rgb = []
    color_hsv = [ColorHSV.RED.value, ColorHSV.GREEN.value, ColorHSV.BLUE.value]
    cnts_rgb = []
    objects = []
    color_rgb = [Color.RED, Color.GREEN, Color.BLUE]

    for x in range(0, 3):
        pass

        # transform for RED
        img_threshold_rgb.append(threshold_hsv(img_work, *color_hsv[x]))
        img_erode = img_threshold_rgb[x]
        for y in range(0, 1):
            img_erode = morphological_transformations(img_erode, morpho_type="ERODE", kernel_shape=(14, 14))
            img_erode = morphological_transformations(img_erode, morpho_type="DILATE", kernel_shape=(10, 10))
        img_erode_rgb.append(img_erode)

        # extract the contours
        cnts_rgb.append(biggest_contours_finder(img_erode_rgb[x], 9))

        # extract the object position, angle and color
        if cnts_rgb[x] is not None:
            for cnt in cnts_rgb[x]:
                cx, cy = get_contour_barycenter(cnt)
                cx_rel, cy_rel = relative_pos_from_pixels(img_work, cx, cy)
                angle = get_contour_angle(cnt)
                a, obj_pose = client.get_target_pose_from_rel(workspace, height_offset=0.0, x_rel=cx_rel, y_rel=cy_rel, yaw_rel=angle)
                objects.append(Object(obj_pose, None, color_rgb[x], 0, cx_rel, cy_rel, cx, cy))

    for obj in objects:
        obj.obj_pos.z += global_z_offset

    # convert gray scale to BGR for debug display
    img_erode_red = cv2.cvtColor(img_erode_rgb[0], cv2.COLOR_GRAY2BGR, 0)
    img_erode_green = cv2.cvtColor(img_erode_rgb[1], cv2.COLOR_GRAY2BGR, 0)
    img_erode_blue = cv2.cvtColor(img_erode_rgb[2], cv2.COLOR_GRAY2BGR, 0)

    a, img = debug_markers(img)


    # resize all imgs
    img = resize_img(img, width=600, height=600)
    img_work = resize_img(img_work, width=300, height=300)
    img_erode_red = resize_img(img_erode_red, width=300, height=300)
    img_erode_green = resize_img(img_erode_green, width=300, height=300)
    img_erode_blue = resize_img(img_erode_blue, width=300, height=300)

    draw_debug(img_work)
    draw_debug(img_erode_red)
    draw_debug(img_erode_green)
    draw_debug(img_erode_blue)

    blanc = np.zeros((35, 300, 3), np.uint8)

    img_work = concat_imgs([img_work, blanc], 0)
    img_erode_red = concat_imgs([img_erode_red, blanc], 0)
    img_erode_green = concat_imgs([img_erode_green, blanc], 0)
    img_erode_blue = concat_imgs([img_erode_blue, blanc], 0)

    img_work = resize_img(img_work, height=300)
    img_erode_red = resize_img(img_erode_red, height=300)
    img_erode_green = resize_img(img_erode_green, height=300)
    img_erode_blue = resize_img(img_erode_blue, height=300)

    # label all images
    add_annotation_to_image(img, "  " * 40, write_on_top=False)
    add_annotation_to_image(img, " " * 22 + "Camera", write_on_top=False)
    add_annotation_to_image(img_work, "        Workspace         ", write_on_top=False)
    add_annotation_to_image(img_erode_red, "          Red             ", write_on_top=False)
    add_annotation_to_image(img_erode_green, "          Green           ", write_on_top=False)
    add_annotation_to_image(img_erode_blue, "          Blue            ", write_on_top=False)

    # concat all images
    img_l = concat_imgs([img_work, img_erode_red], 1)
    img_r = concat_imgs([img_erode_green, img_erode_blue], 1)

    img_res = concat_imgs([img_l, img_r], 0)
    img_res = concat_imgs([img, img_res], 1)

    show_img("robot view", img_res, wait_ms=100)

    return objects


# get an array of class Object and put it on a grid
def put_objects_on_grid(objects, grid_size):
    grid = []
    # build the grid
    for x in range(0, grid_size[0]):
        grid.append([])
    for x in range(0, grid_size[0]):
        for y in range(0, grid_size[1]):
            grid[x].append([])

    # put all objects in the grid
    for object in objects:
        y = object.cx_rel * grid_size[0]
        x = object.cy_rel * grid_size[1]
        grid[int(x)][int(y)].append(object)

    return grid


# display the grid in the term
def display_grid(grid):
    red, green, blue = " R ", " G ", " B "
    for l in grid:
        print("+" + "---+" * len(l) + "\n|", end="")
        for objs in l:
            if len(objs) > 0:
                if objs[0].color == Color.RED:
                    print(red, end="")
                if objs[0].color == Color.GREEN:
                    print(green, end="")
                if objs[0].color == Color.BLUE:
                    print(blue, end="")
            else:
                print("   ", end='')
            print("|", end='')
        print("")
    print("+" + "---+" * len(l))


def place_on_grid(grid, x, y, z=0):
    obj_pos = [0.0, 0.0, 0.0, 0.0, math.pi / 2, 0.0]
    a, pos_min = client.get_target_pose_from_rel(workspace, height_offset=0.0, x_rel=0, y_rel=0, yaw_rel=0)
    a, pos_max = client.get_target_pose_from_rel(workspace, height_offset=0.0, x_rel=1, y_rel=1, yaw_rel=0)
    size_x = (pos_max.x - pos_min.x) / len(grid)
    size_y = (pos_max.y - pos_min.y) / len(grid[0])

    obj_pos[0] = pos_min.x + size_x * (x + 0.5)
    obj_pos[1] = pos_min.y + size_y * (y + 0.5)
    obj_pos[2] = pos_min.z + z + global_z_offset

    client.place_from_pose(*obj_pos)


# take a shape and put it in a case
def pick_place_on_grid(grid, obj, x, y, z=0):
    print(obj, "=>", x, y)
    a, pos_min = client.get_target_pose_from_rel(workspace, height_offset=0.0, x_rel=0, y_rel=0, yaw_rel=0)
    a, pos_max = client.get_target_pose_from_rel(workspace, height_offset=0.0, x_rel=1, y_rel=1, yaw_rel=0)
    size_x = (pos_max.x - pos_min.x) / len(grid)
    size_y = (pos_max.y - pos_min.y) / len(grid[0])

    client.pick_from_pose(*obj.obj_pos.to_list())

    obj.obj_pos.x = pos_min.x + size_x * (x + 0.5)
    obj.obj_pos.y = pos_min.y + size_y * (y + 0.5)
    obj.obj_pos.z = pos_min.z + z + global_z_offset

    client.place_from_pose(*obj.obj_pos.to_list())


def move_in_grid(grid, x1, y1, x2, y2):
    pick_place_on_grid(grid, grid[x1][y1][0], x2, y2)
    grid[x2][y2].insert(grid[x1][y1].pop(0), 0)


def sort_score(obj):
    score = (obj.cx_rel + obj.cy_rel * 0.5)
    return score


# put blue pieces back in storage and put all other pieces out of the workspace
def init_game():
    objects = get_all_object()
    grid = put_objects_on_grid(objects, [4, 4])

    # sort from top left to bottom right
    objects.sort(key=sort_score)
    display_grid(grid)
    i, j, k, l = 0, 0, 0, 0
    while len(objects) > 0:
        obj = objects.pop(0)
        if obj.color == Color.BLUE and i <= len(grid[0]) and param["slope"] == 0:
            x, y, z = i, 0, 0
            i += 1
        elif obj.color == Color.GREEN and l == 0 and param["slope"] == 0:
            x, y, z = -0.7, -0.7, 0
            l = 1
        else:
            x, y, z = -0.7, 1.5, j
            j += 0.01
            k += 1
        pick_place_on_grid(grid, obj, x, y, z=z)


# count how many pieces are on the play grid
def count_plays(grid):
    tot = 0
    for x in range(0, 3):
        for y in range(0, 3):
            tot += abs(grid[x][y])
    return tot


# wait player turn
def wait_player():
    print("Player Turn")

    if param["turn_end"] == 1:
        # wait for button press
        client.move_joints(*sleep_joints)
        print("waiting button press...")
        client.set_learning_mode(True)
        while True:
            a, pin = client.digital_read(button_pin)
            if pin == 0:
                break
        client.set_learning_mode(False)
        return get_all_object()

    elif param["turn_end"] == 2:
        # wait for arm movement
        print("waiting for player to move the arm...")
        client.move_joints(*sleep_joints)
        client.set_learning_mode(True)
        time.sleep(3)
        a, joints_o = client.get_joints()
        while 1:
            a, joints = client.get_joints()
            for x in range(0, len(joints)):
                if abs(joints[x] - joints_o[x]) > 0.0872665:
                    time.sleep(1)
                    client.set_learning_mode(False)
                    return get_all_object()
                joints_o[x] = joints_o[x] * 0.9 + joints[x] * 0.1
            time.sleep(0.1)
    else:
        # wait for the green circle
        print("waiting green circle to be move...")
        go = 1
        while go:
            objects = get_all_object()
            grid = put_objects_on_grid(objects, [4, 4])
            x = 0
            for obj in objects:
                if obj.color == Color.GREEN:
                    pick_place_on_grid(grid, obj, -0.7, -0.7)
                    objects.pop(x)
                    go = 0
                    break
                x += 1
        return objects


# take a grid and check for winner
# return the value of the winner (-1 = human / 1 = AI)
def ai_win_check(grid):
    for l in grid:
        if l[0] == l[1] == l[2] != 0:
            return l[0]
    for x in range(0, 3):
        if grid[0][x] == grid[1][x] == grid[2][x] != 0:
            return grid[0][x]
    if grid[0][0] == grid[1][1] == grid[2][2] != 0:
        return grid[0][0]
    if grid[0][2] == grid[1][1] == grid[2][0] != 0:
        return grid[0][2]
    return 0


# recursive scan for the best play and return a score for each grid (1.0 = win, 1.0 = draw, -1.0 = lose)
def ai_recursive(grid, turn):
    win = ai_win_check(grid)
    if win != 0:
        return win
    score = [0, 0, 0]
    # lose, equal, win
    for x in range(0, 3):
        for y in range(0, 3):
            if grid[x][y] == 0:
                grid[x][y] = turn
                tmp = ai_recursive(grid, -turn)
                if tmp > 0:
                    score[turn + 1] += tmp
                elif tmp == 0:
                    score[1] += 1
                else:
                    score[-turn + 1] += -tmp
                grid[x][y] = 0
    if score[2] > 0:
        return turn * score[2] / 9
    elif score[1] > 0:
        return 0
    elif score[0] > 0:
        return -turn * score[0] / 9
    return 0


# compile view_grid in grid (0 empty space, 1 blue circle, -1 red circle)
def compile_grid(grid):
    game_grid = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    if param["slope"] == 1:
        grid = copy.deepcopy(grid)
        for x in range(0, 3):
            grid[x].insert(0, 0)

    for x in range(0, 3):
        for y in range(0, 3):
            if len(grid[x][y + 1]) > 0:
                if grid[x][y + 1][0].color == Color.BLUE:
                    game_grid[x][y] = 1
                elif grid[x][y + 1][0].color == Color.RED:
                    game_grid[x][y] = -1
    return game_grid


# in the work space: BLUE = AI, RED = human
def ai_play(view_grid, randomness):
    grid = compile_grid(view_grid)
    score_grid = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    for x in range(0, 3):
        for y in range(0, 3):
            score_grid[x][y] = random.randint(0, randomness * 100) / 100000.0
    # Fill the score grid
    for x in range(0, 3):
        for y in range(0, 3):
            if grid[x][y] == 0:
                grid[x][y] = 1
                score_grid[x][y] += ai_recursive(grid, -1)
                grid[x][y] = 0
            else:
                score_grid[x][y] = -9 ** 9 - 1
    # take the best score from the grid
    best_x, best_y = 0, 0
    best = -128
    for x in range(0, 3):
        for y in range(0, 3):
            if score_grid[x][y] > best:
                best = score_grid[x][y]
                best_x, best_y = x, y

    print("AI evaluation")
    for l in score_grid:
        print(l)
    print("AI pLay: " + str([best_x, best_y]))
    return [best_x, best_y, best]


def win_action():
    print("robot win")
    client.move_joints(*[0, 0, 0.6, 0, 0, 0])
    client.move_joints(*[0, 0.6, -0.5, 0, 0, 0])
    client.move_joints(*[0, 0, 0.6, 0, 0, 0])
    client.wait(1)


def lose_action():
    print("player win")
    client.move_joints(*[0, 0, 0, 0, 0, 0])
    client.move_joints(*[-2, 0, 0, 0, 0, 0])
    client.move_joints(*[-2, 0, -0.9, 0, -0.6, 0])
    client.wait(1)


def none_action():
    print("nobody win")
    client.move_joints(*[0, 0, 0, 0, 0, 0])
    client.move_joints(*[0, 0, 0, -1.570, 0, 0])
    client.move_joints(*[0, 0, 0, 1.570, 0, 0])
    client.move_joints(*[0, 0, 0, 0, 0, 0])


def cheat_action(x, y):
    client.move_pose(*cheat_pose.to_list())
    time.sleep(1)


def no_more_circles_action():
    print("no more circle in stock")


def cheat_detection(grid_view_1, grid_view_2):
    grid_1 = compile_grid(grid_view_1)
    grid_2 = compile_grid(grid_view_2)
    change = 0
    for x in range(0, 3):
        for y in range(0, 3):
            if grid_1[x][y] != 0 and grid_2[x][y] == 0:
                print("a circle has been removed", x, y)
                cheat_action(x, y)
            elif grid_1[x][y] != 0 and grid_2[x][y] != grid_1[x][y]:
                print("a circle has been replace", x, y)
                cheat_action(x, y)
            elif grid_1[x][y] == 0 and grid_2[x][y] == -1:
                change += 1
                if change > 1:
                    print("player has play multiple time")
                    cheat_action(x, y)


def robot_play(p, grid):
    if param["slope"] == 1:
        client.push_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)
        client.move_joints(*sleep_joints)
        client.move_joints(*slope_pos)
        client.pull_air_vacuum_pump(RobotTool.VACUUM_PUMP_1)
        client.move_joints(*sleep_joints)
        place_on_grid(grid, *p)
    else:
        obj = None
        while obj is None:
            for l in grid:
                if len(l[0]) > 0 and l[0][0].color == Color.BLUE:
                    obj = l[0][0]
                    break
            if obj is None:
                no_more_circles_action()
                objs = get_all_object()
                grid = put_objects_on_grid(objs, [4, 4])
        pick_place_on_grid(grid, obj, p[0], p[1] + 1)


def play_game():
    init_game()
    objs = get_all_object()
    grid = put_objects_on_grid(objs, grid_size)
    while True:  # loop for each turn
        grid_o = grid
        objects = wait_player()
        grid = put_objects_on_grid(objects, grid_size)
        display_grid(grid)
        cheat_detection(grid_o, grid)
        p = ai_play(grid, param["rand"])
        if ai_win_check(compile_grid(grid)) == -1:
            lose_action()
            return
        if count_plays(compile_grid(grid)) == 9:
            none_action()
            return

        robot_play(p[:2], grid)

        objs = get_all_object()
        grid = put_objects_on_grid(objs, grid_size)
        if ai_win_check(compile_grid(grid)) == 1:
            win_action()
            return
        if count_plays(compile_grid(grid)) == 9:
            none_action()
            return


mode = [
    [
        "\nLoop mode (automatically restart at the end of each game)?",
        "1: Off (default)",
        "2: On [--loop]"
    ], [
        "\nRobot turn mod (how you want the robot to know when to play)?",
        "1: Green circle [--green] ",
        "2: Button press [--button]",
        "3: Learning mode (default)"
    ], [
        "\nUse the slope?",
        "1: No  [--noslope]",
        "2: Yes (default)",
        "3: Reset slope position [--reset]"
    ]
]


def int_input(min, max):
    while True:
        try:
            a = int(input())
            if min <= a <= max:
                return a
        except:
            pass


# display menu and ask for user input
def menu():
    for l in mode[0]:
        print(l)
    param["loop"] = int_input(1, len(mode[0]) - 1) - 1
    for l in mode[1]:
        print(l)
    param["turn_end"] = int_input(1, len(mode[1]) - 1) - 1

    for l in mode[2]:
        print(l)
    param["slope"] = int_input(1, len(mode[2]) - 1) - 1
    if param["slope"] == 2:
        f = open("data.txt", "w")
        f.write("")
        f.close()
        param["slope"] = 1

    print("Randomness between 0 and 1000 (default: 5)")
    param["rand"] = int_input(0, 1000)
    return param


observation_pose_tumbs = PoseObject(  # =< position for the robot to watch the workspace
    x=0.25, y=0., z=0.4,
    roll=0.0, pitch=math.pi / 4, yaw=0.0,
)


def get_slope_pos():
    try:
        f = open("data.txt", "r")
        str1 = f.read()
        f.close()
        str1 = str1.split(" ")
        for x in range(1, 7):
            slope_pos.append(float(str1[x]))
        print("slope pos:" + str(slope_pos))
    except:
        client.set_learning_mode(True)
        print("the slope pickup position is undefined, put the robot arm on the picking position and press enter or use --noslope to play without it")
        input()
        a, joints = client.get_joints()
        time.sleep(1)
        client.move_joints(*sleep_joints)
        f = open("data.txt", "w")
        f.write("slope_pos:")
        for x in joints:
            f.write(" " + str(x))
        f.close()
        get_slope_pos()


if __name__ == '__main__':
    param = {
        "loop"      : 0,
        "turn_end"  : 2,
        "menu"      : 0,
        "rand"      : 5,
        "slope"     : 1
    }
    # param is a table containing all the parameters that the user can change
    # loop off/on, turn mode green/button/learning_mode, menu off/on, randomness, slope off/on
    try:
        client.calibrate(CalibrateMode.AUTO)
        client.change_tool(RobotTool.VACUUM_PUMP_1)
    except:
        print("calibration failed")

    for av in sys.argv[1:]:
        if av == "--loop" or av == "-l":
            param["loop"] = 1
        elif av == "--green" or av == "-g":
            param["turn_end"] = 0 #green shape
        elif av == "--button" or av == "-b":
            param["turn_end"] = 1 #button press
        elif av == "--menu" or av == "-m":
            param["menu"] = 1
        elif av == "--noslope" or av == "-s":
            param["slope"] = 0
        elif av == "--reset":
            f = open("data.txt", "w")
            f.write("")
            f.close()
        else:
            param["rand"] = max(min(int(av), 1000), 0)

    if param["menu"] == 1:
        param = menu()

    if param["slope"] == 1:
        get_slope_pos()
        grid_size[0] -= 1
        grid_size[1] -= 1

    print("#" * 10)
    for x in range(0, len(mode)):
        print(mode[x][0])
    print("\nRandomness at " + str(param["rand"]))
    print("#" * 10)
    param["rand"] /= 10

    if param["turn_end"] == 0:
        client.set_pin_mode(button_pin, PinMode.INPUT)

    try:
        while True:
            play_game()
            client.move_joints(*sleep_joints)
            if param["loop"] == 0:
                break
            time.sleep(3)
        client.set_learning_mode(True)
    except Exception as e:
        print(eeeee)
        client.move_joints(*sleep_joints)
        client.set_learning_mode(True)
