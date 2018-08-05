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
from harvesters._private.frontend.pyqt5.icon import Icon


class Action(QAction, Subject):
    def __init__(
            self, icon=None, title=None, parent=None, checkable=False,
            action=None, is_enabled=None
    ):
        #
        super().__init__(Icon(icon), title, parent)

        #
        self._dialog = None
        self._observers = []
        self._action = action
        self._is_enabled = is_enabled

        #
        self.setCheckable(checkable)

    def execute(self):
        # Execute everything it's responsible for.
        if self._action:
            self._action()

        # Update itself.
        self.update()

        # Update its observers.
        self.update_observers()

    def update(self):
        if self._is_enabled:
            self.setEnabled(self._is_enabled())
        self._update()

    def _update(self):
        pass

