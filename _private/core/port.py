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
from genicam2.genapi import AbstractPort
from genicam2.genapi import EAccessMode
from genicam2.gentl import Port

# Local application/library specific imports


class ConcretePort(AbstractPort):
    """
    An object-oriented version of PortImpl class.

    """
    def __init__(self, port_object=None):
        #
        super().__init__()

        #
        if isinstance(port_object, Port):
            self._port = port_object
        else:
            raise TypeError('Supplied object is not a Port object.')

    @property
    def port(self):
        return self._port

    def is_open(self):
        return False if self.port is None else True

    def write(self, address, value):
        self.port.write(address, value)

    def read(self, address, length):
        buffer = self.port.read(address, length)
        return buffer[1]

    def open(self, port_object):
        self._port = port_object

    def close(self):
        self._port = None

    def get_access_mode(self):
        return EAccessMode.RW if self.is_open else EAccessMode.NA
