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
import sys

# Related third party imports
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication, QPlainTextEdit, \
    QVBoxLayout, QHBoxLayout, QLineEdit, QFrame

# Local application/library specific imports
from system import get_system_font
from harvester import __version__


class DecoratedDialog(QDialog):
    def __init__(self, parent_widget=None, path_to_image=None):
        #
        super().__init__(parent_widget)

        #
        self._path_to_image = path_to_image

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), QPixmap("image/background/about.jpg"))


class TransparentLineEdit(QLineEdit):
    def __init__(self, text):
        #
        super().__init__(text)

        self.setReadOnly(True)
        self.setFont(get_system_font())
        self.setStyleSheet('background: rgb(0, 0, 0, 0%)')
        self.setFrame(False)


class TransparentTextEdit(QPlainTextEdit):
    def __init__(self, text):
        #
        super().__init__(text)

        self.setReadOnly(True)
        self.setFont(get_system_font())
        self.setStyleSheet('background: rgb(0, 0, 0, 0%)')
        self.setLineWrapMode(True)
        self.setFrameStyle(QFrame.NoFrame)


class About(QDialog):
    indent = '    '

    def __init__(self, parent_widget=None):
        #
        super().__init__(parent_widget)

        #
        self._parent_widget = parent_widget

        #
        self._license = ''
        self._initialize_license()

        #
        layout_main = QVBoxLayout()
        layout_text_boxes = QVBoxLayout()
        layout_image = QHBoxLayout()

        #
        content = 'Pieter Bruegel the Elder, The Harvesters\n'
        content += '(c) 2000–2018 The Metropolitan Museum of Arts\n'
        content += '\n'

        #
        content += 'Harvester ' + __version__ + '\n'
        content += '\n'

        #
        content += self._license
        content += '\n'

        #
        content += 'The Harvester GUI uses the following libraries/resources:\n'
        content += 'VisPy (http://vispy.org/)\n'
        content += 'PyQt5 (https://www.riverbankcomputing.com/software/pyqt/intro/)\n'
        content += 'Icons8 (https://icons8.com/)'

        text_about_harvester = TransparentTextEdit(content)
        layout_text_boxes.addWidget(text_about_harvester)

        #
        image = DecoratedDialog()
        image.setFixedWidth(640)
        image.setFixedHeight(480)

        #
        layout_image.addWidget(image)

        #
        layout_main.addLayout(layout_image)
        layout_main.addLayout(layout_text_boxes)
        self.setLayout(layout_main)
        self.setFixedHeight(750)

        #
        self.setWindowTitle('About Harvester')

    def _get_version_info(self):
        return 'Version ' + self._parent_widget.version

    def _initialize_license(self):
        try:
            with open('LICENSE') as f:
                for line in f:
                    self._license += line
                self._license += '\n'
        except FileNotFoundError as e:
            self._license += 'WARNING: This is ILLEGAL becuase '
            self._license += 'the LICENSE file can\'t be found. '
            self._license += 'The file must be placed in an appropriate place.\n'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    about = About()
    about.show()
    sys.exit(app.exec_())