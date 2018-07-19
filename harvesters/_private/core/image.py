#!/usr/bin/env python3
# ----------------------------------------------------------------------------
#
# Copyright 2018 EMVA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ----------------------------------------------------------------------------


# Standard library imports

# Related third party imports
from genicam2.gentl import InvalidParameterException
import numpy as np

# Local application/library specific imports
from harvesters._private.core.pfnc import symbolics

class Image:
    def __init__(self, parent=None, ndarray: np.ndarray=None):
        #
        super().__init__()

        #
        self._parent = parent
        self._ndarray = ndarray

    @property
    def width(self) -> int:
        try:
            width = self._parent.gentl_buffer.width
        except InvalidParameterException:
            width = self._parent.node_map.Width.value

        return width

    @property
    def height(self) -> int:
        try:
            height = self._parent.gentl_buffer.height
        except InvalidParameterException:
            height = self._parent.node_map.Height.value

        return height

    @property
    def pixel_format(self) -> str:
        try:
            pixel_format_int = self._parent.gentl_buffer.pixel_format
        except InvalidParameterException:
            return self._parent.node_map.PixelFormat.value
        else:
            return symbolics[int(pixel_format_int)]

    @property
    def ndarray(self) -> np.ndarray:
        return self._ndarray
