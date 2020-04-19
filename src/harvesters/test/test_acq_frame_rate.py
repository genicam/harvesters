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
from harvesters.test.base_harvester import TestHarvesterCoreBase


class ThreadWithTimeLimit(Thread):
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


class TestTutorials(TestHarvesterCoreBase):

    def _test_performance_on_image_acquisition(self, sleep_duration=0.0):
        #
        self._logger.info(
            'Sleep duration: {0} s'.format(sleep_duration)
        )

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(
            0, sleep_duration=sleep_duration
        )

        # Then start image acquisition.
        self.ia.start_acquisition(run_in_background=True)

        # Run the image acquisition thread:
        thread = ThreadWithTimeLimit(
            worker=self._worker_update_statistics, timeout=5
        )
        thread.start()
        thread.join()

        # Stop image acquisition:
        self.ia.stop_acquisition()

        # Destroy the image acquirer:
        self.ia.destroy()

    def _worker_update_statistics(self, id_: int):
        #
        if self.ia:
            message_config = 'W: {0} x H: {1}, {2}, '.format(
                self.ia.remote_device.node_map.Width.value,
                self.ia.remote_device.node_map.Height.value,
                self.ia.remote_device.node_map.PixelFormat.value
            )

            message_statistics = '{0:.1f} fps, elapsed {1}, {2} images'.format(
                self.ia.statistics.fps,
                str(datetime.timedelta(
                    seconds=int(self.ia.statistics.elapsed_time_s)
                )),
                self.ia.statistics.num_images
            )

            #
            self._logger.info(
                '{0:08x}: {1}'.format(
                    id_, message_config + message_statistics
                )
            )

    def test_performance_on_image_acquisition_with_sleep_duration(self):
        # Connect to the first camera in the list.
        sleep_duration = 0.001
        for i in range(4):
            self._test_performance_on_image_acquisition(
                sleep_duration=sleep_duration
            )
            sleep_duration *= 0.1

    def test_performance_on_image_acquisition_with_zero_sleep_duration(self):
        self._test_performance_on_image_acquisition(
            sleep_duration=0.0
        )

    def test_multiple_access(self):
        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        #
        self.ia.start_acquisition(run_in_background=True)

        #
        nr = 100

        # Run the image acquisition thread:
        threads = []
        for i in range(nr):
            threads.append(
                ThreadWithTimeLimit(
                    worker=self._worker_update_statistics,
                    timeout=10, sleep=0
                )
            )

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        #
        self.ia.stop_acquisition()

        # Destroy the image acquirer:
        self.ia.destroy()


if __name__ == '__main__':
    unittest.main()
