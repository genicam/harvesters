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


class TestTutorials(TestHarvesterCoreBase):

    def test_severis_usage(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.iam = self.harvester.create_image_acquisition_manager(0)

        #
        num_images_to_acquire = 0

        # Setup the camera before starting image acquisition.
        self.setup_camera()

        # Then start image acquisition.
        self.iam.start_image_acquisition()

        # Setup your equipment then trigger the camera.
        self.setup_equipment_and_trigger_camera()

        while num_images_to_acquire < 100:
            #
            with self.iam.fetch_buffer() as buffer:
                # I know we should use a logger instead of the print
                # function though...
                self._logger.info('{0}'.format(buffer))

                # TODO: Work with the image you got.
                # self.do_something(buffer)

                # Set up your equipment for the next image acquisition.
                self.setup_equipment_and_trigger_camera()

            num_images_to_acquire += 1

    def setup_camera(self):
        self.iam.device.node_map.AcquisitionMode.value = 'Continuous'
        self.iam.device.node_map.TriggerMode.value = 'On'
        self.iam.device.node_map.TriggerSource.value = 'Software'

    def setup_equipment_and_trigger_camera(self):
        # Setup your equipment.
        # TODO: Code here.

        # Trigger the camera because you have already setup your
        # equipment for the upcoming image acquisition.
        self.iam.device.node_map.TriggerSoftware.execute()


if __name__ == '__main__':
    unittest.main()
