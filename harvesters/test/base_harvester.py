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
import sys
import unittest

# Related third party imports

# Local application/library specific imports
from harvesters.core import Harvester
from harvesters._private.core.helper.system import is_running_on_windows


class TestHarvesterCoreBase(unittest.TestCase):
    _path = 'C:/Users/z1533tel/dev/genicam/bin/Win64_x64/' \
        if is_running_on_windows() else \
        '/Users/kznr/dev/genicam/bin/Maci64_x64/'

    _filename = 'TLSimu.cti'

    sys.path.append(_path)

    def __init__(self, *args, **kwargs):
        #
        super().__init__(*args, **kwargs)

    def setUp(self):
        #
        super().setUp()

        #
        self._harvester = Harvester()
        self._harvester.add_cti_file(self._path + self._filename)
        self._harvester.update_device_info_list()
        self._harvester.connect_device(0)

    def tearDown(self):
        #
        self._harvester.reset()

        #
        super().tearDown()


if __name__ == '__main__':
    unittest.main()
