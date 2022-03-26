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
from harvesters.test.base_harvester import TestHarvester


class TestDeprecatedItems(TestHarvester):
    def test_create_image_acquirer(self):
        self._logger.info("you will see deprecation warning.")
        self.ia = self.harvester.create_image_acquirer(0)
        self._logger.info("did you see that?")


if __name__ == '__main__':
    unittest.main()
