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
import unittest

# Related third party imports

# Local application/library specific imports
from core.harvester import Harvester
from core.helper.system import is_running_on_windows


class TestHarvesterCore(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_harvester_core(self):
        #
        from time import sleep

        #
        with Harvester() as harvester:
            path = 'C:/Users/z1533tel/dev/genicam/bin/Win64_x64/TLSimu.cti' \
                if is_running_on_windows() else \
                '/Users/kznr/dev/genicam/bin/Win64_x64/TLSimu.cti'
            harvester.add_cti_file(path)
            harvester.update_device_info_list()
            harvester.connect_device(0)
            for i in range(5):
                print('---> going to start image acquisition.')
                harvester.start_image_acquisition()
                j = 0
                frames = 10.
                while j < int(frames):
                    # Emulate a refresh cycle.
                    sleep(1. / frames)

                    if j % 2 == 0:
                        # Option 1: This way is secure and preferred.
                        try:
                            # We know we've started image acquisition but this
                            # try-except block is demonstrating a case where
                            # a client called fetch_buffer method even though
                            # he'd forgotten to start image acquisition.
                            with harvester.fetch_buffer() as buffer:
                                self.print_buffer(buffer)
                        except AttributeError:
                            # Harvester Core has not started image acquisition so
                            # calling fetch_buffer() raises AttributeError because
                            # None object is used for the with statement.
                            pass
                    else:
                        # Option 2: You can manually do the same job but not
                        # recommended because you might forget to queue the
                        # buffer.
                        buffer = harvester.fetch_buffer()
                        self.print_buffer(buffer)
                        harvester.queue_buffer(buffer)

                    #
                    j += 1
                harvester.stop_image_acquisition()
                print('<--- have just stopped image acquisition.')

    @staticmethod
    def print_buffer(buffer):
        print('W: {0} x H: {1}, {2}, {3}'.format(
            buffer.image.width,
            buffer.image.height,
            buffer.image.pixel_format,
            buffer.image.ndarray
        ))


if __name__ == '__main__':
    unittest.main()
