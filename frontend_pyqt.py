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
from PyQt5.QtCore import QMutexLocker, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QAction, QComboBox, \
    QDesktopWidget, QWidget, QVBoxLayout, QFileDialog, QDialog, QShortcut

# Local application/library specific imports
from about import About
from action import Action
from attribute_controller import AttributeController
from canvas import Canvas
from device_list import ComboBox
from frontend_helper import compose_tooltip
from icon import Icon
from system import get_system_font


class HarvesterGUI(QMainWindow):
    def __init__(self, harvester_core=None):
        #
        super().__init__()

        #
        self._harvester_core = harvester_core
        self._observer_widgets = []

        #
        self._widget_device_list = None
        self._widget_status_bar = None
        self._widget_main = None
        self._widget_about = None
        self._widget_attribute_controller = None
        self._widget_image_canvas = Canvas(
            harvester_core=harvester_core, mutex=self.harvester_core.mutex
        )

        #
        self._initialize_widgets()

        #
        for o in self._observer_widgets:
            o.update()

    @property
    def canvas(self):
        return self._widget_image_canvas

    @property
    def attribute_controller(self):
        return self._widget_attribute_controller

    @property
    def about(self):
        return self._widget_about

    @property
    def version(self):
        return self.harvester_core.version

    @property
    def device_list(self):
        return self._widget_device_list

    @property
    def cti_file_paths(self):
        return self.harvester_core.cti_file_paths

    @property
    def harvester_core(self):
        return self._harvester_core

    def _initialize_widgets(self):
        #
        self.setWindowTitle('Harvester')
        self.setFont(get_system_font())

        #
        self.statusBar().showMessage('')
        self.statusBar().setFont(get_system_font())

        #
        self._initialize_gui_toolbar(self._observer_widgets)

        #
        self._widget_main = FormWidget(self)
        self.setCentralWidget(self._widget_main)

        #
        self.resize(800, 600)

        # Place it in the center.
        rectangle = self.frameGeometry()
        coordinate = QDesktopWidget().availableGeometry().center()
        rectangle.moveCenter(coordinate)
        self.move(rectangle.topLeft())

    def _initialize_gui_toolbar(self, observers):
        #
        group_gentl_info = self.addToolBar('GenTL Information')
        group_connection = self.addToolBar('Connection')
        group_device = self.addToolBar('Image Acquisition')
        group_help = self.addToolBar('Help')

        #
        button_select_file = ActionSelectFile(self, Icon('open_file.png'),
            'Select file')
        shortcut_key = 'Ctrl+o'
        button_select_file.setToolTip(
            compose_tooltip('Open a CTI file to load', shortcut_key)
        )
        button_select_file.setShortcut(shortcut_key)
        button_select_file.toggle()
        observers.append(button_select_file)

        #
        button_update = ActionUpdateList(self, Icon('update.png'),
            'Update device list')
        shortcut_key = 'Ctrl+u'
        button_update.setToolTip(
            compose_tooltip('Update the device list', shortcut_key)
        )
        button_update.setShortcut(shortcut_key)
        button_update.toggle()
        observers.append(button_update)

        #
        button_connect = ActionConnect(self, Icon('connect.png'), 'Connect')
        shortcut_key = 'Ctrl+c'
        button_connect.setToolTip(
            compose_tooltip(
                'Connect the selected device to Harvester',
                shortcut_key
            )
        )
        button_connect.setShortcut(shortcut_key)
        button_connect.toggle()
        observers.append(button_connect)

        #
        button_disconnect = ActionDisconnect(self, Icon('disconnect.png'),
            'Disconnect')
        shortcut_key = 'Ctrl+d'
        button_disconnect.setToolTip(
            compose_tooltip(
                'Disconnect the device from Harvester',
                shortcut_key
            )
        )
        button_disconnect.setShortcut(shortcut_key)
        button_disconnect.toggle()
        observers.append(button_disconnect)

        #
        button_start_acquisition = ActionStartImageAcquisition(self,
            Icon('start_acquisition.png'), 'Start Acquisition')
        shortcut_key = 'Ctrl+j'
        button_start_acquisition.setToolTip(
            compose_tooltip('Start image acquisition', shortcut_key)
        )
        button_start_acquisition.setShortcut(shortcut_key)
        button_start_acquisition.toggle()
        observers.append(button_start_acquisition)

        #
        button_toggle_drawing = ActionToggleDrawing(self,
            Icon('pause.png'), 'Stop Drawing')
        shortcut_key = 'Ctrl+k'
        button_toggle_drawing.setToolTip(
            compose_tooltip('Stop drawing', shortcut_key)
        )
        button_toggle_drawing.setShortcut(shortcut_key)
        button_toggle_drawing.toggle()
        observers.append(button_toggle_drawing)

        #
        button_stop_acquisition = ActionStopImageAcquisition(self,
            Icon('stop_acquisition.png'), 'Stop Acquisition')
        shortcut_key = 'Ctrl+l'
        button_stop_acquisition.setToolTip(
            compose_tooltip('Stop image acquisition', shortcut_key)
        )
        button_stop_acquisition.setShortcut(shortcut_key)
        button_stop_acquisition.toggle()
        observers.append(button_stop_acquisition)

        #
        button_dev_attribute = ActionShowDevAttribute(self,
            Icon('device_attribute.png'), 'Device Attribute')
        shortcut_key = 'Ctrl+a'
        button_dev_attribute.setToolTip(
            compose_tooltip('Edit device attribute', shortcut_key)
        )
        button_dev_attribute.setShortcut(shortcut_key)
        button_dev_attribute.toggle()
        observers.append(button_dev_attribute)

        #
        self._widget_about = About(self)
        button_about = ActionShowAbout(self, Icon('about.png'), 'About')
        button_about.setToolTip(
            compose_tooltip('Show information about Harvester')
        )
        button_about.toggle()
        observers.append(button_about)

        #
        self._widget_device_list = ComboBox(self)
        self._widget_device_list.setSizeAdjustPolicy(
            QComboBox.AdjustToContents
        )
        shortcut_key = 'Ctrl+Shift+d'
        shortcut = QShortcut(QKeySequence(shortcut_key), self)

        def show_popup():
            self._widget_device_list.showPopup()

        shortcut.activated.connect(show_popup)
        self._widget_device_list.setToolTip(
            compose_tooltip('Select a device to connect', shortcut_key)
        )
        observers.append(self._widget_device_list)
        for d in self.harvester_core.device_info_list:
            self._widget_device_list.addItem(d)
        group_connection.addWidget(self._widget_device_list)
        observers.append(self._widget_device_list)

        #
        button_select_file.add_observer(button_update)
        button_select_file.add_observer(button_connect)
        button_select_file.add_observer(button_disconnect)
        button_select_file.add_observer(button_dev_attribute)
        button_select_file.add_observer(button_start_acquisition)
        button_select_file.add_observer(button_toggle_drawing)
        button_select_file.add_observer(button_stop_acquisition)
        button_select_file.add_observer(self._widget_device_list)

        #
        button_update.add_observer(self._widget_device_list)

        #
        button_connect.add_observer(button_select_file)
        button_connect.add_observer(button_update)
        button_connect.add_observer(button_disconnect)
        button_connect.add_observer(button_dev_attribute)
        button_connect.add_observer(button_start_acquisition)
        button_connect.add_observer(button_toggle_drawing)
        button_connect.add_observer(button_stop_acquisition)
        button_connect.add_observer(self._widget_device_list)

        #
        button_disconnect.add_observer(button_select_file)
        button_disconnect.add_observer(button_update)
        button_disconnect.add_observer(button_connect)
        button_disconnect.add_observer(button_dev_attribute)
        button_disconnect.add_observer(button_start_acquisition)
        button_disconnect.add_observer(button_toggle_drawing)
        button_disconnect.add_observer(button_stop_acquisition)
        button_disconnect.add_observer(self._widget_device_list)

        #
        button_start_acquisition.add_observer(button_toggle_drawing)
        button_start_acquisition.add_observer(button_stop_acquisition)

        #
        button_toggle_drawing.add_observer(button_start_acquisition)
        button_toggle_drawing.add_observer(button_stop_acquisition)

        #
        button_stop_acquisition.add_observer(button_start_acquisition)
        button_stop_acquisition.add_observer(button_toggle_drawing)

        #
        group_gentl_info.addAction(button_select_file)
        group_gentl_info.addAction(button_update)

        #
        group_connection.addAction(button_connect)
        group_connection.addAction(button_disconnect)

        #
        group_device.addAction(button_start_acquisition)
        group_device.addAction(button_toggle_drawing)
        group_device.addAction(button_stop_acquisition)
        group_device.addAction(button_dev_attribute)

        #
        group_help.addAction(button_about)

        group_gentl_info.actionTriggered[QAction].connect(
            self.on_button_clicked_action)
        group_connection.actionTriggered[QAction].connect(
            self.on_button_clicked_action)
        group_device.actionTriggered[QAction].connect(
            self.on_button_clicked_action)
        group_help.actionTriggered[QAction].connect(
            self.on_button_clicked_action
        )

    @staticmethod
    def on_button_clicked_action(action):
        action.execute()


class FormWidget(QWidget):
    def __init__(self, harvester_gui):
        #
        super(FormWidget, self).__init__(harvester_gui)

        #
        self._harvester_gui = harvester_gui

        #
        self._layout = QVBoxLayout()
        self._layout.addWidget(self._harvester_gui.canvas.native)

        #
        self.setLayout(self._layout)


class ActionSelectFile(Action):
    def __init__(self, harvester_gui, icon, title):
        #
        super().__init__(harvester_gui, icon, title)

    def _execute(self):
        # Show a dialog and update the CTI file list.
        dialog = QFileDialog(self.parent_widget)
        dialog.setWindowTitle('Select a CTI file to load')
        dialog.setNameFilter('CTI files (*.cti)')
        dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec_() == QDialog.Accepted:
            #
            file_path = dialog.selectedFiles()[0]

            #
            self.parent_widget.harvester_core.release_all_resources()

            # Update the path to the target GenTL Producer.
            self.parent_widget.harvester_core.add_file_path(file_path)
            print(file_path)

            # Update the device list.
            self.parent_widget.harvester_core.initialize_device_info_list()

    def update(self):
        enable = False
        if self.parent_widget.harvester_core.connecting_device is None:
            enable = True
        self.setEnabled(enable)


class ActionUpdateList(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        self.parent_widget.harvester_core.update_device_info_list()

    def update(self):
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device is None:
                enable = True
        self.setEnabled(enable)


class ActionConnect(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        # connect the selected device to Harvest.
        self.parent_widget.harvester_core.connect_device(
            self.parent_widget.device_list.currentIndex()
        )

        if self.parent_widget.harvester_core.node_map:
            self.parent_widget._widget_attribute_controller = \
                AttributeController(
                    self.parent_widget.harvester_core.node_map,
                    parent_widget=self.parent_widget
                )

    def update(self):
        #
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device is None:
                enable = True
        self.setEnabled(enable)


class ActionDisconnect(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        # Disconnect the device from Harvest.
        self.parent_widget.harvester_core.disconnect_device()

    def update(self):
        # Close attribute dialog if it's been opened.
        if self.parent_widget.attribute_controller:
            if self.parent_widget.attribute_controller.isVisible():
                self.parent_widget.attribute_controller.close()

        if self.parent_widget.harvester_core.connecting_device is None:
            self.parent_widget.harvester_core._feature_tree_model = None

        #
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device:
                enable = True
        self.setEnabled(enable)


class ActionStartImageAcquisition(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        self.parent_widget.harvester_core.start_image_acquisition()

    def update(self):
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device:
                if not self.parent_widget.harvester_core.is_acquiring_images or \
                    self.parent_widget.canvas.is_pausing:
                    enable = True
        self.setEnabled(enable)


class ActionToggleDrawing(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title, checkable=True)

    def _execute(self):
        self.parent_widget.canvas.toggle_drawing()

    def update(self):
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device:
                if self.parent_widget.harvester_core.is_acquiring_images:
                    enable = True
        self.setEnabled(enable)
        #
        checked = True if self.parent_widget.canvas.is_pausing else False
        self.setChecked(checked)


class ActionStopImageAcquisition(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        self.parent_widget.harvester_core.stop_image_acquisition()
        self.parent_widget.canvas.pause_drawing(False)

    def update(self):
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device:
                if self.parent_widget.harvester_core.is_acquiring_images:
                    enable = True
        self.setEnabled(enable)


class ActionShowDevAttribute(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

    def _execute(self):
        with QMutexLocker(self.parent_widget.harvester_core.mutex):
            if self.parent_widget.attribute_controller.isHidden():
                self.parent_widget.attribute_controller.show()
                self.parent_widget.attribute_controller.expand_all()

    def update(self):
        enable = False
        if self.parent_widget.cti_file_paths:
            if self.parent_widget.harvester_core.connecting_device is not None:
                enable = True
        self.setEnabled(enable)


class ActionShowAbout(Action):
    def __init__(self, parent_widget, icon, title):
        #
        super().__init__(parent_widget, icon, title)

        #
        self._dialog = parent_widget.about
        self._is_model = False

    def _execute(self):
        self._dialog.setModal(False)
        self._dialog.show()

    def update(self):
        pass


