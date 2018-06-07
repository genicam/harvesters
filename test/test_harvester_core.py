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
from time import sleep
import unittest

# Related third party imports

# Local application/library specific imports
from core.harvester import Harvester
from core.system import is_running_on_windows


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
                harvester.start_image_acquisition()
                j = 0
                frames = 10.
                while j < int(frames):
                    sleep(1. / frames)
                    image = harvester.get_image()
                    print(image)
                    j += 1
                harvester.stop_image_acquisition()


if __name__ == '__main__':
    unittest.main()
