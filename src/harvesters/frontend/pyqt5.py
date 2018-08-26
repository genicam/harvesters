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
from logging import DEBUG
import os
import sys

# Related third party imports
from PyQt5.QtCore import QMutexLocker, QMutex, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QAction, QComboBox, \
    QDesktopWidget, QFileDialog, QDialog, QShortcut, QApplication

# Local application/library specific imports
from harvesters._private.frontend.canvas import Canvas
from harvesters._private.core.helper.logging import get_logger
from harvesters._private.frontend.helper import compose_tooltip
from harvesters._private.frontend.pyqt5.about import About
from harvesters._private.frontend.pyqt5.action import Action
from harvesters._private.frontend.pyqt5.attribute_controller import AttributeController
from harvesters._private.frontend.pyqt5.device_list import ComboBox
from harvesters._private.frontend.pyqt5.helper import get_system_font
from harvesters._private.frontend.pyqt5.icon import Icon
from harvesters._private.frontend.pyqt5.thread import PyQtThread
from harvesters.core import Harvester as HarvesterCore


class Harvester(QMainWindow):
    #
    _signal_update_statistics = pyqtSignal(str)
    _signal_stop_image_acquisition = pyqtSignal()

    def __init__(self, *, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        #
        self._mutex = QMutex()

        profile = True if 'HARVESTER_PROFILE' in os.environ else False
        self._harvester_core = HarvesterCore(
            profile=profile, logger=self._logger
        )
        self._iam = None  # Image Acquisition Manager

        self._widget_canvas = Canvas()
        self._widget_canvas.set_shaders()  # Pass custom shares if needed.
        self._widget_canvas.create_native()
        self._widget_canvas.native.setParent(self)

        #
        self._action_stop_image_acquisition = None

        #
        self._observer_widgets = []

        #
        self._widget_device_list = None
        self._widget_status_bar = None
        self._widget_main = None
        self._widget_about = None
        self._widget_attribute_controller = None

        #
        self._signal_update_statistics.connect(self.update_statistics)
        self._signal_stop_image_acquisition.connect(self._stop_image_acquisition)

        #
        self._initialize_widgets()

        #
        for o in self._observer_widgets:
            o.update()

        self._is_going_to_terminate = False

    def _stop_image_acquisition(self):
        self.action_stop_image_acquisition.execute()

    def update_statistics(self, message):
        self.statusBar().showMessage(message)

    def closeEvent(self, QCloseEvent):
        self._is_going_to_terminate = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._harvester_core.reset()

    @property
    def canvas(self):
        return self._widget_canvas

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
    def cti_files(self):
        return self.harvester_core.cti_files

    @property
    def harvester_core(self):
        return self._harvester_core

    @property
    def mutex(self):
        return self._mutex

    def _initialize_widgets(self):
        #
        self.setWindowIcon(Icon('genicam_logo_i.png'))

        #
        self.setWindowTitle('GenICam.Harvester')
        self.setFont(get_system_font())

        #
        self.statusBar().showMessage('')
        self.statusBar().setFont(get_system_font())

        #
        self._initialize_gui_toolbar(self._observer_widgets)

        #
        self.setCentralWidget(self.canvas.native)

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
        button_select_file = ActionSelectFile(
            icon='open_file.png', title='Select file', parent=self,
            action=self.action_on_select_file,
            is_enabled=self.is_enabled_on_select_file
        )
        shortcut_key = 'Ctrl+o'
        button_select_file.setToolTip(
            compose_tooltip('Open a CTI file to load', shortcut_key)
        )
        button_select_file.setShortcut(shortcut_key)
        button_select_file.toggle()
        observers.append(button_select_file)

        #
        button_update = ActionUpdateList(
            icon='update.png', title='Update device list', parent=self,
            action=self.action_on_update_list,
            is_enabled=self.is_enabled_on_update_list
        )
        shortcut_key = 'Ctrl+u'
        button_update.setToolTip(
            compose_tooltip('Update the device list', shortcut_key)
        )
        button_update.setShortcut(shortcut_key)
        button_update.toggle()
        observers.append(button_update)

        #
        button_connect = ActionConnect(
            icon='connect.png', title='Connect', parent=self,
            action=self.action_on_connect,
            is_enabled=self.is_enabled_on_connect
        )
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
        button_disconnect = ActionDisconnect(
            icon='disconnect.png', title='Disconnect', parent=self,
            action=self.action_on_disconnect,
            is_enabled=self.is_enabled_on_disconnect
        )
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
        button_start_acquisition = ActionStartImageAcquisition(
            icon='start_acquisition.png', title='Start Acquisition', parent=self,
            action=self.action_on_start_image_acquisition,
            is_enabled=self.is_enabled_on_start_image_acquisition
        )
        shortcut_key = 'Ctrl+j'
        button_start_acquisition.setToolTip(
            compose_tooltip('Start image acquisition', shortcut_key)
        )
        button_start_acquisition.setShortcut(shortcut_key)
        button_start_acquisition.toggle()
        observers.append(button_start_acquisition)

        #
        button_toggle_drawing = ActionToggleDrawing(
            icon='pause.png', title='Pause/Resume Drawing', parent=self,
            action=self.action_on_toggle_drawing,
            is_enabled=self.is_enabled_on_toggle_drawing
        )
        shortcut_key = 'Ctrl+k'
        button_toggle_drawing.setToolTip(
            compose_tooltip('Pause/Resume drawing', shortcut_key)
        )
        button_toggle_drawing.setShortcut(shortcut_key)
        button_toggle_drawing.toggle()
        observers.append(button_toggle_drawing)

        #
        button_stop_acquisition = ActionStopImageAcquisition(
            icon='stop_acquisition.png', title='Stop Acquisition', parent=self,
            action=self.action_on_stop_image_acquisition,
            is_enabled=self.is_enabled_on_stop_image_acquisition
        )
        shortcut_key = 'Ctrl+l'
        button_stop_acquisition.setToolTip(
            compose_tooltip('Stop image acquisition', shortcut_key)
        )
        button_stop_acquisition.setShortcut(shortcut_key)
        button_stop_acquisition.toggle()
        observers.append(button_stop_acquisition)
        self._action_stop_image_acquisition = button_stop_acquisition

        #
        button_dev_attribute = ActionShowAttributeController(
            icon='device_attribute.png', title='Device Attribute', parent=self,
            action=self.action_on_show_attribute_controller,
            is_enabled=self.is_enabled_on_show_attribute_controller
        )
        shortcut_key = 'Ctrl+a'
        button_dev_attribute.setToolTip(
            compose_tooltip('Edit device attribute', shortcut_key)
        )
        button_dev_attribute.setShortcut(shortcut_key)
        button_dev_attribute.toggle()
        observers.append(button_dev_attribute)

        #
        self._widget_about = About(self)
        button_about = ActionShowAbout(
            icon='about.png', title='About', parent=self,
            action=self.action_on_show_about
        )
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
        button_update.add_observer(button_connect)

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
            self.on_button_clicked_action
        )
        group_connection.actionTriggered[QAction].connect(
            self.on_button_clicked_action
        )
        group_device.actionTriggered[QAction].connect(
            self.on_button_clicked_action
        )
        group_help.actionTriggered[QAction].connect(
            self.on_button_clicked_action
        )

    @staticmethod
    def on_button_clicked_action(action):
        action.execute()

    @property
    def action_stop_image_acquisition(self):
        return self._action_stop_image_acquisition

    @property
    def iam(self):
        return self._iam

    @iam.setter
    def iam(self, value):
        self._iam = value

    def action_on_connect(self):
        #
        self._iam = self.harvester_core.create_image_acquisition_manager(
            self.device_list.currentIndex()
        )

        if not self._iam:
            # The device is not available.
            return

        #
        self.iam.thread_image_acquisition = PyQtThread(
            parent=self, mutex=self.mutex
        )
        self.iam.thread_statistics_measurement = PyQtThread(
            parent=self, mutex=self.mutex
        )

        self.iam.updated_statistics = self._signal_update_statistics
        self.iam.signal_stop_image_acquisition = self._signal_stop_image_acquisition

        try:
            if self.iam.device.node_map:
                self._widget_attribute_controller = \
                    AttributeController(
                        self.iam.device.node_map,
                        parent=self
                    )
        except AttributeError:
            pass

        #
        self.canvas.iam = self.iam

    def is_enabled_on_connect(self):
        enable = False
        if self.cti_files:
            if self.harvester_core.device_info_list:
                if self.iam is None:
                    enable = True
        return enable

    def action_on_disconnect(self):
        if self.attribute_controller:
            if self.attribute_controller.isVisible():
                self.attribute_controller.close()
                self._widget_attribute_controller = None

            # Discard the image acquisition manager.
            if self.iam:
                self.iam.destroy()
                self._iam = None

    def action_on_select_file(self):
        # Show a dialog and update the CTI file list.
        dialog = QFileDialog(self)
        dialog.setWindowTitle('Select a CTI file to load')
        dialog.setNameFilter('CTI files (*.cti)')
        dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec_() == QDialog.Accepted:
            #
            file_path = dialog.selectedFiles()[0]

            #
            self.harvester_core.reset()

            # Update the path to the target GenTL Producer.
            self.harvester_core.add_cti_file(file_path)

            # Update the device list.
            self.harvester_core.update_device_info_list()

    def is_enabled_on_select_file(self):
        enable = False
        if self.iam is None:
            enable = True
        return enable

    def action_on_update_list(self):
        self.harvester_core.update_device_info_list()

    def is_enabled_on_update_list(self):
        enable = False
        if self.cti_files:
            if self.iam is None:
                enable = True
        return enable

    def is_enabled_on_disconnect(self):
        enable = False
        if self.cti_files:
            if self.iam:
                enable = True
        return enable

    def action_on_start_image_acquisition(self):
        if self.iam.is_acquiring_images:
            # If it's pausing drawing images, just resume it and
            # immediately return this method.
            if self.canvas.is_pausing:
                self.canvas.resume_drawing()
        else:
            self.iam.start_image_acquisition()

    def is_enabled_on_start_image_acquisition(self):
        enable = False
        if self.cti_files:
            if self.iam:
                if not self.iam.is_acquiring_images or \
                        self.canvas.is_pausing:
                    enable = True
        return enable

    def action_on_stop_image_acquisition(self):
        self.iam.stop_image_acquisition()
        self.canvas.pause_drawing(False)

    def is_enabled_on_stop_image_acquisition(self):
        enable = False
        if self.cti_files:
            if self.iam:
                if self.iam.is_acquiring_images:
                    enable = True
        return enable

    def action_on_show_attribute_controller(self):
        with QMutexLocker(self.mutex):
            if self.iam and self.attribute_controller.isHidden():
                self.attribute_controller.show()
                self.attribute_controller.expand_all()

    def is_enabled_on_show_attribute_controller(self):
        enable = False
        if self.cti_files:
            if self.iam is not None:
                enable = True
        return enable

    def action_on_toggle_drawing(self):
        self.canvas.toggle_drawing()

    def is_enabled_on_toggle_drawing(self):
        enable = False
        if self.cti_files:
            if self.iam:
                if self.iam.is_acquiring_images:
                    enable = True
        return enable

    def action_on_show_about(self):
        self.about.setModal(False)
        self.about.show()


class ActionSelectFile(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionUpdateList(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionConnect(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionDisconnect(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionStartImageAcquisition(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionToggleDrawing(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled,
            checkable=True
        )

    def _update(self):
        #
        checked = True if self.parent().canvas.is_pausing else False
        self.setChecked(checked)


class ActionStopImageAcquisition(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionShowAttributeController(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )


class ActionShowAbout(Action):
    def __init__(
            self, icon=None, title=None, parent=None, action=None, is_enabled=None
    ):
        #
        super().__init__(
            icon=icon, title=title, parent=parent, action=action, is_enabled=is_enabled
        )

        #
        self._is_model = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    harvester = Harvester()
    harvester.show()
    sys.exit(app.exec_())

