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
from harvesters.test.base_harvester import TestHarvesterCoreBase


class TestHarvesterCore(TestHarvesterCoreBase):
    @staticmethod
    def print_buffer(buffer):
        print('W: {0} x H: {1}, {2}\n{3}'.format(
            buffer.image.width,
            buffer.image.height,
            buffer.image.pixel_format,
            buffer.image.ndarray
        ))

    def test_harvester_core(self):
        #
        for i in range(10):
            print('---> {0}: started'.format(i))
            self._harvester.start_image_acquisition()
            j = 0
            # Run it as fast as possible.
            frames = 10
            while j < frames:
                if j % 2 == 0:
                    # Option 1: This way is secure and preferred.
                    try:
                        # We know we've started image acquisition but this
                        # try-except block is demonstrating a case where
                        # a client called fetch_buffer method even though
                        # he'd forgotten to start image acquisition.
                        with self._harvester.fetch_buffer() as buffer:
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
                    buffer = self._harvester.fetch_buffer()
                    self.print_buffer(buffer)
                    self._harvester.queue_buffer(buffer)

                #
                j += 1
            self._harvester.stop_image_acquisition()
            print('    <--- {0}: stopped'.format(i))


if __name__ == '__main__':
    unittest.main()
