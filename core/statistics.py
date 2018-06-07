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

# Local application/library specific imports


class Statistics:
    def __init__(self):
        #
        super().__init__()

        #
        self._timestamp_base = 0
        self._has_acquired_1st_timestamp = False
        self._fps = 0.
        self._num_images = 0
        self._fps_max = 0.

    def set_timestamp(self, timestamp, frequency):
        # TODO: Harvester is temporarily expecting to have ns timestamps.
        if not self._has_acquired_1st_timestamp:
            self._timestamp_base = timestamp
            self._has_acquired_1st_timestamp = True
        else:
            diff = timestamp - self._timestamp_base
            if diff > 0:
                fps = self._num_images * frequency / diff
                if fps > self._fps_max:
                    self._fps_max = fps
                self._fps = fps
            else:
                self._fps = 0.

    def reset(self):
        self._timestamp_base = 0
        self._has_acquired_1st_timestamp = False
        self._fps = 0.
        self._num_images = 0
        self._fps_max = 0.

    def increment_num_images(self, num=1):
        if self._has_acquired_1st_timestamp:
            self._num_images += num

    @property
    def fps(self):
        return self._fps

    @property
    def fps_max(self):
        return self._fps_max

    @property
    def num_images(self):
        return self._num_images

