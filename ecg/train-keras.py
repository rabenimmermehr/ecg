from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()

import argparse
import numpy as np
import json
import os
import time

from loader import Loader
from keras_models import model

NUMBER_EPOCHS = 1000
VERBOSE_LEVEL = 1


def get_folder_name(start_time, net_type):
    folder_name = FOLDER_TO_SAVE + net_type + '/' + start_time
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name


def get_filename_for_saving(start_time, net_type):
    saved_filename = get_folder_name(start_time, net_type) + \
        "/{val_loss:.3f}-{val_acc:.3f}-{epoch:002d}-{loss:.3f}-{acc:.3f}.hdf5"
    return saved_filename


def plot_model(model, start_time, net_type):
    from keras.utils.visualize_util import plot
    plot(
        model,
        to_file=get_folder_name(start_time, net_type) + '/model.png',
        show_shapes=True,
        show_layer_names=False)


def save_params(params, start_time, net_type):
    saving_filename = get_folder_name(start_time, net_type) + "/params.json"
    save_str = json.dumps(params, ensure_ascii=False)
    save_str = save_str if isinstance(save_str, str) else save_str.decode('utf-8')
    with open(saving_filename, 'w') as outfile:
        outfile.write(save_str)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("data_path", help="path to data files")
    parser.add_argument("config_file", help="path to confile file")
    parser.add_argument("--refresh", help="whether to refresh cache", action="store_true")
    args = parser.parse_args()

    dl = Loader(
        args.data_path,
        use_one_hot_labels=True,
        seed=2016,
        use_cached_if_available=not args.refresh)

    x_train = dl.x_train[:, :, np.newaxis]
    y_train = dl.y_train
    print("Training size: " + str(len(x_train)) + " examples.")

    x_val = dl.x_test[:, :, np.newaxis]
    y_val = dl.y_test
    print("Validation size: " + str(len(x_val)) + " examples.")

    start_time = str(int(time.time()))

    params = json.load(open(args.config_file, 'r'))
    FOLDER_TO_SAVE = params["FOLDER_TO_SAVE"]

    net_type = params["net_type"]
    save_params(params, start_time, net_type)

    params.update({
        "input_shape": x_train[0].shape,
        "num_categories": dl.output_dim
    })

    network = model.build_network(**params)

    try:
        plot_model(network, start_time, net_type)
    except:
        print("Skipping plot")

    from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping

    stopping = EarlyStopping(
        monitor='val_loss',
        patience=10,
        verbose=VERBOSE_LEVEL) 

    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=0.0001,
        verbose=VERBOSE_LEVEL)

    checkpointer = ModelCheckpoint(
        filepath=get_filename_for_saving(start_time, net_type),
        save_best_only=True,
        verbose=VERBOSE_LEVEL)

    network.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        nb_epoch=NUMBER_EPOCHS,
        callbacks=[checkpointer, reduce_lr, stopping],
        verbose=VERBOSE_LEVEL)