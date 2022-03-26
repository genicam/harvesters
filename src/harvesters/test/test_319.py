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
from harvesters.core import Harvester, DeviceInfo

# Local application/library specific imports
from harvesters.test.base_harvester import get_cti_file_path


class TestDeviceInfo(unittest.TestCase):
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

    def test_listing_up_device_info_list_0_0(self):
        print(DeviceInfo.search_keys)

    def test_listing_up_device_info_list_0_1(self):
        print(self.harvester.device_info_list)

    def test_listing_up_device_info_list_0_2(self):
        for entry in self.harvester.device_info_list:
            print(entry)

    def test_listing_up_device_info_list_1(self):
        for i in range(len(self.harvester.device_info_list)):
            ia = self.harvester.create(search_key=i)
            self.assertIsNotNone(ia)
            ia.destroy()

    def test_listing_up_device_info_list_1_no_keyword(self):
        for i in range(len(self.harvester.device_info_list)):
            ia = self.harvester.create(i)
            self.assertIsNotNone(ia)
            ia.destroy()

    def test_listing_up_device_info_list_2(self):
        for i in range(len(self.harvester.device_info_list)):
            ia = self.harvester.create(
                search_key=self.harvester.device_info_list[i])
            self.assertIsNotNone(ia)
            ia.destroy()

    def test_listing_up_device_info_list_2_no_keyword(self):
        for i in range(len(self.harvester.device_info_list)):
            ia = self.harvester.create(
                self.harvester.device_info_list[i])
            self.assertIsNotNone(ia)
            ia.destroy()

    def test_listing_up_device_info_list_3(self):
        self.ia = self.harvester.create(
            search_key={'serial_number': 'SN_InterfaceA_0'})
        self.assertIsNotNone(self.ia)

    def test_listing_up_device_info_list_3_no_keyword(self):
        self.ia = self.harvester.create(
            {'serial_number': 'SN_InterfaceA_0'})
        self.assertIsNotNone(self.ia)

    def test_listing_up_device_info_list_4(self):
        self.ia = self.harvester.create(
            search_key={'display_name': 'TLSimuMono (SN_InterfaceA_0)'})
        self.assertIsNotNone(self.ia)

    def test_listing_up_device_info_list_4_no_keyword(self):
        self.ia = self.harvester.create(
            {'display_name': 'TLSimuMono (SN_InterfaceA_0)'})
        self.assertIsNotNone(self.ia)

    def test_listing_up_device_info_list_5(self):
        with self.assertRaises(ValueError):
            self.ia = self.harvester.create(search_key={'model': 'TLSimuMono'})

    def test_listing_up_device_info_list_5_no_keyword(self):
        with self.assertRaises(ValueError):
            self.ia = self.harvester.create({'model': 'TLSimuMono'})

    def test_listing_up_device_info_list_6(self):
        self.ia = self.harvester.create(
            search_key={'model': 'TLSimuMono',
                        'serial_number': 'SN_InterfaceA_0'})
        self.assertIsNotNone(self.ia)

    def test_listing_up_device_info_list_6_no_keyword(self):
        self.ia = self.harvester.create(
            {'model': 'TLSimuMono', 'serial_number': 'SN_InterfaceA_0'})
        self.assertIsNotNone(self.ia)

    def test_listing_up_device_info_list_7(self):
        for i in range(len(self.harvester.device_info_list)):
            ia = self.harvester.create(search_key=None)
            self.assertIsNotNone(ia)
            ia.destroy()

    def test_listing_up_device_info_list_7_no_keyword(self):
        for i in range(len(self.harvester.device_info_list)):
            ia = self.harvester.create()
            self.assertIsNotNone(ia)
            ia.destroy()


if __name__ == '__main__':
    unittest.main()
