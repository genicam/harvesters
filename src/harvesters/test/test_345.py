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
        self.ia = None

    def tearDown(self) -> None:
        if self.ia:
            self.ia.destroy()
        self.harvester.reset()

    def test_system(self):
        # GIVEN: an image acquirer
        self.ia = self.harvester.create()

        # AND GIVEN: its system entity
        entity = self.ia.system
        self.assertIsNotNone(entity)
        self.assertTrue(type(entity) is System)

        # WHEN: probing its node map
        # THEN: returns a node map object
        # AND THEN: the node map is valid
        node_map = entity.node_map
        self.assertTrue(type(node_map) is genicam.genapi.NodeMap)

    def test_interface(self):
        # GIVEN: an image acquirer
        self.ia = self.harvester.create()

        # AND GIVEN: its interface entity
        entity = self.ia.interface
        self.assertIsNotNone(entity)
        self.assertTrue(type(entity) is Interface)

        # WHEN: probing its node map
        # THEN: returns a node map object
        # AND THEN: the node map is valid
        node_map = entity.node_map
        self.assertTrue(type(node_map) is genicam.genapi.NodeMap)

    def test_device(self):
        # GIVEN: an image acquirer
        self.ia = self.harvester.create()

        # AND GIVEN: its remote device entity
        entity = self.ia.device
        self.assertIsNotNone(entity)
        self.assertTrue(type(entity) is Device)

        # WHEN: probing its node map
        # THEN: returns a node map object
        # AND THEN: the node map is valid
        node_map = entity.node_map
        self.assertTrue(type(node_map) is genicam.genapi.NodeMap)

    def test_remote_device(self):
        # GIVEN: an image acquirer
        self.ia = self.harvester.create()

        # AND GIVEN: its remote device entity
        entity = self.ia.remote_device
        self.assertIsNotNone(entity)
        self.assertTrue(type(entity) is RemoteDevice)

        # WHEN: probing its node map
        # THEN: returns a node map object
        # AND THEN: the node map is valid
        node_map = entity.node_map
        self.assertTrue(type(node_map) is genicam.genapi.NodeMap)


if __name__ == '__main__':
    unittest.main()
