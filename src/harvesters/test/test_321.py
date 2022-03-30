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
from harvesters.core import ParameterSet, ParameterKey

# Local application/library specific imports


class TestDeviceInfo(unittest.TestCase):
    key = ParameterKey.NUM_BUFFERS_FOR_FETCH_CALL
    default = None

    def test(self):
        tests = [
            self._test_case_1,
            self._test_case_2,
            self._test_case_3,
            self._test_case_4,
        ]
        for _test in tests:
            for value_w in [None, 3, "a"]:
                _test(value_w=value_w)

    def _test_case_1(self, value_w):
        # GIVEN: a parameter set that explicitly sets the parameter
        config = ParameterSet({self.key: value_w})
        # WHEN: inquiring the parameter
        value_r = ParameterSet.get(self.key, self.default, config)
        # THEN: the set value is returned
        self.assertEqual(value_w, value_r)

    def _test_case_2(self, value_w):
        # GIVEN: a parameter set that does not define the parameter
        config = ParameterSet()
        # WHEN: inquiring the parameter
        value_r = ParameterSet.get(self.key, self.default, config)
        # THEN: the default value is returned
        self.assertEqual(self.default, value_r)

    def _test_case_3(self, value_w):
        # GIVEN: none instead of a parameter set
        config = None
        # WHEN: inquiring the parameter
        value_r = ParameterSet.get(self.key, self.default, config)
        # THEN: the default value is returned
        self.assertEqual(self.default, value_r)

    def _test_case_4(self, value_w):
        # GIVEN: none instead of a parameter set
        config = None
        # WHEN: inquiring the parameter
        value_r = ParameterSet.get(self.key, self.default, config)
        # THEN: the default value is returned
        self.assertEqual(self.default, value_r)


if __name__ == '__main__':
    unittest.main()
