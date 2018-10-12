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
import time

# Related third party imports
from genicam2.gentl import InvalidParameterException, \
    NotImplementedException, NotAvailableException, InvalidHandleException
from genicam2.genapi import LogicalErrorException

# Local application/library specific imports


class Statistics:
    def __init__(self):
        #
        super().__init__()

        #
        self._time_base = time.time()
        self._time_elapsed = 0
        self._timestamp_base = 0
        self._has_acquired_1st_timestamp = False
        self._fps = 0.
        self._num_images = 0
        self._fps_max = 0.

    def update_timestamp(self, buffer):
        freq = self._get_timestamp_freq(buffer)
        if freq is not None:
            if not self._has_acquired_1st_timestamp:
                self._timestamp_base = self._get_timestamp(buffer)
                self._has_acquired_1st_timestamp = True
            else:
                # Calculate the instant frame rate from the gap between
                # the one before the latest and the latest:
                now = self._get_timestamp(buffer)
                diff = now - self._timestamp_base
                self._timestamp_base = now
                if diff > 0:
                    fps = freq / diff
                    if fps > self._fps_max:
                        self._fps_max = fps
                    self._fps = fps
        else:
            if self._time_elapsed > 0:
                self._fps = self._num_images / self._time_elapsed

    @staticmethod
    def _get_timestamp(buffer):
        try:
            timestamp = buffer.timestamp_ns
        except (InvalidParameterException, NotImplementedException,
                NotAvailableException):
            try:
                timestamp = buffer.timestamp
            except (InvalidParameterException, NotAvailableException):
                timestamp = 0

        return timestamp

    @staticmethod
    def _get_timestamp_freq(buffer):
        #
        try:
            _ = buffer.timestamp_ns
        except (InvalidParameterException, NotImplementedException,
                NotAvailableException, InvalidHandleException):
            try:
                frequency = buffer.parent.parent.timestamp_frequency
            except (InvalidParameterException, NotImplementedException,
                    NotAvailableException):
                return None
        else:
            frequency = 1000000000  # Hz

        return frequency

    def reset(self):
        self._time_base = time.time()
        self._timestamp_base = 0
        self._has_acquired_1st_timestamp = False
        self._fps = 0.
        self._num_images = 0
        self._fps_max = 0.

    def increment_num_images(self, num=1):
        self._time_elapsed = time.time() - self._time_base
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

    @property
    def elapsed_time_s(self):
        return self._time_elapsed

