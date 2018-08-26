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
from logging import DEBUG
import os
import sys
import unittest

# Related third party imports

# Local application/library specific imports
from harvesters._private.core.helper.logging import get_logger
from harvesters.core import Harvester
from harvesters._private.core.helper.system import is_running_on_windows, \
    is_running_on_macos


class TestHarvesterCoreBase(unittest.TestCase):
    name = 'HARVESTER_TEST_TARGET'
    if name in os.environ:
        _cti_file = os.getenv(name)
    else:
        if is_running_on_windows():
            _cti_file = 'C:/Users/z1533tel/dev/genicam/bin/Win64_x64'
        else:
            if is_running_on_macos():
                _cti_file = '/Users/kznr/dev/genicam/bin/Maci64_x64'
            else:
                _cti_file = '/home/vagrant/dev/genicam/bin/Linux64_x64'

        _cti_file += '/TLSimu.cti'

    sys.path.append(_cti_file)

    def __init__(self, *args, **kwargs):
        #
        super().__init__(*args, **kwargs)

        #
        self._harvester = None
        self._iam = None
        self._thread = None
        self._logger = get_logger(name=__name__, level=DEBUG)

    def setUp(self):
        #
        super().setUp()

        #
        self._harvester = Harvester(logger=self._logger)
        self._harvester.add_cti_file(self._cti_file)
        self._harvester.update_device_info_list()

    def tearDown(self):
        #
        if self.iam:
            self.iam.destroy()

        #
        self._harvester.reset()

        #
        self._iam = None

        #
        super().tearDown()

    @property
    def harvester(self):
        return self._harvester

    @property
    def iam(self):
        return self._iam

    @iam.setter
    def iam(self, value):
        self._iam = value

    @property
    def general_purpose_thread(self):
        return self._thread

    @general_purpose_thread.setter
    def general_purpose_thread(self, value):
        self._thread = value

    def is_running_with_default_target(self):
        return True if 'TLSimu.cti' in self._cti_file else False


if __name__ == '__main__':
    unittest.main()
