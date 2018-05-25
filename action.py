# ----------------------------------------------------------------------------
#
# Copyright 2018, EMVA
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
from subject import Subject


class Action(QAction, Subject):
    def __init__(self, parent_widget, icon, title, checkable=False):
        #
        super().__init__(icon, title, parent_widget)

        #
        self._parent_widget = parent_widget
        self._dialog = None
        self._observers = []

        #
        self.setCheckable(checkable)

    @property
    def parent_widget(self):
        return self._parent_widget

    def execute(self):
        # Execute everything it's responsible for.
        self._execute()

        # Update itself.
        self.update()

        # Update its observers.
        self.update_observers()

    def _execute(self):
        raise NotImplementedError

    def setToolTip(self, tool_tip, shortcut_key=None):
        _tool_tip = tool_tip
        if shortcut_key:
            _tool_tip += ' (' + shortcut_key + ')'
        super().setToolTip(_tool_tip)
