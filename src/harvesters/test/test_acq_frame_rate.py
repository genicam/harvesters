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
import datetime
from threading import Thread
import time
import unittest

# Related third party imports

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvester
from harvesters.test.base_harvester import BaseVersion


class ImageAcquisitionThread(Thread):
    def __init__(self, *, acquirer, timeout=0):
        super().__init__()
        self._is_running = False
        self._timeout_s = timeout
        self._time_base = 0
        self._ia = acquirer
        self._nr_images = 0

    @property
    def nr_images(self):
        return self._nr_images

    def run(self):
        self._is_running = True
        self._time_base = time.time()
        while self._is_running:
            #
            with self._ia.fetch():
                self._nr_images += 1
            #
            diff_s = time.time() - self._time_base
            if diff_s > self._timeout_s:
                self._is_running = False


class StatisticsMonitorThread(Thread):
    def __init__(self, *, worker=None, timeout=0, sleep=0.25):
        """

        :param worker:
        :param timeout: Set timeout value in second.
        """
        #
        super().__init__()

        #
        self._worker = worker
        self._is_running = False
        self._timeout_s = timeout
        self._time_base = 0
        self._sleep = sleep

    def run(self):
        self._is_running = True
        self._time_base = time.time()
        while self._is_running:
            #
            if self._worker:
                self._worker(id_=self.ident)
                time.sleep(self._sleep)
            #
            diff_s = time.time() - self._time_base
            if diff_s > self._timeout_s:
                self._is_running = False


class TestTutorials(TestHarvester):

    def test_performance_on_single_threaded_image_acquisition(self):
        self.ia = self.harvester.create(0)
        self.ia.start()
        timeout = 3
        thread = ImageAcquisitionThread(acquirer=self._ia, timeout=timeout)
        thread.start()
        thread.join()
        self._test_logger.info(
            "acquired: {} in {} ({:.2f} fps)".format(
                thread.nr_images, timeout, thread.nr_images / timeout
            )
        )
        self.ia.stop()

    def _test_performance_on_image_acquisition(self, sleep_duration=0.0):
        #
        self._test_logger.info("sleep duration: {0} s".format(sleep_duration))

        # Connect to the first camera in the list.
        self.ia = self.harvester.create(0)

        # Then start image acquisition.
        self.ia.start(run_as_thread=True)

        # Run the image acquisition thread:
        thread = StatisticsMonitorThread(
            worker=self._worker_update_statistics, timeout=3
        )
        thread.start()
        thread.join()

        # Stop image acquisition:
        self.ia.stop()

        # Destroy the image acquirer:
        self.ia.destroy()

    def _worker_update_statistics(self, id_: int):
        #
        if self.ia:
            message = (
                f"W: {self.ia.remote_device.node_map.Width.value} "
                f"x H: {self.ia.remote_device.node_map.Height.value}, "
                f"{self.ia.remote_device.node_map.PixelFormat.value}, "
            )

            if self.ia.statistics.elapsed_time_s == 0.0:
                return

            message += (
                f"{self.ia.statistics.num_images / self.ia.statistics.elapsed_time_s:.1f} fps, "
                f"elapsed {str(datetime.timedelta(seconds=int(self.ia.statistics.elapsed_time_s)))}, "
                f"{self.ia.statistics.num_images} images"
            )

            #
            self._test_logger.debug(f"{id_:08x}: {message}")

    def test_performance_on_image_acquisition_with_zero_sleep_duration(self):
        self._test_performance_on_image_acquisition(sleep_duration=0.0)

    def test_multiple_access(self):
        # Connect to the first camera in the list.
        self.ia = self.harvester.create(0)

        #
        self.ia.start(run_as_thread=True)

        #
        nr = 3

        # Run the image acquisition thread:
        threads = []
        for i in range(nr):
            threads.append(
                StatisticsMonitorThread(
                    worker=self._worker_update_statistics, timeout=3, sleep=0
                )
            )

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        #
        self.ia.stop()

        # Destroy the image acquirer:
        self.ia.destroy()


class ThreadWithTimeLimitVersion1(StatisticsMonitorThread):
    base_version = BaseVersion.VERSION_1


class TestTutorialsVersion1(TestTutorials):
    base_version = BaseVersion.VERSION_1


if __name__ == "__main__":
    unittest.main()
