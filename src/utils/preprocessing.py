#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Jan 29, 2021

@file: preprocessing.py
@desc: All function related to the data preprocessing step of the pipeline.
@author: laugh12321
@contact: laugh12321@vip.qq.com
"""
import functools
import numpy as np
from typing import Tuple, Union, List

from src.utils.utils import shuffle_arrays_together, get_label_indices_per_class

HEIGHT = 0
WIDTH = 1
DEPTH = 2


def reshape_cube_to_1d_samples(data: np.ndarray,
                               labels: np.ndarray,
                               channels_idx: int = 0) -> \
        Tuple[np.ndarray, np.ndarray]:
    """
    Reshape the data and labels from [CHANNELS, HEIGHT, WIDTH] to
        [PIXEL,CHANNELS, 1], so it fits the 2D Convolutional modules.

    :param data: Data to reshape.
    :param labels: Corresponding labels.
    :param channels_idx: Index at which the channels are located in the
                         provided data file.
    :return: Reshape data and labels
    :rtype: tuple with reshaped data and labels
    """
    data = np.rollaxis(data, channels_idx, len(data.shape))
    height, width, channels = data.shape
    data = data.reshape(height * width, channels)
    labels = labels.reshape(height * width, -1)
    data = data.astype(np.float32)
    labels = labels.astype(np.float32)

    return data, labels


def remove_nan_samples(data: np.ndarray, labels: np.ndarray) -> Tuple[
    np.ndarray, np.ndarray]:
    """
    Remove samples which contain only nan values

    :param data: Data with dimensions [SAMPLES, ...]
    :param labels: Corresponding labels
    :return: Data and labels with removed samples containing nans
    """
    all_but_samples_axes = tuple(range(1, data.ndim))
    nan_samples_indexes = np.isnan(data).any(axis=all_but_samples_axes).ravel()
    labels = labels[~nan_samples_indexes]
    data = data[~nan_samples_indexes]
    return data, labels


def train_val_test_split(data: np.ndarray, labels: np.ndarray,
                         train_size: Union[List, float, int] = 0.8,
                         val_size: float = 0.1,
                         seed: int = 0) -> Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split the data into train, val and test sets. The size of the training set
    is set by the train_size parameter. All the remaining samples will be
    treated as a test set

    :param data: Data with the [SAMPLES, ...] dimensions
    :param labels: Vector with corresponding labels
    :param train_size:  If float, should be between 0.0 and 1.0,
        If stratified = True, it represents percentage of each class to be extracted.
        If float and stratified = False, it represents percentage of the whole datasets to be extracted with samples drawn randomly, regardless of their class.
        If int and stratified = True, it represents number of samples to be drawn from each class.
        If int and stratified = False, it represents overall number of samples to be drawn regardless of their class, randomly.
        Defaults to 0.8
    :param val_size: Should be between 0.0 and 1.0. Represents the percentage
                     of each class from the training set to be extracted as a
                     validation set, defaults to 0.1
    :param seed: Seed used for data shuffling
    :return: train_x, train_y, val_x, val_y, test_x, test_y
    :raises AssertionError: When wrong type is passed as train_size
    """
    shuffle_arrays_together([data, labels], seed=seed)
    train_indices = _get_set_indices(train_size, labels)
    val_indices = _get_set_indices(val_size, labels[train_indices])
    val_indices = train_indices[val_indices]
    test_indices = np.setdiff1d(np.arange(len(data)), train_indices)
    train_indices = np.setdiff1d(train_indices, val_indices)
    return data[train_indices], labels[train_indices], data[val_indices], \
           labels[val_indices], data[test_indices], labels[test_indices]


@functools.singledispatch
def _get_set_indices(size: Union[List, float, int],
                     labels: np.ndarray) -> np.ndarray:
    """
    Extract indices of a subset of specified data according to size and
    stratified parameters.

    :param labels: Vector with corresponding labels
    :param size: If float, should be between 0.0 and 1.0,
                    if stratified = True, it represents percentage
                    of each class to be extracted.
                 If float and stratified = False, it represents
                    percentage of the whole datasets to be extracted
                    with samples drawn randomly, regardless of their class.
                 If int and stratified = True, it represents number of samples
                    to be drawn from each class.
                 If int and stratified = False, it represents overall number of
                    samples to be drawn regardless of their class, randomly.
                 Defaults to 0.8
    :return: Indexes of the train set
    :raises TypeError: When wrong type is passed as size
    """
    raise NotImplementedError()


@_get_set_indices.register(float)
def _(size: float, labels: np.ndarray) -> np.ndarray:
    if not 0 < size <= 1:
        raise AssertionError
    train_indices = np.arange(int(len(labels) * size))

    return train_indices


@_get_set_indices.register(int)
def _(size: int, labels: np.ndarray) -> np.ndarray:
    if size < 1:
        raise AssertionError
    train_indices = np.arange(size, dtype=int)

    return train_indices


@_get_set_indices.register(list)
def _(size: List,
      labels: np.ndarray,
      _) -> np.ndarray:
    label_indices, unique_labels = get_label_indices_per_class(
        labels, return_uniques=True)
    if len(size) == 1:
        size = int(size[0])
    for n_samples, label in zip(size, range(len(unique_labels))):
        label_indices[label] = label_indices[label][:int(n_samples)]
    train_indices = np.concatenate(label_indices, axis=0)
    return train_indices
