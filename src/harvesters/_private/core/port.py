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
import io
from datetime import datetime
import os
import sys
import pathlib
from typing import Optional, Dict
import ntpath
import tempfile
import re
from urllib.parse import urlparse

# Related third party imports
from genicam.genapi import AbstractPort
from genicam.genapi import EAccessMode
from genicam.genapi import NodeMap
from genicam.genapi import GenericException as GenApi_GenericException
from genicam.genapi import LogicalErrorException

from genicam.gentl import Port

# Local application/library specific imports
from harvesters.util.logging import get_logger
from harvesters._private.core.helper.system import is_running_on_windows


_logger = get_logger(name=__name__)


def _get_port_connected_node_map(
        *, port: Optional[Port] = None, file_path: Optional[str] = None,
        xml_dir_to_store: Optional[str] = None,
        file_dict: Dict[str, bytes] = None, do_clean_up: bool = True):
    global _logger

    assert port

    node_map = NodeMap()

    file_path = _retrieve_file_path(
        port=port, file_path_to_load=file_path,
        xml_dir_to_store=xml_dir_to_store, file_dict=file_dict)

    if file_path is not None:
        # Every valid (zipped) XML file MUST be parsed as expected and the
        # method returns the file path where the file is located:
        # Then load the XML file content on the node map object.
        has_valid_file = True

        # In this case, the file has been identified as a Zip file but
        # has been diagnosed as BadZipFile due to a technical reason.
        # Let the NodeMap object load the file from the path:
        try:
            node_map.load_xml_from_zip_file(file_path)
        except GenApi_GenericException:
            try:
                node_map.load_xml_from_file(file_path)
            except GenApi_GenericException as e:
                if file_dict:
                    if do_clean_up:
                        _remove_intermediate_file(file_path)
                    _logger.warning(e, exc_info=True)
                    raise
                else:
                    _logger.warning(e, exc_info=True)

        if do_clean_up:
            _remove_intermediate_file(file_path)

        if has_valid_file:
            concrete_port = ConcretePort(port)
            node_map.connect(concrete_port, port.name)

    return node_map


def _remove_intermediate_file(file_path: str):
    global _logger
    os.remove(file_path)
    _logger.debug('deleted: {0}'.format(file_path))


def _retrieve_file_path(
        *, port: Optional[Port] = None, url: Optional[str] = None,
        file_path_to_load: Optional[str] = None,
        xml_dir_to_store: Optional[str] = None,
        file_dict: Dict[str, bytes] = None):
    global _logger

    if file_path_to_load:
        if not os.path.exists(file_path_to_load):
            raise LogicalErrorException(
                '{} does not exist.'.format(file_path_to_load))
    else:
        if url is None:
            if len(port.url_info_list) > 0:
                url = port.url_info_list[0].url
            else:
                raise LogicalErrorException(
                    'The target port does not hold any URL.')

        _logger.debug('fetched url: {}'.format(url))

        location, others = url.split(':', 1)
        location = location.lower()

        if location == 'local':
            file_name, address, size = others.split(';')
            address = int(address, 16)
            # Remove optional /// after local: See section 4.1.2 in GenTL
            # v1.4 Standard
            file_name = file_name.lstrip('/')

            delimiter = '?'
            if delimiter in size:
                size, _ = size.split(delimiter)
            size = int(size, 16)  # From Hex to Dec

            size, binary_data = port.read(address, size)

            file_path_to_load = _save_file(
                xml_dir_to_store=xml_dir_to_store, file_name=file_name,
                binary_data=binary_data, file_dict=file_dict)

        elif location == 'file':
            file_path_to_load = urlparse(url).path
            if is_running_on_windows():
                file_path_to_load = re.sub(r'^/+', '', file_path_to_load)

        elif location == 'http' or location == 'https':
            raise NotImplementedError(
                'Failed to parse URL {}: Harvester has not supported '
                'downloading a device description file from vendor '
                'web site. If you must rely on the current condition,'
                'just try to make a request to the Harvester '
                'maintainer.'.format(url))
        else:
            raise LogicalErrorException(
                'Failed to parse URL {}: Unknown format.'.format(url))

    return file_path_to_load


def _save_file(
            *, xml_dir_to_store: Optional[str] = None,
            file_name: Optional[str] = None, binary_data=None,
            file_dict: Dict[str, bytes] = None):
    global _logger

    assert binary_data
    assert file_name

    bytes_io = io.BytesIO(binary_data)

    if xml_dir_to_store is not None:
        if not os.path.exists(xml_dir_to_store):
            os.makedirs(xml_dir_to_store)
    else:
        xml_dir_to_store = tempfile.mkdtemp(
            prefix=datetime.now().strftime('%Y%m%d%H%M%S_'))

    _file_name = ntpath.basename(file_name)
    file_path = os.path.join(xml_dir_to_store, _file_name)

    mode = 'w+'
    data_to_write = bytes_io.getvalue()
    if pathlib.Path(file_path).suffix.lower() != '.zip':
        data_to_write = _drop_padding_data(
            data_to_write, file_name=_file_name, file_dict=file_dict)

    try:
        with open(file_path, mode + 'b') as f:
            f.write(data_to_write)
    except UnicodeEncodeError:
        # Probably you've caught "UnicodeEncodeError: 'charmap' codec can't
        # encode characters"; the file must be a text file:
        try:
            with io.open(file_path, mode, encoding="utf-8") as f:
                f.write(data_to_write)
        except:
            e = sys.exc_info()[0]
            _logger.error(e, exc_info=True)
            raise
    except:
        e = sys.exc_info()[0]
        _logger.error(e, exc_info=True)
        raise
    else:
        _logger.debug("created: {}".format(file_path))

    return file_path


def _drop_padding_data(
        data_to_write: bytes, *, file_name: str = None,
        file_dict: Dict[str, bytes] = None):
    global _logger

    assert data_to_write

    data_to_be_found = b'\x00'
    if file_dict and file_name:
        result = None
        key = None
        for pattern in file_dict.keys():
            result = re.search(pattern, file_name)
            if result:
                key = pattern
                break
        if result and key:
            data_to_be_found = file_dict[key]

    pos = data_to_write.find(data_to_be_found)
    if pos != -1:
        _logger.debug(
            "an x00 has been found in {}; "
            "the array will be truncated.".format(file_name))
        return data_to_write[:pos]
    else:
        return data_to_write


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
        return EAccessMode.RW if self.is_open() else EAccessMode.NA
