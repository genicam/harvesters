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
from PyQt5.QtWidgets import QAction

# Local application/library specific imports
from harvesters._private.core.subject import Subject


class Action(QAction, Subject):
    def __init__(self, icon, title, parent=None, checkable=False):
        #
        super().__init__(icon, title, parent)

        #
        self._dialog = None
        self._observers = []

        #
        self.setCheckable(checkable)

    def execute(self):
        # Execute everything it's responsible for.
        self._execute()

        # Update itself.
        self.update()

        # Update its observers.
        self.update_observers()

    def _execute(self):
        raise NotImplementedError
