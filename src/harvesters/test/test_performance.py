#!/usr/bin/env python3
# ----------------------------------------------------------------------------
#
# Copyright 2022 EMVA
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
import logging
from threading import Thread
import time
from typing import Callable
import unittest

# Related third party imports
from harvesters.core import ImageAcquirer

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvester


class TimerThread(Thread):
    def __init__(self, period: float, notify: Callable[[], None]):
        super().__init__()
        self._period = period
        self._notify = notify

    def run(self) -> None:
        time.sleep(self._period)
        self._notify()


class AcquisitionThread(Thread):
    def __init__(self, acquire: ImageAcquirer, update: Callable[[int], None]):
        super().__init__()
        self._acquire = acquire
        self._is_running = True
        self._nr = 0
        self._update = update

    def run(self):
        while self._is_running:
            with self._acquire.fetch():
                self._nr += 1
                time.sleep(0)
        self._update(self._nr)

    def notify(self):
        self._is_running = False


class Counter:
    def __init__(self):
        super().__init__()
        self._count = 0

    def update(self, count: int):
        self._count = count

    @property
    def count(self):
        return self._count


class TestPerformance(TestHarvester):
    def test_number_of_frames(self):
        self._logger.info("GIVEN: an image acquirer")
        counter = Counter()
        ia = self.harvester.create()
        if self.is_running_with('viky.cti'):
            ia.remote_device.node_map.AcquisitionFrameRate.value = 200
        acquisition_thread = AcquisitionThread(ia, counter.update)
        period = 10.0
        self._logger.info("AND GIVEN: {} sec. as a period".format(period))
        timer_thread = TimerThread(period, notify=acquisition_thread.notify)
        self._logger.info("WHEN: starting image acquisition for {} sec.".format(period))
        ia.start()
        timer_thread.start()
        acquisition_thread.start()
        timer_thread.join()
        acquisition_thread.join()
        ia.stop()
        self._logger.info("THEN: {} images were acquired in {} sec.".format(counter.count, period))


if __name__ == '__main__':
    unittest.main()
