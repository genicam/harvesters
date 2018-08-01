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


class ProcessorBase:
    def __init__(self, description):
        """

        :param description: Set description about this process.
        """
        #
        super().__init__()

        #
        self._description = description
        self._processors = []

    @property
    def description(self):
        """

        :return: A description about this process.

        """
        return self._description

    def process(self, input):
        """

        :param input: Set an arbitrary object. It will be treated as the input
        source of the sequence of processes.

        :return: An arbitrary object as the output of the sequence of processes.
        """
        output = None

        for p in self._processors:
            output = p.process(input)
            input = output

        return output

