"""
Author: Arash Fatehi
Date:   10.12.2022
"""

# Python Imports
import os

# Library Imports
import torch
import numpy as np
import tifffile

# Local Imports
from src.data.ds_base import BaseDataset, DatasetType


class InferenceDataset(BaseDataset):
    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 _file_path,
                 _sample_dimension,
                 _pixel_per_step,
                 _channel_map,
                 _scale_factor):

        super().__init__(_sample_dimension,
                         _pixel_per_step,
                         _channel_map,
                         _scale_factor,
                         _dataset_type=DatasetType.Inference,
                         _ignore_stride_mismatch=False,
                         _label_correction_function=None)

        self.file_path = _file_path
        self.file_name = os.path.basename(_file_path)
        with tifffile.TiffFile(self.file_path) as tiff:
            self.image = tiff.asarray()
            self.tiff_tags = self.get_tiff_tags(tiff)

        self.image_shape = self.image.shape
        self.image = np.array(self.image)
        self.image = self.image.astype(np.float32)

        if self.scale_factor > 1:
            self.image = self.scale(self.image)

        self.check_image_shape_compatibility(self.image_shape,
                                             self.file_name)

        self.nephrin = self.image[:, self.channel_map[0], :, :]
        self.wga = self.image[:, self.channel_map[1], :, :]
        self.collagen4 = self.image[:, self.channel_map[2], :, :]

        sample_per_z = int((self.image_shape[0] - self.sample_dimension[0]) //
                           self.pixel_per_step_z) + 1
        sample_per_x = int((self.image_shape[2] - self.sample_dimension[1]) //
                           self.pixel_per_step_x) + 1
        sample_per_y = int((self.image_shape[3] - self.sample_dimension[2]) //
                           self.pixel_per_step_y) + 1

        self.no_of_samples = sample_per_z * sample_per_x * sample_per_y

    def __len__(self):
        return self.no_of_samples

    def __getitem__(self, index):

        channel_shape = self.nephrin.shape
        sample_per_x = int((channel_shape[1] - self.sample_dimension[1]) //
                           self.pixel_per_step_x) + 1
        sample_per_y = int((channel_shape[2] - self.sample_dimension[2]) //
                           self.pixel_per_step_y) + 1

        _n = index
        z_start = _n // (sample_per_x * sample_per_y)
        _n = _n % (sample_per_x * sample_per_y)

        y_start = _n // sample_per_x

        x_start = _n % sample_per_x

        z_start = z_start * self.pixel_per_step_z
        x_start = x_start * self.pixel_per_step_x
        y_start = y_start * self.pixel_per_step_y

        nephrin = self.nephrin[z_start: z_start + self.sample_dimension[0],
                               x_start: x_start + self.sample_dimension[1],
                               y_start: y_start + self.sample_dimension[2]]

        wga = self.wga[z_start: z_start + self.sample_dimension[0],
                       x_start: x_start + self.sample_dimension[1],
                       y_start: y_start + self.sample_dimension[2]]

        collagen4 = self.collagen4[z_start: z_start + self.sample_dimension[0],
                                   x_start: x_start + self.sample_dimension[1],
                                   y_start: y_start + self.sample_dimension[2]]

        nephrin = np.expand_dims(nephrin, axis=0)
        wga = np.expand_dims(wga, axis=0)
        collagen4 = np.expand_dims(collagen4, axis=0)

        nephrin = nephrin/255
        wga = wga/255
        collagen4 = collagen4/255

        return {
            'nephrin': torch.from_numpy(nephrin),
            'wga': torch.from_numpy(wga),
            'collagen4': torch.from_numpy(collagen4),
            'offsets': torch.from_numpy(
                np.array([index,
                          x_start,
                          y_start,
                          z_start])
            ).int()
        }
