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
from PyQt5.QtWidgets import QComboBox
from gentl import NotImplementedException

# Local application/library specific imports
from observer import Observer
from system import get_system_font


class ComboBox(QComboBox, Observer):
    def __init__(self, parent_widget):
        super().__init__()
        self._parent_widget = parent_widget
        self.setFont(get_system_font())

    @property
    def parent_widget(self):
        return self._parent_widget

    def update(self):
        if self.parent_widget.harvester_core.has_revised_list:
            self.clear()
            separator = '::'
            for d in self.parent_widget.harvester_core.device_info_list:
                name = d.parent.parent.vendor  # i.e., system.vendor
                name += separator
                name += d.vendor
                name += separator
                name += d.model
                if d.serial_number:
                    name += separator
                    name += d.serial_number
                try:
                    _ = d.user_defined_name
                except NotImplementedException as e:
                    print(e)
                else:
                    if d.user_defined_name != '':
                        name += separator
                        name += d.user_defined_name
                self.addItem(name)
        #
        self.parent_widget.harvester_core.has_revised_list = False

        #
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device is None:
                enable = True
        self.setEnabled(enable)
