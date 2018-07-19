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
import re
import sys

# Related third party imports
from PyQt5.Qt import Qt, QStyledItemDelegate, QColor
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, \
    QSortFilterProxyModel
from PyQt5.QtWidgets import QApplication, QTreeView, \
    QSpinBox, QPushButton, QComboBox, QWidget, \
    QLineEdit

from genicam2.genapi import NodeMap
from genicam2.genapi import EInterfaceType, EAccessMode, EVisibility

# Local application/library specific imports
from harvesters._private.frontend.pyqt5.helper import get_system_font


class TreeItem(object):
    _readable_nodes = [
        EInterfaceType.intfIBoolean,
        EInterfaceType.intfIEnumeration,
        EInterfaceType.intfIFloat,
        EInterfaceType.intfIInteger,
        EInterfaceType.intfIString,
        EInterfaceType.intfIRegister,
    ]

    _readable_access_modes = [EAccessMode.RW, EAccessMode.RO]

    def __init__(self, data=None, parent_item=None):
        #
        super().__init__()

        #
        self._parent_item = parent_item
        self._own_data = data
        self._child_items = []

    @property
    def parent_item(self):
        return self._parent_item

    @property
    def own_data(self):
        return self._own_data

    @property
    def child_items(self):
        return self._child_items

    def appendChild(self, item):
        self.child_items.append(item)

    def child(self, row):
        return self.child_items[row]

    def childCount(self):
        return len(self.child_items)

    def columnCount(self):
        ret = 0
        try:
            ret = len(self.own_data)
        except TypeError:
            ret = 1
        return ret

    def data(self, column):
        if isinstance(self.own_data[column], str):
            try:
                return self.own_data[column]
            except IndexError:
                return None
        else:
            value = ''
            feature = self.own_data[column]
            if column == 0:
                value = feature.node.display_name
            else:
                interface_type = feature.node.principal_interface_type

                if interface_type != EInterfaceType.intfICategory:
                    if interface_type == EInterfaceType.intfICommand:
                        value = '-- Click here --'
                    else:
                        value = 'N/A'
                        if feature.node.get_access_mode() in \
                                self._readable_access_modes and \
                                interface_type in self._readable_nodes:
                            try:
                                value = str(feature.value)
                            except AttributeError:
                                try:
                                    value = feature.to_string()
                                except AttributeError:
                                    pass

            return value

    def tooltip(self, column):
        if isinstance(self.own_data[column], str):
            return None
        else:
            feature = self.own_data[column]
            return feature.node.tooltip

    def background(self, column):
        if isinstance(self.own_data[column], str):
            return None
        else:
            feature = self.own_data[column]
            interface_type = feature.node.principal_interface_type
            if interface_type == EInterfaceType.intfICategory:
                return QColor(56, 147, 189)
            else:
                return None

    def foreground(self, column):
        if isinstance(self.own_data[column], str):
            return None
        else:
            feature = self.own_data[column]
            interface_type = feature.node.principal_interface_type
            if interface_type == EInterfaceType.intfICategory:
                return QColor('white')
            else:
                return None

    def parent(self):
        return self._parent_item

    def row(self):
        if self._parent_item:
            return self._parent_item.child_items.index(self)

        return 0


class FeatureTreeModel(QAbstractItemModel):
    #
    _capable_roles = [
        Qt.DisplayRole, Qt.ToolTipRole, Qt.BackgroundColorRole,
        Qt.ForegroundRole
    ]

    #
    _editables = [EAccessMode.RW, EAccessMode.WO]

    def __init__(self, parent=None, node_map: NodeMap=None, thread=None):
        """
        REMARKS: QAbstractItemModel might impact the performance and could
        slow Harvester. As far as we've confirmed, QAbstractItemModel calls
        its index() method for every item already shown. Especially, such
        a call happens every time when (1) its view got/lost focus or (2)
        its view was scrolled. If such slow performance makes people
        irritating we should investigate how can we optimize it.

        """
        #
        super().__init__()

        #
        self._root_item = TreeItem(('Feature Name', 'Value'))
        self._node_map = node_map
        if node_map:
            self.setupModelData(node_map.Root.features, self._root_item)

    @property
    def root_item(self):
        return self._root_item

    def columnCount(self, parent=None, *args, **kwargs):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.root_item.columnCount()

    def data(self, index: QModelIndex, role=None):
        if not index.isValid():
            return None

        if role not in self._capable_roles:
            return None

        item = index.internalPointer()
        value = None
        if role == Qt.DisplayRole:
            value = item.data(index.column())
        elif role == Qt.ToolTipRole:
            value = item.tooltip(index.column())
        elif role == Qt.BackgroundColorRole:
            value = item.background(index.column())
        else:
            value = item.foreground(index.column())

        return value

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        tree_item = index.internalPointer()
        feature = tree_item.own_data[0]
        access_mode = feature.node.get_access_mode()

        if access_mode in self._editables:
            ret = Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            if index.column() == 1:
                ret = Qt.NoItemFlags
            else:
                ret = Qt.ItemIsEnabled
        return ret

    def headerData(self, p_int, Qt_Orientation, role=None):
        # p_int: section
        if Qt_Orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root_item.data(p_int)
        return None

    def index(self, p_int, p_int_1, parent=None, *args, **kwargs):
        # p_int: row
        # p_int_1: column
        if not self.hasIndex(p_int, p_int_1, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(p_int)
        if child_item:
            return self.createIndex(p_int, p_int_1, child_item)
        else:
            return QModelIndex()

    def parent(self, index=None):
        if not index.isValid():
            return index

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=None, *args, **kwargs):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def setupModelData(self, features, parent_item):
        for feature in features:
            interface_type = feature.node.principal_interface_type
            item = TreeItem([feature, feature], parent_item)
            parent_item.appendChild(item)
            if interface_type == EInterfaceType.intfICategory:
                self.setupModelData(feature.features, item)

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            # TODO: Check the type of the target and convert the given value.
            self.dataChanged.emit(index, index)

            #
            tree_item = index.internalPointer()
            feature = tree_item.own_data[0]
            interface_type = feature.node.principal_interface_type
            try:
                if interface_type == EInterfaceType.intfICommand:
                    if value:
                        feature.execute()
                elif interface_type == EInterfaceType.intfIBoolean:
                    feature.value = True if value.lower == 'true' else False
                elif interface_type == EInterfaceType.intfIFloat:
                    feature.value = float(value)
                else:
                    feature.value = value
                return True
            except:
                # TODO: Specify appropriate exceptions
                return False


class FeatureEditDelegate(QStyledItemDelegate):
    def __init__(self, proxy, parent=None):
        #
        super().__init__()

        #
        self._proxy = proxy

    def createEditor(self, parent: QWidget, QStyleOptionViewItem, proxy_index: QModelIndex):

        # Get the actual source.
        src_index = self._proxy.mapToSource(proxy_index)

        # If it's the column #0, then immediately return.
        if src_index.column() == 0:
            return None

        tree_item = src_index.internalPointer()
        feature = tree_item.own_data[0]
        interface_type = feature.node.principal_interface_type

        if interface_type == EInterfaceType.intfIInteger:
            w = QSpinBox(parent)
            w.setRange(feature.min, feature.max)
            w.setSingleStep(feature.inc)
            w.setValue(feature.value)
        elif interface_type == EInterfaceType.intfICommand:
            w = QPushButton(parent)
            w.setText('Execute')
            w.clicked.connect(lambda: self.on_button_clicked(proxy_index))
        elif interface_type == EInterfaceType.intfIBoolean:
            w = QComboBox(parent)
            boolean_ints = {'False': 0, 'True': 1}
            w.addItem('False')
            w.addItem('True')
            proxy_index = boolean_ints['True'] if feature.value else boolean_ints['False']
            w.setCurrentIndex(proxy_index)
        elif interface_type == EInterfaceType.intfIEnumeration:
            w = QComboBox(parent)
            for item in feature.entries:
                w.addItem(item.symbolic)
            w.setCurrentText(feature.value)
        elif interface_type == EInterfaceType.intfIString:
            w = QLineEdit(parent)
            w.setText(feature.value)
        elif interface_type == EInterfaceType.intfIFloat:
            w = QLineEdit(parent)
            w.setText(str(feature.value))
        else:
            return None

        #
        w.setFont(get_system_font())

        return w

    def setEditorData(self, editor: QWidget, proxy_index: QModelIndex):

        src_index = self._proxy.mapToSource(proxy_index)
        value = src_index.data(Qt.DisplayRole)
        tree_item = src_index.internalPointer()
        feature = tree_item.own_data[0]
        interface_type = feature.node.principal_interface_type

        if interface_type == EInterfaceType.intfIInteger:
            editor.setValue(int(value))
        elif interface_type == EInterfaceType.intfIBoolean:
            i = editor.findText(value, Qt.MatchFixedString)
            editor.setCurrentIndex(i)
        elif interface_type == EInterfaceType.intfIEnumeration:
            editor.setEditText(value)
        elif interface_type == EInterfaceType.intfIString:
            editor.setText(value)
        elif interface_type == EInterfaceType.intfIFloat:
            editor.setText(value)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, proxy_index: QModelIndex):

        src_index = self._proxy.mapToSource(proxy_index)
        tree_item = src_index.internalPointer()
        feature = tree_item.own_data[0]
        interface_type = feature.node.principal_interface_type

        if interface_type == EInterfaceType.intfIInteger:
            data = editor.value()
            model.setData(proxy_index, data)
        elif interface_type == EInterfaceType.intfIBoolean:
            data = editor.currentText()
            model.setData(proxy_index, data)
        elif interface_type == EInterfaceType.intfIEnumeration:
            data = editor.currentText()
            model.setData(proxy_index, data)
        elif interface_type == EInterfaceType.intfIString:
            data = editor.text()
            model.setData(proxy_index, data)
        elif interface_type == EInterfaceType.intfIFloat:
            data = editor.text()
            model.setData(proxy_index, data)

    def on_button_clicked(self, proxy_index: QModelIndex):

        src_index = self._proxy.mapToSource(proxy_index)
        tree_item = src_index.internalPointer()
        feature = tree_item.own_data[0]
        interface_type = feature.node.principal_interface_type

        if interface_type == EInterfaceType.intfICommand:
            feature.execute()


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, visibility=EVisibility.Beginner, parent=None):
        #
        super().__init__()

        #
        self._visibility = visibility
        self._keyword = ''

    def filterVisibility(self, visibility):
        beginner_items = {EVisibility.Beginner}
        expert_items = beginner_items.union({EVisibility.Expert})
        guru_items = expert_items.union({EVisibility.Guru})
        all_items = guru_items.union({EVisibility.Invisible})

        items_dict = {
            EVisibility.Beginner: beginner_items,
            EVisibility.Expert: expert_items,
            EVisibility.Guru: guru_items,
            EVisibility.Invisible: all_items
        }

        if visibility not in items_dict[self._visibility]:
            return False
        else:
            return True

    def filterPattern(self, name):
        if not re.search(self._keyword, name, re.IGNORECASE):
            print(name + ': refused')
            return False
        else:
            print(name + ': accepted')
            return True

    def setVisibility(self, visibility: EVisibility):
        self._visibility = visibility
        self.invalidateFilter()

    def setKeyword(self, keyword: str):
        self._keyword = keyword
        self.invalidateFilter()

    def filterAcceptsRow(self, src_row, src_parent: QModelIndex):
        #
        src_model = self.sourceModel()
        src_index = src_model.index(src_row, 0, parent=src_parent)

        tree_item = src_index.internalPointer()
        feature = tree_item.own_data[0]
        name = feature.node.display_name
        visibility = feature.node.visibility
        if len(tree_item.child_items):
            for child in tree_item.child_items:
                if self.filterAcceptsRow(child.row(), src_index):
                    return True
            return False
        else:
            matches = re.search(self._keyword, name, re.IGNORECASE)

        if matches:
            result = self.filterVisibility(visibility)
        else:
            result = False
        return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = FeatureTreeModel()
    view = QTreeView(model)
    view.show()
    sys.exit(app.exec_())
