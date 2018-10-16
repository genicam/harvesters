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


class ThreadImageAcquisitionStatistics(Thread):
    def __init__(self, *, worker=None, timeout_s=0):
        #
        super().__init__()

        #
        self._worker = worker
        self._is_running = False
        self._timeout_s = timeout_s
        self._time_base = 0

    def run(self):
        self._is_running = True
        self._time_base = time.time()
        while self._is_running:
            #
            if self._worker:
                self._worker()
                time.sleep(0.25)

            #
            diff_s = time.time() - self._time_base
            if diff_s > self._timeout_s:
                self._is_running = False


class TestTutorials(TestHarvesterCoreBase):

    def test_performance_on_image_acquisition(self):
        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        # Then start image acquisition.
        self.ia.start_image_acquisition()

        # Run the image acquisition thread:
        thread = ThreadImageAcquisitionStatistics(
            worker=self._worker_update_statistics, timeout_s=10
        )
        thread.start()
        thread.join()

        # Stop image acquisition:
        self.ia.stop_image_acquisition()

    def _worker_update_statistics(self):
        #
        if self.ia:
            message_config = 'W: {0} x H: {1}, {2}, '.format(
                self.ia.device.node_map.Width.value,
                self.ia.device.node_map.Height.value,
                self.ia.device.node_map.PixelFormat.value
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
                '{0}'.format(message_config + message_statistics)
            )


if __name__ == '__main__':
    unittest.main()
