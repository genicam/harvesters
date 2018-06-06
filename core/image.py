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


class Image:
    def __init__(self, parent=None, ndarray: np.ndarray=None):
        #
        super().__init__()

        #
        self._parent = parent
        self._ndarray = ndarray

    @property
    def width(self) -> int:
        return self._parent.gentl_buffer.width

    @property
    def height(self) -> int:
        return self._parent.gentl_buffer.height

    @property
    def pixel_format(self) -> str:
        pixel_format = self._parent.node_map.PixelFormat.get_entry(
            self._parent.gentl_buffer.pixel_format
        )
        return pixel_format.symbolic

    @property
    def ndarray(self) -> np.ndarray:
        return self._ndarray

