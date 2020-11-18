from niryo_one_tcp_client import *
from niryo_one_camera import *
import numpy as np
import cv2
import time

# take an image of the workspace
def take_workspace_img(client):
    a, mtx, dist = client.get_calibration_object()
    while 1:
        a, img_compressed = client.get_img_compressed()
        img_raw = uncompress_image(img_compressed)
        img = undistort_image(img_raw, mtx, dist)
        img_work = extract_img_workspace(img, workspace_ratio=1)
        if img_work is not None:
            break
        print("take_workspace_img failed")
        return False, img
    return True, img_work


def threshold_hls(img, list_min_hsv, list_max_hsv):
    frame_hsl = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
    return cv2.inRange(frame_hsl, tuple(list_min_hsv), tuple(list_max_hsv))


# fill holes in a mask
def fill_holes(img):
    im_floodfill = img.copy()
    h, w = img.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
    img = img | im_floodfill_inv
    return (img)


# calculate a mask
def objs_mask(img):
    color_hls = [[0, 0, 0], [360, 210, 255]]

    mask = threshold_hls(img, *color_hls)

    kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel11 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))

    # erode workspace markers
    mask[:15, :] = cv2.erode(mask[:15, :], kernel7, iterations=5)
    mask[-15:, :] = cv2.erode(mask[-15:, :], kernel7, iterations=5)
    mask[:, :15] = cv2.erode(mask[:, :15], kernel7, iterations=5)
    mask[:, -15:] = cv2.erode(mask[:, -15:], kernel7, iterations=5)

    mask = fill_holes(mask)

    mask = cv2.dilate(mask, kernel3, iterations=1)
    mask = cv2.erode(mask, kernel5, iterations=1)
    mask = cv2.dilate(mask, kernel11, iterations=1)

    mask = fill_holes(mask)

    mask = cv2.erode(mask, kernel7, iterations=1)

    return mask


# rotate a numpy img
def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
    return result


class CameraObject(object):
    def __init__(self, img, x=None, y=None, angle=None, cnt=None, box=None, square=None):
        self.img = img
        self.angle = angle
        self.x = x
        self.y = y
        self.cnt = cnt
        self.box = box
        self.square = square
        self.type = None


# take an img and a mask / return an array of CameraObject
def extract_objs(img, mask):
    cnts, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    objs = []

    initial_shape = img.shape

    #surround the image with Black pixels
    blank = np.zeros(img.shape, np.uint8)
    img = concat_imgs([blank, img, blank], 0)
    blank = np.zeros(img.shape, np.uint8)
    img = concat_imgs([blank, img, blank], 1)

    #for all the contour in the image, copy the corresponding object
    if cnts is not None:
        for cnt in cnts:
            cx, cy = get_contour_barycenter(cnt)

            try:
                angle = get_contour_angle(cnt)
            except:
                angle = 0

            #get the minimal Area Rectangle around the contour
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            up = int(box[0][1])
            down = int(box[2][1])
            left = int(box[1][0])
            right = int(box[3][0])

            size_x = right - left
            size_y = up - down

            #verify that our objects is not just a point or a line
            if size_x <= 0 or size_y <= 0:
                continue

            #transform our rectangle into a square
            if size_x > size_y:
                down -= int((size_x - size_y) / 2)
                size = size_x
            else:
                left -= int((size_y - size_x) / 2)
                size = size_y

            #if the square is to small, skip it
            if size < 64:
                continue

            square = [[down, left], [left + size, down + size]]

            #copy the pixels of our rectangle in a new image
            down += initial_shape[0]
            left += initial_shape[1]
            img_cut = np.zeros((size, size, 3), np.uint8)
            img_cut[:, :] = img[down: down + size, left: left + size]

            #rotate the image so the object is in a vertical orientation
            img_cut = rotate_image(img_cut, angle * 180 / math.pi)

            #append the data and the image of our object
            objs.append(CameraObject(img_cut, cx, cy, angle, cnt, box, square))
    return objs


def standardize_img(img):
    array_type = img.dtype

    # color balance normalizing
    color_mean = np.mean(img, axis=(0, 1))
    mean_color_mean = np.mean(color_mean)
    img = img[:][:]*mean_color_mean/color_mean

    # color range normalizing
    min, max = np.quantile(img, [0.001, 0.95])
    img = (img - min) * 256 / (max - min)
    img = np.clip(img, 0, 255)
    img = img.astype(array_type)
    return img
