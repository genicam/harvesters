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

# Related third party imports

# Local application/library specific imports


class Processor:
    def __init__(self, description):
        #
        super().__init__()

        #
        self._description = description
        self._processors = []

    @property
    def description(self):
        return self._description

    def process(self, input_buffer):
        output_buffer = None

        for p in self._processors:
            output_buffer = p.process(input_buffer)
            input_buffer = output_buffer

        return output_buffer

