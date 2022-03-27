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
from __future__ import annotations
from collections.abc import Iterable
from ctypes import CDLL
from datetime import datetime
from enum import IntEnum
import io
import json
from logging import Logger
from math import ceil, isclose
import ntpath
import os
import pathlib
from queue import Queue
from queue import Full, Empty
import re
import signal
import sys
from threading import Lock, Thread, Event
from threading import current_thread, main_thread
import time
from typing import Union, List, Optional, Dict, TypeVar, Any
from urllib.parse import urlparse
from warnings import warn
import weakref
import tempfile

# Related third party imports
import numpy

from genicam.genapi import NodeMap
from genicam.genapi import GenericException as GenApi_GenericException
from genicam.genapi import LogicalErrorException
from genicam.genapi import ChunkAdapterGeneric, ChunkAdapterU3V, \
    ChunkAdapterGEV

from genicam.gentl import TimeoutException
from genicam.gentl import GenericException as GenTL_GenericException
from genicam.gentl import GenTLProducer, BufferToken, EventManagerNewBuffer
from genicam.gentl import DEVICE_ACCESS_FLAGS_LIST, EVENT_TYPE_LIST, \
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST, \
    PAYLOADTYPE_INFO_IDS
from genicam.gentl import Port, PIXELFORMAT_NAMESPACE_IDS
from genicam.gentl import Buffer as _Buffer, Device as _Device, \
    DataStream as _DataStream, Interface as _Interface, System as _System, \
    GenTLProducer as _GenTLProducer, DeviceInfo as _DeviceInfo

# Local application/library specific imports
from harvesters._private.core.port import ConcretePort
from harvesters._private.core.statistics import Statistics
from harvesters._private.core.helper.system import is_running_on_windows
from harvesters.util.logging import get_logger
from harvesters.util.pfnc import dict_by_names, dict_by_ints
from harvesters.util.pfnc import Dictionary, _PixelFormat
from harvesters.util.pfnc import component_2d_formats


_is_logging_buffer = True if 'HARVESTERS_LOG_BUFFER' in os.environ else False
_sleep_duration_default = 0.000001  # s


_logger = get_logger(name=__name__)


class ParameterKey(IntEnum):
    __doc__ = "A list of variable/defined parameters."
    _ENABLE_PROFILE = -1,
    LOGGER = 0,  # Determines the logger to be used; the value type must be :class:`Logger`.
    TIMEOUT_PERIOD_ON_MODULE_ENUMERATION = 2,  # Determines the time-out period that is applied on the GenTL module enumeration; the value type must be :class:`int`.
    ENABLE_CLEANING_UP_INTERMEDIATE_FILES = 3,  # Determines if you want to delete all of the intermediate files; set :const:`True` if you want to delete, otherwise set :const:`False`.

    THREAD_SLEEP_PERIOD = 100,  # Determines the sleep period that is applied on every single worker execution; the value type is :class:`int`.
    TIMEOUT_PERIOD_ON_UPDATE_EVENT_DATA_CALL = 101,  # Determines the time-out period that is applied on a single GenTL EventGetData call; the value type must be :class:`int`; the unit is [ms].
    TIMEOUT_PERIOD_ON_FETCH_CALL = 102,  # Determines the time-out period that is applied on a single fetch method call; the value type must be :class:`int`; the unit is [s].
    NUM_BUFFERS_FOR_FETCH_CALL = 103,  # Determines the number of buffers to be allocated on the GenTL Producer-side; the value type must be :class:`int`.
    REMOTE_DEVICE_SOURCE_XML_FILE_PATH = 104,  # Determines the file path where the source GenICam device description file is located; the value type must be :class:`str`.
    ENABLE_AUTO_CHUNK_DATA_UPDATE = 105,  # Determines if you let the :class:`ImageAcquirer` object to automatically update the chunk data when the owner image data is fetched; the value type must be :class:`bool`.
    DEVICE_OWNERSHIP_PRIVILEGE = 106,
    THREAD_FACTORY_METHOD = 107,  # Determines the thread factory method where the corersponding thread worker is bound; the value type must be callable.


class ParameterSet:
    """
    A set of parameters. A typical use case is to use the parameter set to
    configure a subject.
    """
    def __init__(self,
                 parameter_dict: Optional[Dict[ParameterKey, Any]] = None):
        """
        Parameters
        ----------
        parameter_dict: Optional[Dict[ParameterKey, Any]] = None):
            A parameter dictionary. You can add or remove an arbitrary
            key after the instantiation.
        """
        super().__init__()
        self._dict = parameter_dict if parameter_dict else dict()

    @property
    def parameters(self) -> Dict[ParameterKey, Any]:
        return self._dict

    @staticmethod
    def check(declared: ParameterSet, supported_keys: List[ParameterKey]):
        if declared:
            global _logger
            for k in declared.parameters.keys():
                if k not in supported_keys:
                    _logger.warning("not supported; key: {}".format(k))

    @staticmethod
    def get(key: ParameterKey, default: Optional[Any], config: Optional[ParameterSet] = None):
        if config is None:
            return default
        else:
            try:
                value = config._dict[key]
            except KeyError:
                return default
            else:
                return value

    def add(self, key: ParameterKey, value: Any):
        global _logger
        if key in self._dict.keys():
            _logger.debug("overwritten; key: {}, value: {}".format(
                key.name, self._dict[key]))

        self._dict[key] = value
        _logger.debug("added parameter; key: {}, value: {}".format(
            key.name, value))

    def remove(self, key: ParameterKey):
        if key in self._dict.keys():
            del self._dict[key]
            _logger.debug("removed parameter; key: {}".format(key.name))


def _family_tree(node, tree=""):
    is_origin = True if tree == "" else False

    try:
        name = node.id_
    except AttributeError:
        name = str(node)

    if is_origin:
        tree = name
    else:
        tree += " :: " + name

    try:
        parent = node.parent
    except AttributeError:
        return tree
    else:
        tree = _family_tree(parent, tree)

    return tree


def _deprecated(deprecated: object, alternative: object) -> None:
    #
    items = []
    for obj in (deprecated, alternative):
        items.append(obj.__name__ + '()' if callable(obj) else obj)

    keys = {'deprecated': 0, 'alternative': 1}
    warn(
        '{} will be deprecated shortly. Use {} instead.'.format(
            items[keys['deprecated']], items[keys['alternative']]
        ),
        DeprecationWarning, stacklevel=3
    )


class _Delegate:
    def __init__(self, source):
        self._source_object = source
        self._attributes = [
            f for f in dir(
                type(self._source_object)) if not f.startswith('_')]

    def __getattr__(self, attribute):
        if attribute in self._attributes:
            if isinstance(
                getattr(type(self._source_object), attribute, None),
                    property):
                return getattr(self._source_object, attribute)
            else:
                def m(*args):
                    return getattr(self._source_object, attribute)(*args)
                setattr(self, attribute, m)
                return m
        else:
            raise AttributeError


class Module(_Delegate):
    def __init__(self, *, module, parent, port: Port = None,
                 file_path: Optional[str] = None,
                 file_dict: Optional[Dict[str, bytes]] = None,
                 do_clean_up: bool = True,
                 xml_dir_to_store: Optional[str] = None):
        super().__init__(module)
        self._module = module
        self._parent = parent
        self._node_map = self._create_node_map(
            port=port, file_path=file_path, file_dict=file_dict,
            do_clean_up=do_clean_up, xml_dir_to_store=xml_dir_to_store) if \
            port else None

    def _create_node_map(
            self, *, port: Optional[Port] = None,
            file_path: Optional[str] = None,
            xml_dir_to_store: Optional[str] = None,
            file_dict: Dict[str, bytes] = None, do_clean_up: bool = True):
        global _logger

        node_map = NodeMap()

        file_path = self._retrieve_file_path(
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
                            self._remove_intermediate_file(file_path)
                        _logger.warning(e, exc_info=True)
                        raise
                    else:
                        _logger.warning(e, exc_info=True)

            if do_clean_up:
                self._remove_intermediate_file(file_path)

            if has_valid_file:
                concrete_port = ConcretePort(port)
                node_map.connect(concrete_port, port.name)

        return node_map

    @staticmethod
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
            if not url:
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

    @staticmethod
    def _remove_intermediate_file(file_path: str):
        global _logger
        os.remove(file_path)
        _logger.debug('deleted: {0}'.format(file_path))

    @property
    def module(self) -> Union[System, Interface, Device, RemoteDevice,
                              DataStream, Buffer]:
        """
        Union[System, Interface, Device, RemoteDevice, DataStream, Buffer]:
        The corresponding GenTL module.
        """
        return self._module

    @property
    def node_map(self) -> NodeMap:
        """
        NodeMap: The GenICam feature node map that belongs to the owner
        object.
        """
        return self._node_map

    @property
    def parent(self) -> Union[None, System, Interface, Device,
                              RemoteDevice, DataStream]:
        """
        Union[None, System, Interface, Device, RemoteDevice, DataStream]:
        The parent raw GenTL module.
        """
        return self._parent


class DataStream(Module):
    """Represents a GenTL Data Stream module."""
    def __init__(self, *, module: _DataStream, parent=None):
        super().__init__(module=module, port=module.port, parent=parent)


class RemoteDevice(Module):
    """Represents a GenTL Remote Device module."""
    def __init__(self, *, module: _Device, parent=None,
                 file_path: Optional[str] = None,
                 file_dict: Optional[Dict[str, bytes]] = None,
                 do_clean_up: bool = True,
                 xml_dir_to_store: Optional[str] = None):
        super().__init__(
            module=module, port=module.remote_port, parent=parent,
            file_path=file_path,
            file_dict=file_dict, do_clean_up=do_clean_up,
            xml_dir_to_store=xml_dir_to_store)

    @property
    def port(self):
        return self.module.remote_port


class Device(Module):
    """Represents a GenTL Device module that is a proxy of a remote device."""
    def __init__(self, *, module: _Device, parent=None):
        super().__init__(module=module, port=module.local_port, parent=parent)

    @property
    def port(self):
        return self.module.local_port


class Interface(Module):
    """Represents a GenTL Interface module."""
    def __init__(self, *, module: _Interface, parent=None):
        super().__init__(module=module, port=module.port, parent=parent)


class System(Module):
    """Represents a GenTL System module."""
    def __init__(self, *, module: _System, parent):
        super().__init__(module=module, parent=parent, port=module.port)


class Producer(Module):
    """Represents a GenTL Producer."""
    def __init__(self, *, module: _GenTLProducer):
        super().__init__(module=module, parent=None)


class DeviceInfo(Module):
    search_keys = [
        f for f in dir(_DeviceInfo) if
        not f.startswith('_') and
        isinstance(getattr(_DeviceInfo, f, None), property)]

    """Represents a GenTL Device Information module."""
    def __init__(self, *, module, parent=None):
        global _logger
        super().__init__(module=module, parent=parent)
        self._property_dict = dict()
        self._build_dict()

    def _build_dict(self):
        for p in self.search_keys:
            value = None
            try:
                value = getattr(self._module, p, None)
            except GenTL_GenericException as e:
                _logger.debug(e, exc_info=True)
            self._property_dict[p] = value

    @property
    def property_dict(self):
        return self._property_dict

    def __repr__(self):
        return str(self._property_dict)


class _SignalHandler:
    _event = None
    _subject = None

    def __init__(self, *, event, subject: ImageAcquirer):
        super().__init__()

        assert event
        assert subject

        self._event = event
        self._subject = subject

    def __call__(self, signum, frame):
        """
        A registered Python signal modules will call this method.
        """
        global _logger
        _logger.debug('caught signal: {}'.format(self._event))
        self._event.set()
        self._subject.destroy()


class ThreadBase:
    """
    Is a base class that is used to implement a thread that users want to
    use. For example, in general, PyQt application should implement a
    thread using QThread instead of Python's built-in Thread class.
    """
    def __init__(self, *, mutex=None):
        super().__init__()

        self._mutex = mutex
        self._is_running = False
        self._id = None

    def start(self) -> None:
        global _logger

        self._internal_start()
        _logger.debug('launched thread: {}'.format(self))

    def _internal_start(self) -> None:
        """
        Releases the acquired mutex.

        This method is abstract and should be reimplemented in any sub-class.
        """
        raise NotImplementedError

    def stop(self) -> None:
        global _logger
        self._internal_stop()
        _logger.debug('terminated thread: {}'.format(self))

    def join(self):
        """
        Waits until the given task is completed.

        This method is abstract and should be reimplemented in any sub-class.
        """
        raise NotImplementedError

    def _internal_stop(self):
        """
        Releases the acquired mutex.

        This method is abstract and should be reimplemented in any sub-class.
        """
        raise NotImplementedError

    def acquire(self):
        """
        Acquires a mutex.

        This method is abstract and should be reimplemented in any sub-class.

        :return: An acquired :class:`MutexLocker` object.
        :rtype: MutexLocker
        """
        raise NotImplementedError

    def release(self) -> None:
        """
        Releases the acquired mutex.

        This method is abstract and should be reimplemented in any sub-class.
        """
        raise NotImplementedError

    def is_running(self) -> bool:
        """
        Returns the truth value of a proposition: The thread is running.

        This method is abstract and should be reimplemented in any sub-class.

        Returns
        -------
        bool
            :const:`True` if the thread is running. Otherwise it returns
            :const:`False`.
        """
        raise NotImplementedError

    @property
    def id_(self) -> int:
        return self._id


class MutexLocker:
    def __init__(self, thread: ThreadBase=None):
        """
        :param thread:
        """
        assert thread

        super().__init__()

        self._thread = thread
        self._locked_mutex = None

    def __enter__(self):
        if not self._thread:
            return None

        self._locked_mutex = self._thread.acquire()
        return self._locked_mutex

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._thread:
            return

        self._thread.release()


class _ImageAcquisitionThread(ThreadBase):
    def __init__(
            self, *,
            image_acquire=None):
        """

        :param image_acquire:
        """
        assert image_acquire

        super().__init__(mutex=Lock())

        self._ia = image_acquire
        self._worker = self._ia.worker_image_acquisition
        self._sleep_duration = self._ia.sleep_duration
        self._thread = None

    def _internal_start(self):
        self._thread = _NativeThread(thread_owner=self, worker=self._worker,
                                     sleep_duration=self._sleep_duration)
        self._id = self._thread.id_
        self._is_running = True
        self._thread.start()

    def join(self):
        global _logger
        _logger.debug('going to join thread: {}'.format(self))
        self._thread.join()
        _logger.debug('joined thread: {}'.format(self))

    def _internal_stop(self):
        if not self._thread:
            return

        self._thread.stop()
        self._is_running = False

    def acquire(self):
        if self._thread:
            return self._thread.acquire()
        else:
            return None

    def release(self):
        if self._thread:
            self._thread.release()
        else:
            return

    @property
    def worker(self):
        if self._thread:
            return self._thread.worker
        else:
            return None

    @worker.setter
    def worker(self, obj):
        if self._thread:
            self._thread.worker = obj
        else:
            return

    @property
    def mutex(self):
        return self._mutex

    @property
    def id_(self) -> str:
        return self._thread.id_ if self._thread else "Not available"

    def is_running(self):
        return self._is_running


class _NativeThread(Thread):
    def __init__(self, thread_owner=None, worker=None,
                 sleep_duration=_sleep_duration_default):
        """

        :param thread_owner:
        :param worker:
        :param sleep_duration:
        """
        assert thread_owner

        super().__init__(daemon=self._is_interactive())

        self._worker = worker
        self._thread_owner = thread_owner
        self._sleep_duration = sleep_duration

    @staticmethod
    def _is_interactive():
        if bool(getattr(sys, 'ps1', sys.flags.interactive)):
            return True

        try:
            from traitlets.config.application import Application as App
            return App.initialized() and App.instance().interact
        except (ImportError, AttributeError):
            return False

    def stop(self):
        with self._thread_owner.mutex:
            self._thread_owner._is_running = False

    def run(self):
        """
        Runs its worker method.

        This method will be terminated once its parent's is_running
        property turns False.
        """
        while self._thread_owner.is_running():
            if self._worker:
                self._worker()
                time.sleep(self._sleep_duration)

    def acquire(self):
        return self._thread_owner.mutex.acquire()

    def release(self):
        self._thread_owner.mutex.release()

    @property
    def id_(self):
        return self.ident

    @property
    def worker(self):
        return self._worker

    @worker.setter
    def worker(self, obj):
        self._worker = obj

    @property
    def mutex(self):
        return self._thread_owner.mutex


class ComponentBase:
    """
    Is a base class of various data component types.
    """
    def __init__(self, *, buffer=None):
        """
        :param buffer:
        """
        assert buffer

        super().__init__()

        self._buffer = buffer
        self._data = None

    @property
    def data_format(self) -> str:
        """
        str: The type of the data component.
        """
        return self._buffer.data_format

    @property
    def data_format_namespace(self) -> PIXELFORMAT_NAMESPACE_IDS:
        """
        PIXELFORMAT_NAMESPACE_IDS: The data type namespace of the data
        component.
        """
        return self._buffer.data_format

    @property
    def source_id(self) -> int:
        """
        int: The source ID of the data component.
        """
        return self._buffer.source_id

    @property
    def data(self) -> Union[numpy.ndarray, None]:
        """
        Union[numpy.ndarray, None]: The raw image data.
        """
        return self._data


Component = TypeVar('Component', bound=ComponentBase)


class ComponentUnknown(ComponentBase):
    """
    Represents a data component that is classified as
    :const:`PART_DATATYPE_UNKNOWN` by the GenTL Standard.
    """
    def __init__(self):
        #
        super().__init__()


class Component2DImage(ComponentBase):
    """
    Represents a data component that is classified as
    :const:`PART_DATATYPE_2D_IMAGE` by the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer=None, part=None, node_map: Optional[NodeMap] = None,
            ):
        """
        :param buffer:
        :param part:
        :param node_map:
        """
        assert buffer
        assert node_map

        super().__init__(buffer=buffer)

        self._part = part
        self._node_map = node_map
        proxy = Dictionary.get_proxy(symbolic=self.data_format)
        self._nr_components = proxy.nr_components
        self._data = self._to_np_array(proxy)

    @staticmethod
    def _get_nr_bytes(pf_proxy: _PixelFormat, width: int, height: int) -> int:
        nr_bytes = height * width

        if pf_proxy.alignment.is_packed():
            nr_bytes *= pf_proxy.depth_in_byte
            nr_bytes = ceil(nr_bytes)
        else:
            nr_bytes *= pf_proxy.alignment.unpacked_size
            nr_bytes *= pf_proxy.nr_components

        return int(nr_bytes)

    def _to_np_array(self, pf_proxy):
        if self.has_part():
            nr_bytes = self._part.data_size
        else:
            try:
                w = self._buffer.width
            except GenTL_GenericException:
                w = self._node_map.Width.value
            try:
                h = self._buffer.height
            except GenTL_GenericException:
                h = self._node_map.Height.value

            nr_bytes = self._get_nr_bytes(
                pf_proxy=pf_proxy, width=w, height=h)

            try:
                padding_y = self._buffer.padding_y
            except GenTL_GenericException:
                padding_y = 0
            nr_bytes += padding_y

        array = numpy.frombuffer(self._buffer.raw_buffer, count=int(nr_bytes),
                                 dtype='uint8', offset=self.data_offset)

        return pf_proxy.expand(array)

    def represent_pixel_location(self) -> Union[numpy.ndarray, None]:
        """
        Returns a NumPy array that represents the 2D pixel location,
        which is defined by PFNC, of the original image data.

        You may use the returned NumPy array for a calculation to map the
        original image to another format.

        Returns
        -------
        Union[numpy.ndarray, None]
            A NumPy array that represents the 2D pixel location.
        """
        if not self.data:
            return None

        return self._data.reshape(
            self.height + self.y_padding,
            int(self.width * self._nr_components + self.x_padding))

    @property
    def num_components_per_pixel(self) -> float:
        """
        float: The number of data components per pixel.
        """
        return self._nr_components

    def __repr__(self):
        return '{} x {}, {}, {} elements,\n{}'.format(
            self.width, self.height, self.data_format, self.data.size,
            self.data)

    @property
    def width(self) -> int:
        """
        int: The width of the data component in the buffer in number of
        pixels.
        """
        try:
            if self._part:
                value = self._part.width
            else:
                value = self._buffer.width
        except GenTL_GenericException:
            try:
                value = self._node_map.Width.value
            except AttributeError:
                value = 0
        return value

    @property
    def height(self) -> int:
        """
        int: The height of the data component in the buffer in number of
        pixels.
        """
        try:
            if self._part:
                value = self._part.height
            else:
                value = self._buffer.height
                if value == 0:
                    value = self._buffer.delivered_image_height
        except GenTL_GenericException:
            try:
                value = self._node_map.Height.value
            except AttributeError:
                value = 0
        return value

    @property
    def data_format_value(self) -> int:
        """
        int: The data type of the data component as integer value.
        """
        try:
            if self._part:
                value = self._part.data_format
            else:
                value = self._buffer.pixel_format
        except GenTL_GenericException:
            value = self._node_map.PixelFormat.get_int_value()
        assert type(value) is int
        return value

    @property
    def data_format(self) -> str:
        """
        str: The data type of the data component as string.
        """
        return dict_by_ints[self.data_format_value]

    @property
    def delivered_image_height(self) -> int:
        """
        int: The image height of the data component.
        """
        try:
            if self._part:
                value = self._part.delivered_image_height
            else:
                value = self._buffer.delivered_image_height
        except GenTL_GenericException:
            value = 0
        return value

    @property
    def x_offset(self) -> int:
        """
        int: The X offset of the data in the buffer in number of pixels from
        the image origin to handle areas of interest.
        """
        try:
            if self._part:
                value = self._part.x_offset
            else:
                value = self._buffer.offset_x
        except GenTL_GenericException:
            value = self._node_map.OffsetX.value
        return value

    @property
    def y_offset(self) -> int:
        """
        int: The Y offset of the data in the buffer in number of pixels from
        the image origin to handle areas of interest.
        """
        try:
            if self._part:
                value = self._part.y_offset
            else:
                value = self._buffer.offset_y
        except GenTL_GenericException:
            value = self._node_map.OffsetY.value
        return value

    @property
    def x_padding(self) -> int:
        """
        int: The X padding of the data component in the buffer in number of
        pixels.
        """
        try:
            if self._part:
                value = self._part.x_padding
            else:
                value = self._buffer.padding_x
        except GenTL_GenericException:
            value = 0
        return value

    @property
    def y_padding(self) -> int:
        """
        int: The Y padding of the data component in the buffer in number of
        pixels.
        """
        try:
            if self._part:
                value = self._part.y_padding
            else:
                value = self._buffer.padding_y
        except GenTL_GenericException:
            value = 0
        return value

    def has_part(self):
        return self._part is not None

    @property
    def data_offset(self) -> int:
        if self.has_part():
            return self._part.data_offset
        else:
            return 0


class Buffer(Module):
    """
    Is provided by an :class:`ImageAcquire` object when you call its
    :meth:`~harvesters.core.ImageAcquirer.fetch` method. It provides
    you a way to access acquired data and its relevant information.

    Note that it will never be necessary to create this object by yourself
    in general.
    """
    def __init__(self, *, module: _Buffer, node_map: Optional[NodeMap] = None,
                 acquire: Optional[ImageAcquirer] = None):
        """
        Parameters
        ----------
        module : _Buffer
            Set a GenTL Buffer object to be wrapped.
        node_map: NodeMap
            Set a node map which blongs to the owner remote device.

        Raises
        ------
        genicam.gentl.GenericException
            If the buffer contains unusable information.
        """
        super().__init__(module=module, parent=module.parent)
        self._payload = self._build_payload(buffer=module, node_map=node_map)
        self._acquire = acquire

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.queue()

    def __repr__(self):
        return '{}'.format(self.payload.__repr__())

    @property
    def timestamp_ns(self) -> int:
        """
        int: The timestamp. The unit is [ns].
        """
        return self.module.timestamp_ns

    @property
    def timestamp(self) -> int:
        """
        int: The timestamp. The unit is GenTL Producer dependent.
        """
        try:
            timestamp = self.module.timestamp_ns
        except GenTL_GenericException:
            try:
                timestamp = self.module.timestamp
            except GenTL_GenericException:
                timestamp = 0

        return timestamp

    @property
    def timestamp_frequency(self) -> int:
        """
        int: The timestamp tick frequency which is used to represent a
        timestamp. The unit is [Hz].
        """
        frequency = 1000000000  # Hz

        try:
            _ = self.module.timestamp_ns
        except GenTL_GenericException:
            try:
                frequency = self.module.parent.parent.timestamp_frequency
            except GenTL_GenericException:
                try:
                    frequency = self._node_map.GevTimestampTickFrequency.value
                except GenTL_GenericException:
                    pass

        return frequency

    @property
    def payload_type(self):
        """
        PAYLOADTYPE_INFO_IDS: The payload type that the :class:`Buffer`
        object contains.
        """
        return self.module.payload_type

    @property
    def payload(self):
        """
        Payload: A containing object which derives from :class:`PayloadBase`
        class.
        """
        return self._payload

    def queue(self):
        """
        Queues the buffer to prepare for the upcoming image acquisition. Once
        the buffer is queued, the :class:`Buffer` object will be obsolete.
        You'll have nothing to do with it.

        Note that you have to return _the ownership of the fetched buffers to
        the :class:`ImageAcquirer` object before stopping image acquisition
        calling this method because the :class:`ImageAcquirer` object tries
        to clear the self-allocated buffers when it stops image acquisition.
        """
        global _logger

        #
        if _is_logging_buffer:
            _logger.debug('queued: {0}'.format(_family_tree(self.module)))

        self.module.parent.queue_buffer(self.module)

    @staticmethod
    def _build_payload(*, buffer: _Buffer,
                       node_map: Optional[NodeMap] = None):
        """
        Raises
        ------
        genicam.gentl.GenericException
            If the buffer does not provide sufficient information that is
            required to compose a logical payload object.
        """
        assert buffer
        assert node_map

        p_type = buffer.payload_type
        if p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_UNKNOWN:
            payload = PayloadUnknown(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_IMAGE or \
                buffer.payload_type == \
                PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_DATA:
            payload = PayloadImage(buffer=buffer, node_map=node_map)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_RAW_DATA:
            payload = PayloadRawData(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_FILE:
            payload = PayloadFile(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG:
            payload = PayloadJPEG(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG2000:
            payload = PayloadJPEG2000(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_H264:
            payload = PayloadH264(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_ONLY:
            payload = PayloadChunkOnly(buffer=buffer)

        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_MULTI_PART:
            payload = PayloadMultiPart(buffer=buffer, node_map=node_map)

        else:
            info = json.dumps({"payload type": "{}".format(p_type)})
            _logger.warning(
                "unsupported; trying to assume it as an image: {}".format(
                    info))
            try:
                payload = PayloadImage(buffer=buffer, node_map=node_map)
            except (GenTL_GenericException, GenApi_GenericException):
                _logger.error("remedy failed: {}".format(info))
                payload = None

        return payload

    def update_chunk_data(self):
        self._acquire._update_chunk_data(self.module)


class PayloadBase:
    """
    Is a base class of various payload types. The types are defined by the
    GenTL Standard. In general, you should not have to design a class that
    derives from this base class.
    """
    def __init__(self, *, buffer: Buffer):
        """
        :param buffer:
        """
        super().__init__()

        self._buffer = buffer
        self._components = []

    @property
    def payload_type(self) -> PAYLOADTYPE_INFO_IDS:
        """
        PAYLOADTYPE_INFO_IDS: The type of the payload.
        """
        return self._buffer.payload_type

    @staticmethod
    def _build_component(buffer: _Buffer, part=None,
                         node_map: Optional[NodeMap] = None):
        global _logger

        try:
            if part:
                data_format = part.data_format
            else:
                data_format = buffer.pixel_format
        except GenTL_GenericException:
            # As a workaround, we are going to retrive a data format
            # value from the remote device node map; note that there
            # could be a case where the value is not synchronized with
            # the delivered buffer; in addition, note that it:
            if node_map:
                name = node_map.PixelFormat.value
                if name in dict_by_names:
                    data_format = dict_by_names[name]
                else:
                    raise
            else:
                raise

        symbolic = dict_by_ints[data_format]
        if symbolic in component_2d_formats:
            return Component2DImage(
                buffer=buffer, part=part, node_map=node_map
            )

        _logger.warning(
            "unsupported format: \'{}\'".format(symbolic))

        return None

    @property
    def components(self) -> List[Component]:
        """
        List[Component]: A :class:`list` containing objects that derive from
        :class:`ComponentBase` class.
        """
        return self._components


Payload = TypeVar('Payload', bound=PayloadBase)


class PayloadUnknown(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_UNKNOWN`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        """

        :param buffer:
        """
        assert buffer
        super().__init__(buffer=buffer)


class PayloadImage(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_IMAGE` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer,
                 node_map: Optional[NodeMap] = None):
        """

        :param buffer:
        :param node_map:
        """
        super().__init__(buffer=buffer)

        self._components.append(
            self._build_component(
                buffer=buffer, node_map=node_map))

    def __repr__(self):
        return '{}'.format(self.components[0].__repr__())


class PayloadRawData(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_RAW_DATA`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        """
        :param buffer:
        """
        super().__init__(buffer=buffer)


class PayloadFile(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_FILE` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        super().__init__(buffer=buffer)


class PayloadJPEG(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        """
        :param buffer:
        """
        super().__init__(buffer=buffer)


class PayloadJPEG2000(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG2000`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        """
        :param buffer:
        """
        super().__init__(buffer=buffer)


class PayloadH264(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_H264` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        """
        :param buffer:
        """
        super().__init__(buffer=buffer)


class PayloadChunkOnly(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_ONLY`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer):
        super().__init__(buffer=buffer)


class PayloadMultiPart(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_MULTI_PART`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer: _Buffer, node_map: NodeMap):
        """
        :param buffer:
        :param node_map:
        """
        super().__init__(buffer=buffer)

        for i, part in enumerate(self._buffer.parts):
            self._components.append(
                self._build_component(
                    buffer=buffer, part=part, node_map=node_map))

    def __repr__(self):
        ret = ''
        for i, c in enumerate(self.components):
            ret += 'Component {}: {}\n'.format(i, c.__repr__())
        ret = ret[:-1]
        return ret


class Callback:
    """
    Is used as a base class to implement user defined callback behavior.
    """
    def emit(self, context: Optional[object] = None) -> None:
        """
        Is called when a specific condition is met.

        This method is abstract and should be reimplemented in any sub-class.
        """
        raise NotImplementedError


class ImageAcquirer:
    """
    Manages everything you need to acquire images from the connecting device.
    """
    _event = Event()
    _specialized_tl_type = ['U3V', 'GEV']

    _supported_parameters = [
        ParameterKey.ENABLE_CLEANING_UP_INTERMEDIATE_FILES,
        ParameterKey.ENABLE_AUTO_CHUNK_DATA_UPDATE,
        ParameterKey.REMOTE_DEVICE_SOURCE_XML_FILE_PATH,
        ParameterKey.THREAD_SLEEP_PERIOD,
        ParameterKey.TIMEOUT_PERIOD_ON_UPDATE_EVENT_DATA_CALL,
        ParameterKey.TIMEOUT_PERIOD_ON_FETCH_CALL,
        ParameterKey.NUM_BUFFERS_FOR_FETCH_CALL,
    ]

    class Events(IntEnum):
        TURNED_OBSOLETE = 0,
        NEW_BUFFER_AVAILABLE = 1,
        RETURN_ALL_BORROWED_BUFFERS = 2,
        READY_TO_STOP_ACQUISITION = 3,
        INCOMPLETE_BUFFER = 4,

    def _create_acquisition_thread(self) -> _ImageAcquisitionThread:
        return _ImageAcquisitionThread(image_acquire=self)

    def __init__(self, *, device=None, config: Optional[ParameterSet] = None, profiler=None, file_dict=None):
        """

        Parameters
        ----------
        device : Device_
        sleep_duration : float
        file_path : str
            Set a path to camera description file which you want to load on
            the target node map instead of the one which the device declares.
        update_chunk_automatically : bool
            Set :const:`True` if you want to let the chunk data being updated
            when a buffer is newly fetched. :const:`False` means you will
            explicitly update the chunk data by yourself when needed.
        file_dict : Dict[str, bytes]
        """
        global _logger
        ParameterSet.check(config, self._supported_parameters)
        super().__init__()

        self._is_valid = True
        self._file_dict = file_dict
        self._clean_up = ParameterSet.get(ParameterKey.ENABLE_CLEANING_UP_INTERMEDIATE_FILES, True, config)
        self._enable_auto_chunk_data_update = ParameterSet.get(ParameterKey.ENABLE_AUTO_CHUNK_DATA_UPDATE, True, config)
        self._has_attached_chunk = False

        env_var = 'HARVESTERS_XML_FILE_DIR'
        if env_var in os.environ:
            self._xml_dir = os.getenv(env_var)
        else:
            self._xml_dir = None

        self._device = device

        file_path = ParameterSet.get(ParameterKey.REMOTE_DEVICE_SOURCE_XML_FILE_PATH, None, config)

        self._remote_device = RemoteDevice(
            module=device.module, parent=device, file_path=file_path,
            file_dict=file_dict, do_clean_up=self._clean_up,
            xml_dir_to_store=self._xml_dir)
        self._interface = device.parent
        self._system = self._interface.parent

        if self._remote_device:
            assert self._remote_device.node_map

        self._data_streams = []
        self._event_new_buffer_managers = []

        self._create_ds_at_connection = True
        if self._create_ds_at_connection:
            self._setup_data_streams()

        self._profiler = profiler

        self._num_buffers_to_hold = 1
        self._queue = Queue(maxsize=self._num_buffers_to_hold)

        self._sleep_duration = ParameterSet.get(ParameterKey.THREAD_SLEEP_PERIOD, _sleep_duration_default, config)
        self._thread_image_acquisition = self._create_acquisition_thread()

        self._threads = []
        self._threads.append(self._thread_image_acquisition)

        self._sigint_handler = None
        if current_thread() is main_thread():
            self._sigint_handler = _SignalHandler(
                event=self._event, subject=self)
            signal.signal(signal.SIGINT, self._sigint_handler)
            _logger.debug('created: {0}'.format(self._sigint_handler))

        self._num_images_to_acquire = 0

        self._timeout_on_internal_fetch_call = ParameterSet.get(ParameterKey.TIMEOUT_PERIOD_ON_UPDATE_EVENT_DATA_CALL, 1, config)  # ms
        self._timeout_on_client_fetch_call = ParameterSet.get(ParameterKey.TIMEOUT_PERIOD_ON_FETCH_CALL, 0.01, config)  # s

        self._statistics = Statistics()
        self._announced_buffers = []

        self._has_acquired_1st_image = False
        self._is_acquiring = False

        num_buffers_default = ParameterSet.get(ParameterKey.NUM_BUFFERS_FOR_FETCH_CALL, 3, config)
        try:
            self._min_num_buffers = self._data_streams[0].buffer_announce_min
        except GenTL_GenericException as e:
            # In general, a GenTL Producer should not raise the
            # InvalidParameterException to the inquiry for
            # STREAM_INFO_BUF_ANNOUNCE_MIN because it is totally legal
            # but we have observed a fact that there is at least one on
            # the market. As a workaround we involve this try-except block:
            _logger.warning(e, exc_info=True)
            self._min_num_buffers = num_buffers_default
            self._num_buffers = num_buffers_default
        else:
            self._num_buffers = max(
                num_buffers_default, self._min_num_buffers)

        self._chunk_adapter = self._get_chunk_adapter(
            device=self.device, node_map=self.remote_device.node_map)

        self._finalizer = weakref.finalize(self, self.destroy)

        self._supported_events = [
            self.Events.TURNED_OBSOLETE,
            self.Events.RETURN_ALL_BORROWED_BUFFERS,
            self.Events.READY_TO_STOP_ACQUISITION,
            self.Events.NEW_BUFFER_AVAILABLE,
            self.Events.INCOMPLETE_BUFFER]
        self._callback_dict = dict()
        for event in self._supported_events:
            self._callback_dict[event] = None

    def is_valid(self) -> bool:
        """
        bool: Returns :const:`False` and it means the object has been
        obsolete and there is nothing to do for you. Just leave the object
        and start working with another newly created object.

        The :meth:`Harvester.update` method call on its parent
        :class:`Harvester` object make its owning :class:`ImageAcquirer`
        objects obsolete as the available device information is completely
        reconstructed.
        """
        return self._is_valid

    def _emit_callbacks(self, event: Events) -> None:
        global _logger

        callbacks = self._callback_dict[event]
        if isinstance(callbacks, Iterable):
            for callback in callbacks:
                self._emit_callback(callback)
        else:
            callback = callbacks
            self._emit_callback(callback)

    def _emit_callback(
            self,
            callback: Optional[Union[Callback, List[Callback]]]) -> None:
        if callback:
            if isinstance(callback, Callback):
                _logger.debug("going to emit: {0}".format(callback))
                callback.emit(context=self)
            else:
                raise TypeError

    def _check_validity(self, event: Events):
        if event not in self._supported_events:
            raise ValueError

    def add_callback(self, event: Events, callback: Callback):
        self._check_validity(event)
        assert callback
        self._callback_dict[event] = callback

    def remove_callback(self, event: Events):
        self._check_validity(event)
        self._callback_dict[event] = None

    def remove_callbacks(self):
        for event in self._supported_events:
            self._callback_dict[event] = None

    @property
    def supported_events(self):
        return self._supported_events

    @staticmethod
    def _get_chunk_adapter(
            *, device=None, node_map: Optional[NodeMap] = None):
        if device.tl_type == 'U3V':
            return ChunkAdapterU3V(node_map)
        elif device.tl_type == 'GEV':
            return ChunkAdapterGEV(node_map)
        else:
            return ChunkAdapterGeneric(node_map)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._finalizer()

    def _release_remote_device(self):
        if self.remote_device.node_map:
            self.remote_device.node_map.disconnect()

        if self._chunk_adapter:
            self._chunk_adapter = None

        if self._device.is_open():
            self._device.close()

    def destroy(self) -> None:
        """
        Destroys itself; releases all preserved external resources such as
        buffers or the connected remote device.

        Note that once the destroy method is called on the object then the
        object will immediately turn obsolete and there will never be any
        way to make the object usable. Just throw the object away and
        create another object by calling
        :meth:`Harvester.create_image_acquire` method.
        """
        global _logger

        if not self._is_valid:
            return

        self.stop()

        if self._chunk_adapter:
            self._chunk_adapter = None

        self._release_data_streams()
        self._release_remote_device()

        self._remote_device = None
        self._device = None
        self._interface = None
        self._system = None

        self._is_valid = False

        if self._profiler:
            self._profiler.print_diff()

        _logger.info('released resources: {}'.format(self))
        self._emit_callbacks(self.Events.TURNED_OBSOLETE)

    @property
    def num_buffers(self) -> int:
        """
        int: The number of buffers that is prepared for the image acquisition
        process. The buffers will be announced to the target GenTL Producer.
        """
        return self._num_buffers

    @num_buffers.setter
    def num_buffers(self, value: int = 1):
        if value >= self._min_num_buffers:
            self._num_buffers = value
        else:
            raise ValueError(
                'The number of buffers must be '
                'greater than or equal to {}'.format(self._min_num_buffers))

    @property
    def sleep_duration(self) -> float:
        """
        float: The duration that lets the image acquisition thread sleeps at
        every execution. The unit is [ms].
        """
        return self._sleep_duration

    @property
    def min_num_buffers(self) -> int:
        """
        int: The minimum number of the buffers for image acquisition. You
        have to set a value to :meth:`num_buffers` so that is greater than or
        equal to this.
        """
        return self._min_num_buffers

    @property
    def num_filled_buffers_to_hold(self) -> int:
        """
        int: The number of buffers that is used for a case where the image
        acquisition process runs in the background. You will fetch buffers
        from the buffers when you call the :meth:`fetch` method in a
        case you started the image acquisition passing :const:`True` to
        :data:`run_as_thread` of the :meth:`start` method.
        """
        return self._num_buffers_to_hold

    @num_filled_buffers_to_hold.setter
    def num_filled_buffers_to_hold(self, value: int = 1):
        global _logger

        if value > 0:
            self._num_buffers_to_hold = value

            buffers = []
            while not self._queue.empty():
                buffers.append(self._queue.get_nowait())

            self._queue = Queue(maxsize=self._num_buffers_to_hold)

            while len(buffers) > 0:
                try:
                    self._queue.put(buffers.pop(0))
                except Full as e:
                    _logger.debug(e, exc_info=True)
                    buffer = buffers.pop(0)
                    buffer.parent.queue_buffer(buffer)

        else:
            raise ValueError(
                'The number of filled buffers to hold must be > 0.')

    @property
    def num_holding_filled_buffers(self) -> int:
        """
        int: The number of available buffers, i.e., the buffers that contain
        images.
        """
        return self._queue.qsize()

    @property
    def data_streams(self) -> List[DataStream]:
        """
        List[DataStream]: A list of GenTL :class:`DataStream` objects that the
        :class:`ImageAcquire` object is working with.
        """
        return self._data_streams

    @property
    def remote_device(self) -> RemoteDevice:
        """
        RemoteDevice: The remote GenTL :class:`Device` object, typically a
        camera, that the :class:`ImageAcquire` object is working with.
        """
        return self._remote_device

    @property
    def device(self) -> Device:
        """
        Device: The local GenTL :class:`Device` proxy object that the
        :class:`ImageAcquire` object is working with.
        """
        return self._device

    @property
    def interface(self) -> Interface:
        """
        Interface: The GenTL :class:`Interface` object that the
        :class:`ImageAcquire` object is working with.
        """
        return self._interface

    @property
    def system(self) -> System:
        """
        System: The GenTL :class:`System` object that the
        :class:`ImageAcquire` object is working with.
        """
        return self._system

    def is_acquiring(self) -> bool:
        """
        Returns the truth value of a proposition: It's acquiring images.

        Returns
        -------
        bool
            :const:`True` if it's acquiring images. Otherwise :const:`False`.
        """
        return self._is_acquiring

    def is_armed(self) -> bool:
        """
        Returns the arm status on image acquisition.

        Returns
        -------
            :const:`True` if it's been armed for image acquisition; otherwise,
            :const:`False`.
        """
        if not self.is_acquiring() or \
                self.is_acquiring() and self._num_images_to_acquire == 0:
            return False
        else:
            return True

    @property
    def timeout_on_client_fetch_call(self) -> float:
        """
        float: It is used to define the timeout duration on a single fetch
        method calL. The unit is [s].
        """
        return self._timeout_on_client_fetch_call

    @timeout_on_client_fetch_call.setter
    def timeout_on_client_fetch_call(self, value: float):
        client = value
        internal = float(self.timeout_on_internal_fetch_call / 1000)
        info = json.dumps({"internal": internal, "client": client})
        if isclose(client, internal):
            _logger.warning("may cause timeout: {}".format(info))
        else:
            if client < internal:
                _logger.warning("may cause timeout: {}".format(info))
        self._timeout_on_client_fetch_call = value

    @property
    def timeout_on_internal_fetch_call(self) -> int:
        """
        int: It is used to define the timeout duration on an internal single
        GenTL fetch calL. The unit is [ms].
        """
        return self._timeout_on_internal_fetch_call

    @timeout_on_internal_fetch_call.setter
    def timeout_on_internal_fetch_call(self, value):
        internal = float(value)
        client = self.timeout_on_client_fetch_call * 1000.
        info = json.dumps({"internal": internal, "client": client})
        if isclose(internal, client):
            _logger.warning("may cause timeout: {}".format(info))
        else:
            if internal > client:
                _logger.warning("may cause timeout: {}".format(info))
        self._timeout_on_internal_fetch_call = value

    @property
    def timeout_for_image_acquisition(self) -> int:
        """
        Deprecated: Use timeout_on_internal_fetch_call instead.
        """
        return self._timeout_on_internal_fetch_call

    @timeout_for_image_acquisition.setter
    def timeout_for_image_acquisition(self, ms):
        self._timeout_on_internal_fetch_call = ms

    @property
    def thread_image_acquisition(self) -> ThreadBase:
        """
        The thread object that runs image acquisition.
        """
        return self._thread_image_acquisition

    @thread_image_acquisition.setter
    def thread_image_acquisition(self, obj):
        self._thread_image_acquisition = obj
        self._thread_image_acquisition.worker = self.worker_image_acquisition

    @property
    def statistics(self) -> Statistics:
        """
        Statistics: The statistics about image acquisition.
        """
        return self._statistics

    def _setup_data_streams(self, file_dict: Dict[str, bytes] = None):
        global _logger

        for i, stream_id in enumerate(self._device.data_stream_ids):
            _data_stream = self._device.create_data_stream()

            try:
                _data_stream.open(stream_id)
            except GenTL_GenericException as e:
                _logger.error(e, exc_info=True)
            else:
                _logger.debug(
                    'opened: {0}'.format(_family_tree(_data_stream)))

            self._data_streams.append(DataStream(module=_data_stream))

            event_token = self._data_streams[i].register_event(
                EVENT_TYPE_LIST.EVENT_NEW_BUFFER)

            self._event_new_buffer_managers.append(
                EventManagerNewBuffer(event_token))

    def start_acquisition(self, run_in_background: bool = False) -> None:
        """
        .. deprecated:: 1.3
            :meth:`start_acquisition` will be removed in 1.4.0, it is replaced
            by :meth:`start`.
        """
        _deprecated(self.start_acquisition, self.start)
        self.start(run_as_thread=run_in_background)

    def start(self, *, run_as_thread: bool = False) -> None:
        """
        Starts image acquisition process.

        Parameters
        ----------
        run_as_thread : bool
            Set :const:`True` if you want to let the ImageAcquire object keep
            acquiring images in the background and the images you get calling
            :meth:`fetch` method will be from the :class:`ImageAcquirer`.
            Otherwise, the images will directly come from the target GenTL
            Producer.
        """
        global _logger

        if not self.is_acquiring():
            self._num_images_to_acquire = 0

        # Refill the number of images to be acquired if needed:
        if self._num_images_to_acquire == 0:
            # In this case, the all images have been acquired from the
            # previous session; now we refill the number of the images
            # to acquire in the next session:
            try:
                acq_mode = self.remote_device.node_map.AcquisitionMode.value
            except GenTL_GenericException as e:
                num_images_to_acquire = -1
                _logger.warning(e, exc_info=True)
            else:
                if acq_mode == 'Continuous':
                    num_images_to_acquire = -1
                elif acq_mode == 'SingleFrame':
                    num_images_to_acquire = 1
                elif acq_mode == 'MultiFrame':
                    num_images_to_acquire = \
                        self.remote_device.node_map.AcquisitionFrameCount.value
                else:
                    num_images_to_acquire = -1

            self._num_images_to_acquire = num_images_to_acquire

        if not self.is_armed():
            # In this case, we have not armed our GenTL Producer yet for
            # the coming image acquisition; let's arm it:

            if not self._create_ds_at_connection:
                self._setup_data_streams(file_dict=self._file_dict)

            for ds in self._data_streams:
                if ds.defines_payload_size():
                    buffer_size = ds.payload_size
                else:
                    buffer_size = self.remote_device.node_map.PayloadSize.value

                num_required_buffers = self._num_buffers
                try:
                    num_buffers = ds.buffer_announce_min
                    if num_buffers < num_required_buffers:
                        num_buffers = num_required_buffers
                except GenTL_GenericException as e:
                    num_buffers = num_required_buffers
                    _logger.warning(e, exc_info=True)

                num_buffers = max(num_buffers, self._num_images_to_acquire)

                raw_buffers = self._create_raw_buffers(num_buffers, buffer_size)
                buffer_tokens = self._create_buffer_tokens(raw_buffers)
                self._announced_buffers = self._announce_buffers(
                    data_stream=ds, _buffer_tokens=buffer_tokens)
                self._queue_announced_buffers(
                    data_stream=ds, buffers=self._announced_buffers)

                try:
                    self.remote_device.node_map.TLParamsLocked.value = 1
                except GenTL_GenericException:
                    # SFNC < 2.0
                    pass

                ds.start_acquisition(
                    ACQ_START_FLAGS_LIST.ACQ_START_FLAGS_DEFAULT, -1)

            self._has_attached_chunk = False
            self._is_acquiring = True

            if run_as_thread:
                if self.thread_image_acquisition:
                    self.thread_image_acquisition.start()

        _logger.info('started acquisition: {0}'.format(self))

        self.remote_device.node_map.AcquisitionStart.execute()
        _logger.debug('started streaming: {0}'.format(
                _family_tree(self._device.module)))

        if self._profiler:
            self._profiler.print_diff()

    def worker_image_acquisition(self) -> None:
        """
        The worker method of the image acquisition task.

        :return: None
        """
        global _logger

        queue = self._queue

        for manager in self._event_new_buffer_managers:
            buffer = self._fetch(manager=manager,
                                 timeout_on_client_fetch_call=self.timeout_on_client_fetch_call)
            if buffer:
                with MutexLocker(self.thread_image_acquisition):
                    if not self._is_acquiring:
                        return
                    if queue.full():
                        _buffer = queue.get()
                        _buffer.parent.queue_buffer(_buffer)
                    queue.put(buffer)
                self._emit_callbacks(self.Events.NEW_BUFFER_AVAILABLE)

    def _update_chunk_data(self, buffer: _Buffer):
        global _logger

        try:
            if not buffer.is_containing_chunk_data():
                return
        except GenTL_GenericException:
            try:
                if buffer.num_chunks == 0:
                    return
            except GenTL_GenericException:
                if _is_logging_buffer:
                    _logger.warning(
                        'no way to check chunk availability: {0}'.format(
                            _family_tree(buffer)))
                    return
            else:
                if _is_logging_buffer:
                    _logger.debug('contains chunk data: {0}'.format(
                        _family_tree(buffer)))

        if buffer.tl_type not in self._specialized_tl_type:
            try:
                self._chunk_adapter.attach_buffer(
                    buffer.raw_buffer,
                    buffer.chunk_data_info_list)
            except GenTL_GenericException as e:
                _logger.error(e, exc_info=True)
        else:
            try:
                size = buffer.delivered_chunk_payload_size
            except GenTL_GenericException:
                try:
                    size = buffer.size_filled
                except GenTL_GenericException:
                    size = len(buffer.raw_buffer)

            if self._has_attached_chunk:
                self._chunk_adapter.update_buffer(buffer.raw_buffer)
                action = 'updated'
            else:
                self._chunk_adapter.attach_buffer(buffer.raw_buffer[:size])
                self._has_attached_chunk = True
                action = 'attached'

            if _is_logging_buffer:
                _logger.debug('chunk data: {}, {}'.format(
                    action, _family_tree(buffer)))

    def try_fetch(self, *, timeout: float = 0,
                  is_raw: bool = False) -> Union[Buffer, _Buffer, None]:
        """
        Unlike the fetch method, the try_fetch method gives up and
        returns None if no complete buffer was acquired during the defined
        period.

        Parameters
        ----------
        timeout : float
            Set the period that defines the expiration for an available
            buffer delivery; if no buffer is fetched within the period
            then None will be returned. The unit is [s].

        is_raw : bool
            Set :const:`True` if you need a raw GenTL Buffer module; note
            that you'll have to manipulate the object by yourself.

        Returns
        -------
        Union[Buffer, Buffer_, None]
            A buffer if it is complete; otherwise None.
        """
        buffer = self._fetch(manager=self._event_new_buffer_managers[0],
                             timeout_on_client_fetch_call=timeout,
                             throw_except=False)

        buffer = self._finalize_fetching_process(buffer, is_raw)

        return buffer

    def _fetch(self, *, manager: EventManagerNewBuffer,
               timeout_on_client_fetch_call: float = 0,
               throw_except: bool = False) -> Union[Buffer, _Buffer, None]:
        global _logger

        assert manager

        buffer = None
        watch_timeout = True if timeout_on_client_fetch_call > 0 else False
        base = time.time()

        while not buffer:
            if watch_timeout:
                elapsed = time.time() - base
                if elapsed > timeout_on_client_fetch_call:
                    if _is_logging_buffer:
                        _logger.debug(
                            'timeout: elapsed {0} sec.'.format(
                                timeout_on_client_fetch_call))
                    if throw_except:
                        raise TimeoutException
                    else:
                        return None

            try:
                manager.update_event_data(self.timeout_on_internal_fetch_call)
            except TimeoutException:
                continue
            except GenTL_GenericException as e:
                _logger.error(e, exc_info=True)
                raise
            else:
                context = None
                frame_id = None
                try:
                    is_complete = manager.buffer.is_complete()
                    if _is_logging_buffer:
                        context = manager.buffer.context
                        frame_id = manager.buffer.frame_id
                except GenTL_GenericException:
                    is_complete = False

                if is_complete:
                    self._update_num_images_to_acquire()
                    self._update_statistics(manager.buffer)
                    buffer = manager.buffer
                    if _is_logging_buffer:
                        _logger.debug(
                            'fetched: {0} (#{1}); {2}'.format(
                                context, frame_id,
                                _family_tree(manager.buffer)))
                else:
                    _logger.warning(
                        'incomplete or not available; discarded: {}'.format(
                            _family_tree(manager.buffer)))

                    ds = manager.buffer.parent
                    ds.queue_buffer(manager.buffer)
                    self._emit_callbacks(self.Events.INCOMPLETE_BUFFER)
                    return None

        return buffer

    def _try_fetch_from_queue(
            self, *, is_raw: bool = False) -> Union[Buffer, _Buffer, None]:
        with MutexLocker(self.thread_image_acquisition):
            try:
                raw_buffer = self._queue.get(block=False)
                return self._finalize_fetching_process(raw_buffer, is_raw)
            except Empty:
                return None

    def _finalize_fetching_process(
            self, raw_buffer: _Buffer, is_raw: bool) -> Union[Buffer, _Buffer, None]:
        if not raw_buffer:
            return None

        if self._enable_auto_chunk_data_update:
            self._update_chunk_data(buffer=raw_buffer)

        if is_raw:
            return raw_buffer

        try:
            buffer = Buffer(module=raw_buffer,
                            node_map=self.remote_device.node_map,
                            acquire=self)
        except GenTL_GenericException:
            family_tree = _family_tree(raw_buffer)
            _logger.warning(
                'information not available; discarded: {}'.format(
                    family_tree))
            raw_buffer.parent.queue_buffer(raw_buffer)
            return None
        else:
            return buffer

    def fetch_buffer(self, *, timeout: float = 0, is_raw: bool = False,
                     cycle_s: float = None) -> Buffer:
        """
        .. deprecated:: 1.3
            :meth:`fetch_buffer` will be removed in 1.4.0, it is replaced
            by :meth:`fetch`.
        """
        _deprecated(self.fetch_buffer, self.fetch)
        return self.fetch(timeout=timeout, is_raw=is_raw, cycle_s=cycle_s)

    def fetch(self, *, timeout: float = 0, is_raw: bool = False,
                     cycle_s: float = None) -> Union[Buffer, _Buffer, None]:
        """
        Fetches an available :class:`Buffer` object that has been filled up
        with a single image and returns it.

        Parameters
        ----------
        timeout : float
            Set the period that defines the expiration for an available
            buffer delivery; if no buffer is fetched within the period
            then TimeoutException will be raised. The unit is [s].

        is_raw : bool
            Set :const:`True` if you need a raw GenTL Buffer module; note
            that you'll have to manipulate the object by yourself.

        cycle_s : float
            Set the cycle that defines how frequently check if a buffer is
            available. The unit is [s].

        Returns
        -------
        Union[Buffer, Buffer_, None]
            A buffer object if the resource is complete; otherwise None.
        """

        buffer = None
        while not buffer:
            if self.thread_image_acquisition and \
                    self.thread_image_acquisition.is_running():
                buffer = self._try_fetch_from_queue(is_raw=is_raw)
                if not buffer:
                    time.sleep(cycle_s if cycle_s else 0.0001)
            else:
                raw_buffer = self._fetch(
                    manager=self._event_new_buffer_managers[0],
                    timeout_on_client_fetch_call=timeout, throw_except=True)
                buffer = self._finalize_fetching_process(raw_buffer, is_raw)

        return buffer

    def _update_num_images_to_acquire(self) -> None:
        if self._num_images_to_acquire >= 1:
            self._num_images_to_acquire -= 1

        if self._num_images_to_acquire == 0:
            self._emit_callbacks(self.Events.READY_TO_STOP_ACQUISITION)

    def _update_statistics(self, buffer) -> None:
        assert buffer
        self._statistics.increment_num_images()
        self._statistics.update_timestamp(buffer)

    def _create_raw_buffers(
            self, num_buffers: int = 0, size: int = 0) -> List[bytes]:
        assert num_buffers >= 0
        assert size >= 0

        raw_buffers = []
        for _ in range(num_buffers):
            _logger.debug(
                "allocated: {0} bytes by {1}".format(size, self))
            raw_buffers.append(bytes(size))

        return raw_buffers

    @staticmethod
    def _create_buffer_tokens(raw_buffers: List[bytes] = None):
        assert raw_buffers

        _buffer_tokens = []
        for i, buffer in enumerate(raw_buffers):
            _buffer_tokens.append(
                BufferToken(buffer, i))

        return _buffer_tokens

    def _announce_buffers(
            self, data_stream: DataStream = None,
            _buffer_tokens: List[BufferToken] = None) -> List[Buffer]:
        global _logger

        assert data_stream

        announced_buffers = []
        for token in _buffer_tokens:
            announced_buffer = data_stream.announce_buffer(token)
            announced_buffers.append(announced_buffer)
            _logger.debug(
                'announced: {0}'.format(_family_tree(announced_buffer)))

        return announced_buffers

    def _queue_announced_buffers(
            self, data_stream: Optional[DataStream] = None,
            buffers: Optional[List[Buffer]] = None) -> None:
        global _logger

        assert data_stream

        for buffer in buffers:
            data_stream.queue_buffer(buffer)
            _logger.debug('queued: {0}'.format(_family_tree(buffer)))

    def stop_acquisition(self) -> None:
        """
        .. deprecated:: 1.3
            :meth:`stop_acquisition` will be removed in 1.4.0, it is replaced
            by :meth:`stop`.
        """
        _deprecated(self.stop_acquisition, self.stop)
        self.stop()

    def stop(self) -> None:
        """
        Stops image acquisition process.
        """
        global _logger

        if self.is_acquiring():
            self._is_acquiring = False

            if self.thread_image_acquisition.is_running():
                self.thread_image_acquisition.stop()
                self.thread_image_acquisition.join()

            with MutexLocker(self.thread_image_acquisition):
                try:
                    self.remote_device.node_map.AcquisitionStop.execute()
                except GenApi_GenericException as e:
                    _logger.warning(e, exc_info=True)
                else:
                    _logger.debug('stopped streaming: {}'.format(
                        _family_tree(self._device.module)))

                try:
                    self.remote_device.node_map.TLParamsLocked.value = 0
                except GenApi_GenericException:
                    pass

                for data_stream in self._data_streams:
                    try:
                        data_stream.stop_acquisition(
                            ACQ_STOP_FLAGS_LIST.ACQ_STOP_FLAGS_KILL
                        )
                    except GenTL_GenericException as e:
                        _logger.warning(e, exc_info=True)

                    self._flush_buffers(data_stream)

                for event_manager in self._event_new_buffer_managers:
                    event_manager.flush_event_queue()

                if self._create_ds_at_connection:
                    self._release_buffers()
                else:
                    self._release_data_streams()

            self._has_acquired_1st_image = False
            self._chunk_adapter.detach_buffer()
            _logger.info('stopped acquisition: {}'.format(self))

        if self._profiler:
            self._profiler.print_diff()

    def _flush_buffers(self, data_stream: DataStream) -> None:
        self._emit_callbacks(self.Events.RETURN_ALL_BORROWED_BUFFERS)
        data_stream.flush_buffer_queue(
            ACQ_QUEUE_TYPE_LIST.ACQ_QUEUE_ALL_DISCARD)

    def _release_data_streams(self) -> None:
        global _logger

        self._release_buffers()

        for data_stream in self._data_streams:
            if data_stream and data_stream.is_open():
                name = _family_tree(data_stream.module)
                data_stream.close()
                _logger.debug('closed: {}'.format(name))

        self._data_streams.clear()
        self._event_new_buffer_managers.clear()

    def _release_buffers(self) -> None:
        global _logger

        for data_stream in self._data_streams:
            if data_stream.is_open():
                for buffer in self._announced_buffers:
                    name = _family_tree(buffer)
                    _ = data_stream.revoke_buffer(buffer)
                    _logger.debug('revoked: {0}'.format(name))

        self._announced_buffers.clear()

        while not self._queue.empty():
            _ = self._queue.get_nowait()


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


class _CallbackDestroyImageAcquirer(Callback):
    def __init__(self, harvester):
        self._harvester = harvester

    def emit(self, context: Optional[ImageAcquirer] = None) -> None:
        context.destroy()
        if context in self._harvester.image_acquirers:
            self._harvester.image_acquirers.remove(context)


class Harvester:
    """
    Is the class that works for you as Harvester Core. Everything begins with
    this class.
    """
    #
    _supported_parameters = [
        ParameterKey.LOGGER,
        ParameterKey.ENABLE_CLEANING_UP_INTERMEDIATE_FILES,
        ParameterKey.TIMEOUT_PERIOD_ON_MODULE_ENUMERATION,
        ParameterKey._ENABLE_PROFILE,
    ]

    def __init__(self, *, config: Optional[ParameterSet] = None):
        """
        Parameters
        ----------
        config: Optional[ParameterSet] = None
            Set a parameter set. Possible parameters are:

                - :const:`~harvesters.core.ParameterKey.Logger`,
                - :const:`~harvesters.core.ParameterKey.EnableCleaningUpIntermediateFiles`, and
                - :const:`~harvesters.core.ParameterKey.TimeOutPeriodOnModuleEnumeration`.
        """
        global _logger

        ParameterSet.check(config, self._supported_parameters)

        logger = ParameterSet.get(ParameterKey.LOGGER, None, config)
        _logger = logger or _logger

        super().__init__()

        self._cti_files = []
        self._producers = []
        self._systems = []
        self._ifaces = []
        self._device_info_list = []
        self._ias = []
        self._has_revised_device_list = False
        self._clean_up = \
            ParameterSet.get(ParameterKey.ENABLE_CLEANING_UP_INTERMEDIATE_FILES, True, config)

        self._timeout_period_on_module_enumeration = \
            ParameterSet.get(ParameterKey.TIMEOUT_PERIOD_ON_MODULE_ENUMERATION, 1000, config)  # ms

        if ParameterSet.get(ParameterKey._ENABLE_PROFILE, False, config):
            from harvesters._private.core.helper.profiler import Profiler
            self._profiler = Profiler()
            self._profiler.print_diff()
        else:
            self._profiler = None

        self._finalizer = weakref.finalize(self, self._reset)
        _logger.info('created: {0}'.format(self))

    @property
    def image_acquirers(self) -> List[ImageAcquirer]:
        """
        List[ImageAcquirer]: The image acquirer objects that belong to the
        harvester object.
        """
        return self._ias

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._finalizer()

    def reset(self) -> None:
        """
        Resets the Harvester object to the initial state.
        """
        self._finalizer()

    @property
    def cti_files(self):
        """
        .. deprecated:: 1.3
            :attr:`cti_files` will be removed in 1.4.0, it is replaced
            by :attr:`files`.
        """
        _deprecated('cti_files', 'files')
        return self.files

    @property
    def files(self) -> List[str]:
        """
        List[str]: A list of associative CTI files.
        """
        return self._cti_files

    @property
    def device_info_list(self) -> List[DeviceInfo]:
        """
        List[DeviceInfo]: A list of available device information.
        """
        return self._device_info_list

    @property
    def timeout_for_update(self) -> int:
        """
        int: The duration that is used as the time limit for the device
        enumeration process. The unit is [ms].
        """
        return self._timeout_period_on_module_enumeration

    @timeout_for_update.setter
    def timeout_for_update(self, ms: Optional[int] = 0) -> None:
        self._timeout_period_on_module_enumeration = ms

    @property
    def has_revised_device_info_list(self) -> bool:
        return self._has_revised_device_list

    @has_revised_device_info_list.setter
    def has_revised_device_info_list(self, value):
        self._has_revised_device_list = value

    def create(
            self,
            search_key: Optional[Union[int, Dict[str, str], DeviceInfo]] = None,
            *, config: Optional[ParameterSet] = None) -> ImageAcquirer:
        """
        Creates an image acquirer that is mapped to the specified remote
        device.

        Parameters
        ----------
        search_key: Optional[Union[int, Dict[str, str], DeviceInfo]] = None
            Set either an list index (int), a dictionary that specifies
            device information properties (Dict[str, str]), or a
            device information object (DeviceInfo) to specify a target
            device to be mapped to the ImageAcquirer object to be created.

        config: Optional[ParameterSet] = None
            Set a parameter set. Possible parameters are:

                - :const:`~harvesters.core.ParameterKey.EnableCleaningUpIntermediateFiles`,
                - :const:`~harvesters.core.ParameterKey.EnableAutoChunkDataUpdate`,
                - :const:`~harvesters.core.ParameterKey.RemoveDeviceSourceXmlPath`,
                - :const:`~harvesters.core.ParameterKey.ThreadSleepPeriod`,
                - :const:`~harvesters.core.ParameterKey.TimeOutPeriodOnUpdateEventDataCall`,
                - :const:`~harvesters.core.ParameterKey.TimeOutPeriodOnFetchCall`, and
                - :const:`~harvesters.core.ParameterKey.NumBuffersOnGenTLProducer`.

        Returns
        -------
        ImageAcquirer
            An ImageAcquire object that is mapped to the specified remote
            device.

        Attention
        ---------
        Note that you need to explicitly destroy the object to ensure that
        the mapped device ownership is released.

        """

        def compose_message(status: int, solution: int) -> str:
            status_dict = {
                0: "no device available",
                1: "no device found",
                2: "multiple devices found",
                3: "undefined search key given"
            }
            solution_dict = {
                0: "check the system setup",
                1: "provide sufficient search key",
                2: "provide valid device information",
                3: "provide valid search key",
            }
            return ": ".join([status_dict.get(status),
                              solution_dict.get(solution)])

        if type(search_key) is int:
            raw_device = self.device_info_list[search_key].create_device()
        elif type(search_key) is DeviceInfo:
            if search_key in self.device_info_list:
                raw_device = search_key.create_device()
            else:
                raise ValueError(1, 2)
        elif type(search_key) is dict:
            candidate_devices = self.device_info_list.copy()
            for key in search_key.keys():
                value = search_key.get(key)
                if value:
                    to_be_dropped = []
                    for candidate in candidate_devices:
                        try:
                            if value != getattr(candidate, key, None):
                                to_be_dropped.append(candidate)
                        except GenTL_GenericException as e:
                            _logger.debug(e, exc_info=True)
                            continue
                    for candidate in to_be_dropped:
                        candidate_devices.remove(candidate)

            num_candidates = len(candidate_devices)
            if num_candidates > 1:
                raise ValueError(compose_message(2, 1))
            elif num_candidates == 0:
                raise ValueError(compose_message(1, 1))
            else:
                raw_device = candidate_devices[0].create_device()
        elif search_key is None:
            if len(self.device_info_list) > 0:
                raw_device = self.device_info_list[0].create_device()
            else:
                raise ValueError(compose_message(0, 0))
        else:
            raise ValueError(compose_message(3, 3))

        return self._create_acquirer(raw_device=raw_device, config=config)

    def _create_acquirer(self, *, raw_device: Device,
                         config: Optional[ParameterSet] = None,
                         file_dict=None):
        privilege = ParameterSet.get(ParameterKey.DEVICE_OWNERSHIP_PRIVILEGE, 'exclusive', config)
        try:
            if privilege == 'exclusive':
                _privilege = DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_EXCLUSIVE
            elif privilege == 'control':
                _privilege = DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_CONTROL
            elif privilege == 'read_only':
                _privilege = DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_READONLY
            else:
                raise NotImplementedError(
                    'not supported: {}'.format(privilege))

            raw_device.open(_privilege)
            device = Device(module=raw_device, parent=raw_device.parent)

        except GenTL_GenericException as e:
            _logger.warning(e, exc_info=True)
            raise
        else:
            _logger.debug(
                'opened: {}'.format(_family_tree(device)))

            if config:
                config.remove(ParameterKey.DEVICE_OWNERSHIP_PRIVILEGE)

            ia = ImageAcquirer(device=device, config=config,
                               file_dict=file_dict)
            self._ias.append(ia)

            if self._profiler:
                self._profiler.print_diff()

        _logger.info('created: {0} for {1} by {2}'.format(
            ia, device.id_, self))

        return ia

    def create_image_acquirer(
            self, list_index: Optional[int] = None, *,
            id_: Optional[str] = None, vendor: Optional[str] = None,
            model: Optional[str] = None, tl_type: Optional[str] = None,
            user_defined_name: Optional[str] = None,
            serial_number: Optional[str] = None, version: Optional[str] = None,
            sleep_duration: Optional[float] = _sleep_duration_default,
            file_path: Optional[str] = None, privilege: str = 'exclusive',
            file_dict: Dict[str, bytes] = None,
            auto_chunk_data_update=True):
        """
        .. deprecated:: 1.3
            :meth:`create_image_acquirer` will be removed in 1.4.0, it is
            replaced by :meth:`create`.

        Creates an image acquirer for the specified remote device and return
        the created :class:`ImageAcquirer` object.

        :param list_index: Set an item index of the list of :class:`DeviceInfo` objects.
        :param id_: Set an index of the device information list.
        :param vendor: Set a vendor name of the target device.
        :param model: Set a model name of the target device.
        :param tl_type: Set a transport layer type of the target device.
        :param user_defined_name: Set a user defined name string of the target device.
        :param serial_number: Set a serial number string of the target device.
        :param version: Set a version number string of the target device.
        :param sleep_duration: Set a sleep duration in second that is inserted after the image acquisition worker is executed.
        :param file_path: Set a path to camera description file which you want to load on the target node map instead of the one which the device declares.
        :param privilege: Set an access privilege. :const:`exclusive`, :const:`control`, and :const:`read_only` are supported. The default is :const:`exclusive`.

        :return: An :class:`ImageAcquirer` object that associates with the specified device.

        """
        global _logger
        _deprecated(self.create_image_acquirer, self.create)
        if not self.device_info_list:
            return None

        dev_info = None

        if list_index is not None:
            dev_info = self.device_info_list[list_index]
            raw_device = dev_info.create_device()
        else:
            keys = ['id_', 'vendor', 'model', 'tl_type', 'user_defined_name',
                    'serial_number', 'version']

            candidates = self.device_info_list.copy()

            for key in keys:
                key_value = eval(key)
                if key_value:
                    items_to_be_removed = []
                    for item in candidates:
                        try:
                            if key_value != eval('item.' + key):
                                items_to_be_removed.append(item)
                        except GenTL_GenericException as e:
                            _logger.debug(e, exc_info=True)

                    for item in items_to_be_removed:
                        candidates.remove(item)

            num_candidates = len(candidates)
            if num_candidates > 1:
                raise ValueError(
                    'You have two or more candidates. '
                    'You have to pass one or more keys so that '
                    'a single candidate is specified.')
            elif num_candidates == 0:
                raise ValueError(
                    'You have no candidate. '
                    'You have to pass one or more keys so that '
                    'a single candidate is specified.')
            else:
                dev_info = candidates[0]
                raw_device = dev_info.create_device()

        config = ParameterSet({
            ParameterKey.DEVICE_OWNERSHIP_PRIVILEGE: privilege,
            ParameterKey.THREAD_SLEEP_PERIOD: sleep_duration,
            ParameterKey.REMOTE_DEVICE_SOURCE_XML_FILE_PATH: file_path,
            ParameterKey.ENABLE_AUTO_CHUNK_DATA_UPDATE: auto_chunk_data_update,
            ParameterKey.ENABLE_CLEANING_UP_INTERMEDIATE_FILES: self._clean_up
        })

        return self._create_acquirer(raw_device=raw_device, config=config,
                                     file_dict=file_dict)

    def add_cti_file(
            self, file_path: str, check_existence: bool = False,
            check_validity: bool = False):
        """
        .. deprecated:: 1.3
            :meth:`add_cti_file` will be removed in 1.4.0, it is replaced
            by :meth:`add_file`.
        """
        _deprecated(self.add_cti_file, self.add_file)
        self.add_file(file_path)

    def add_file(
            self, file_path: str, check_existence: bool = False,
            check_validity: bool = False) -> None:
        """
        Adds a CTI file as one of GenTL Producers to work with.

        Parameters
        ----------
        file_path : str
            Set a file path to the target CTI file.

        check_existence : bool
            Set True if you want to make sure the specified file exists.

        check_validity : bool
            Set True if you want to make sure the specified file is valid.

        Raises
        ------
        FileNotFoundError
            If the specified file does not exist and check_existence is
            True.

        OSError
            If the specified file is not valid and check_validity is True.
        """
        global _logger

        if check_existence:
            if not os.path.exists(file_path):
                _logger.error('attempted to add but doesn\'t exist: {}'.format(
                    file_path))
                raise FileNotFoundError

        if check_validity:
            try:
                _ = CDLL(file_path)
            except OSError as e:
                _logger.error(e, exc_info=True)
                raise
            else:
                pass

        if file_path not in self._cti_files:
            self._cti_files.append(file_path)
            _logger.info('added: {0} to {1}'.format(file_path, self))

    def remove_file(self, file_path: str) -> None:
        """
        Removes the specified CTI file on the list.

        Parameters
        ----------
        file_path : str
            Set a file path to the target CTI file.
        """
        global _logger

        if file_path in self._cti_files:
            self._cti_files.remove(file_path)
            _logger.info('removed: {0} from {1}'.format(file_path, self))

    def remove_files(self) -> None:
        """
        Removes all CTI files on the list.
        """
        global _logger

        self._cti_files.clear()
        _logger.info('flushed file list: {}'.format(self))

    def _open_gentl_producers(self) -> None:
        global _logger

        for file_path in self._cti_files:
            raw_producer = GenTLProducer.create_producer()
            try:
                raw_producer.open(file_path)
            except GenTL_GenericException as e:
                _logger.warning(e, exc_info=True)
            else:
                self._producers.append(Producer(module=raw_producer))
                _logger.debug('initialized file: {0}'.format(raw_producer.path_name))

    def _open_systems(self) -> None:
        global _logger

        for producer in self._producers:
            raw_system = producer.create_system()
            try:
                raw_system.open()
            except GenTL_GenericException as e:
                _logger.warning(e, exc_info=True)
            else:
                self._systems.append(System(module=raw_system, parent=producer))
                _logger.debug('opened: {0}'.format(_family_tree(raw_system)))

    def _release_acquires(self):
        for ia in self._ias:
            ia.destroy()
        self._ias.clear()

    def _reset(self) -> None:
        """
        Initializes the :class:`Harvester` object. Once you reset the
        :class:`Harvester` object, all allocated resources, including buffers
        and remote device, will be released.
        """
        global _logger
        self._release_acquires()

        _logger.debug('being reset: {}'.format(self))
        self.remove_files()
        self._release_gentl_producers()

        if self._profiler:
            self._profiler.print_diff()

        #
        _logger.info('reset completed: {}'.format(self))

    def _release_gentl_producers(self) -> None:
        global _logger

        self._release_systems()

        for producer in self._producers:
            if producer and producer.is_open():
                name = producer.path_name
                producer.close()
                _logger.debug('closed: {0}'.format(name))

        self._producers.clear()

    def _release_systems(self) -> None:
        global _logger

        self._release_interfaces()

        for system in self._systems:
            if system is not None and system.is_open():
                name = _family_tree(system)
                system.close()
                _logger.debug('closed: {0}'.format(name))

        self._systems.clear()

    def _release_interfaces(self) -> None:
        global _logger

        self._release_device_info_list()

        if self._ifaces is not None:
            for iface in self._ifaces:
                if iface.is_open():
                    name = _family_tree(iface)
                    iface.close()
                    _logger.debug('closed: {0}'.format(name))

        self._ifaces.clear()

    def _release_device_info_list(self) -> None:
        global _logger

        if self.device_info_list is not None:
            self._device_info_list.clear()

        _logger.debug(
            'discarded device information: {}'.format(self))

    def update(self) -> None:
        """
        Updates the list that holds available devices. You'll have to call
        this method every time you added CTI files or plugged/unplugged
        devices.

        Please note that the update method call will eventually turn the
        existing ImageAcquire objects immediately obsolete even if the object
        is still owned by someone. The owner should drop those obsolete
        objects and create another ImageAcquisition object by calling
        the Harvester.create_image_acquire method.
        """
        global _logger

        self._release_acquires()
        self._release_gentl_producers()

        try:
            self._open_gentl_producers()
            self._open_systems()
            for raw_system in self._systems:
                raw_system.update_interface_info_list(self.timeout_for_update)

                for i_info in raw_system.interface_info_list:
                    raw_iface = i_info.create_interface()
                    try:
                        raw_iface.open()
                    except GenTL_GenericException as e:
                        _logger.error(e, exc_info=True)
                    else:
                        _logger.debug('opened: {0}'.format(_family_tree(raw_iface)))

                        iface_ = Interface(module=raw_iface, parent=raw_system)
                        self._ifaces.append(iface_)

                        raw_iface.update_device_info_list(self.timeout_for_update)
                        for dev_info in raw_iface.device_info_list:
                            self.device_info_list.append(
                                DeviceInfo(module=dev_info, parent=iface_))

        except GenTL_GenericException as e:
            _logger.warning(e, exc_info=True)
            self._has_revised_device_list = False
        else:
            self._has_revised_device_list = True

        _logger.info('updated: {}'.format(self))


if __name__ == '__main__':
    pass
