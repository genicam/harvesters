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
import numpy as np

# Local application/library specific imports
from core.image import Image


class Buffer:
    def __init__(self, gentl_buffer=None, node_map=None, raw_data: np.ndarray=None):
        #
        super().__init__()

        #
        self._gentl_buffer = gentl_buffer
        self._node_map = node_map
        self._image = Image(self, raw_data)

    @property
    def image(self) -> Image:
        return self._image

    @property
    def gentl_buffer(self):
        return self._gentl_buffer

    @property
    def node_map(self):
        return self._node_map
