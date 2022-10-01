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
import unittest

# Related third party imports
import genicam.genapi

from harvesters.core import Harvester, System, Interface, Device, RemoteDevice

# Local application/library specific imports
from harvesters.test.base_harvester import get_cti_file_path


class TestTicket345(unittest.TestCase):
    def setUp(self) -> None:
        self._cti_file_path = get_cti_file_path()
        if 'TLSimu.cti' not in self._cti_file_path:
            self.skipTest('The target is not TLSimu.')

        # Create a Harvester object:
        self.harvester = Harvester()
        self.harvester.add_file(self._cti_file_path)
        self.harvester.update()
        self.assertTrue(len(self.harvester.device_info_list) > 0)
        self.ia = self.harvester.create()

    def tearDown(self) -> None:
        if self.ia:
            self.ia.destroy()
        self.harvester.reset()

    def setup_camera(self):
        self.ia.remote_device.node_map.TriggerMode.value = 'On'
        self.ia.remote_device.node_map.TriggerSource.value = 'Software'

    def test_try_fetch_without_buffer_delivery(self):
        # GIVEN: a remote device that is external trigger-driven
        self.setup_camera()

        # WHEN: starting image acquisition
        self.ia.start()

        # THEN: it's running
        self.assertTrue(self.ia.is_acquiring())

        # AND WHEN: trying to fetch a buffer
        buffer = self.ia.try_fetch(timeout=1)

        # THEN: the buffer is None
        self.assertIsNone(buffer)

    def test_try_fetch_with_buffer_delivery(self):
        # GIVEN: a remote device that is self trigger-driven
        self.assertEqual(
            self.ia.remote_device.node_map.TriggerMode.value, 'Off')

        # WHEN: starting image acquisition
        self.ia.start()

        # THEN: it's running
        self.assertTrue(self.ia.is_acquiring())

        # AND WHEN: trying to fetch a buffer
        with self.ia.try_fetch(timeout=1) as buffer:
            # THEN: the buffer is not None
            self.assertIsNotNone(buffer)

    def test_try_fetch_no_timeout_parameter(self):
        # WHEN: starting image acquisition
        self.ia.start()

        # THEN: it's running
        self.assertTrue(self.ia.is_acquiring())

        # AND WHEN: trying to fetch a buffer
        # THEN: it raises an exception
        with self.assertRaises(TypeError):
            _ = self.ia.try_fetch()


if __name__ == '__main__':
    unittest.main()
