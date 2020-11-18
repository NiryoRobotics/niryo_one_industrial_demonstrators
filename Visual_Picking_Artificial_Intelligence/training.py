#!/usr/bin/env python

import numpy as np
import cv2
import os
import random
import tensorflow as tf
from tensorflow.keras.layers import Dense, Flatten, Conv2D, Dropout, Input, MaxPool2D
import time
import utils

class MyModel:
    def __init__(self, input_shape, output_len):
        self.model = tf.keras.Sequential()
        # layers
        self.model.add(Input(shape=input_shape))
        self.model.add(Conv2D(32, kernel_size=5, activation='relu'))
        self.model.add(MaxPool2D(pool_size=(4, 4), padding='valid'))

        self.model.add(Dropout(0.1))
        self.model.add(Conv2D(32, kernel_size=5, activation='relu'))
        self.model.add(MaxPool2D(pool_size=(4, 4), padding='valid'))

        self.model.add(Flatten())
        self.model.add(Dropout(0.1))
        self.model.add(Dense(128, activation='relu'))
        self.model.add(Dense(output_len, activation='softmax'))

        #optimizer and compile
        optimizer = tf.keras.optimizers.Adam()
        self.model.compile(
            optimizer=optimizer,
            loss="binary_crossentropy",
            metrics=["accuracy"])


def load_dataset(data_path):

    #list all directories in data_path
    objects_names = os.listdir(data_path)
    print(objects_names)

    objects_list = [] #list containing all objects images
    labels_list = [] #list containing all objects Labels
    files_names = [] #list containing all objects names
    obj_id = 0

    #make the data_mask directorie
    try:
        os.mkdir("./data_mask")
    except:
        pass

    for name in objects_names:
        # list all image for each objects
        list_dir = os.listdir(data_path + name)

        print(name + " " + str(len(list_dir)))
        # make a "data_mask/<obj_name>" subdirectory for each object
        try:
            os.mkdir("./data_mask/" + name)
        except:
            pass

        #for each file in in "data/<obj_name>""
        for file_name in list_dir:
            # read the file
            img = cv2.imread(data_path + name + "/" + file_name)
            img = utils.standardize_img(img)
            # extract all objects from the image
            mask = utils.objs_mask(img)
            objs = utils.extract_objs(img, mask)

            #for each object in the image
            for x in range(0, len(objs)):
                img = objs[x].img

                #write the image in data_mask/<file_name>"
                cv2.imwrite("data_mask/" + name + "/" + str(x) + "_" + file_name, img)

                #resize the image to match our model input
                img = cv2.resize(img, (64, 64))

                #create a numpy  array of float with a size of (64, 64, 3)
                img_float = np.zeros((64, 64, 3), np.float32)

                #scale the image color between 0.0 and 1.0 and copy it in the numpy array
                img_float[:][:][:] = img[:][:][:] / 255.0

                #create a numpy array full of 0 with a shape of (len(objects_names))
                label = np.zeros((len(objects_names)), np.float32)

                #set is corresponding id to 1
                label[obj_id] = 1

                #insert all our numpy array in the data set

                objects_list.append(img_float)
                labels_list.append(label)
                files_names.append(str(x) + "_" + file_name)

            print(len(objs), end='')
            print("|", end="", flush=True)
        print("")
        obj_id += 1

    return [objects_list, labels_list, files_names, objects_names]

#this shuffle take an arra
def shuffle(*list_to_shuffle):
    # shuffle data
    c = list(zip(*list_to_shuffle))
    random.shuffle(c)
    list_to_shuffle = zip(*c)

    return list_to_shuffle


def test(model, objects_list, labels_list, objects_names, training_size, files_names):
    print("")
    print("")
    print("testing...", end="", flush=True)
    t = time.time()
    predictions = model.model.predict(objects_list)
    t = time.time() - t
    print("ok ", str(t)[2:5] + "ms for " + str(len(objects_list)) + " images")

    nb_error = 0
    nb_error_new = 0
    for x in range(len(objects_list)):
        x_max, y_max = predictions[x].argmax(), labels_list[x].argmax()
        if x == training_size:
            print("training data end")
        if x_max != y_max:
            if x > training_size:
                nb_error_new += 1
            else:
                nb_error += 1
            print("error", x, predictions[x], y_max, x_max, objects_names[y_max], objects_names[x_max], files_names[x])
            if __name__ == '__main__':
                cv2.imshow(objects_names[y_max] + " " + objects_names[x_max] + " " + files_names[x], objects_list[x])

    acc_tot = (len(objects_list) - nb_error) / len(objects_list)
    acc_test = (len(objects_list) - training_size - nb_error_new) / max(len(objects_list) - training_size, 1)
    print(acc_tot * 100, "%", "training data (sample size " + str(training_size)+")")
    print(acc_test * 100, "%", "new data (sample size " + str(len(objects_list)-training_size)+")")
    if (__name__ == "__main__"):
        cv2.waitKey(1000)
        input()
    return acc_tot, acc_test

def training():

    #set numpy precision to human friendly format
    np.set_printoptions(precision=3, suppress=True)


    *data_set, objects_names = load_dataset("data/")
    objects_list, labels_list, files_names = shuffle(*data_set)

    if len(objects_list) == 0:
        print("cannot train without a data set of 0")
        return None

    #transform the python array in numpy array ()
    objects_list = np.array(objects_list)
    labels_list = np.array(labels_list)

    # calculate the size of the training set
    training_size = int(len(objects_list) * 0.8)

    #split the training set and the test set
    object_train = objects_list[:training_size]
    labels_train = labels_list[:training_size]

    #print the total length of the data set
    print(len(objects_list))

    # create a model witch take 64px * 64px RGB image
    model = MyModel((64, 64, 3), len(objects_names))



    model.model.summary(line_length=None, positions=None, print_fn=None)

    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        featurewise_center=False,
        samplewise_center=False,
        featurewise_std_normalization=False,
        samplewise_std_normalization=False,
        zca_whitening=False,
        zca_epsilon=1e-06,
        rotation_range=5,
        width_shift_range=[-4, 4],
        height_shift_range=[-4, 4],
        brightness_range=None,
        shear_range=0.0,
        zoom_range=[0.95, 1.05],
        channel_shift_range=0.0,
        fill_mode="nearest",
        cval=0.0,
        horizontal_flip=0.5,
        vertical_flip=0.5,
        rescale=None,
        preprocessing_function=None,
        data_format=None,
        validation_split=0,
        dtype=None,
    )

    #train the model
    history = model.model.fit(
        datagen.flow(object_train, labels_train, batch_size=32), steps_per_epoch=int(len(object_train)/32),
        epochs=25
    )

    print("saving...", end="", flush=True)
    model.model.save("model")
    print("ok")

    test(model, objects_list, labels_list, objects_names, training_size, files_names)
    return model.model

#cela permet de ne pas lancer le programme en ca de include / import
if __name__ == '__main__':
    training()
