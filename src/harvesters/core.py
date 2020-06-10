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
from collections.abc import Iterable
from datetime import datetime
from enum import IntEnum
import io
from logging import Logger
import ntpath
import os
import pathlib
from queue import Queue
from queue import Full, Empty
import signal
import sys
from threading import Lock, Thread, Event
from threading import current_thread, main_thread
import time
from typing import Union, List, Optional
from urllib.parse import urlparse
from warnings import warn
import weakref
import tempfile

# Related third party imports
import numpy

from genicam.genapi import NodeMap
from genicam.genapi import LogicalErrorException, RuntimeException
from genicam.genapi import ChunkAdapterGeneric, ChunkAdapterU3V, \
    ChunkAdapterGEV

from genicam.gentl import TimeoutException, \
    NotImplementedException, ParsingChunkDataException, NoDataException, \
    ErrorException, InvalidBufferException, InvalidParameterException
from genicam.gentl import GenericException
from genicam.gentl import GenTLProducer, BufferToken, EventManagerNewBuffer
from genicam.gentl import DEVICE_ACCESS_FLAGS_LIST, EVENT_TYPE_LIST, \
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST, \
    PAYLOADTYPE_INFO_IDS
from genicam.gentl import EventToken, Port, PIXELFORMAT_NAMESPACE_IDS
from genicam.gentl import Buffer as Buffer_

# Local application/library specific imports
from harvesters._private.core.port import ConcretePort
from harvesters._private.core.statistics import Statistics
from harvesters.util.logging import get_logger
from harvesters.util.pfnc import dict_by_names, dict_by_ints
from harvesters.util.pfnc import Dictionary
from harvesters.util.pfnc import component_2d_formats


_is_logging_buffer_manipulation = True if 'HARVESTERS_LOG_BUFFER_MANIPULATION' in os.environ else False
_sleep_duration_default = 0.000001  # s


def _deprecated(deprecated: object, alternative: object) -> None:
    #
    items = []
    for obj in (deprecated, alternative):
        items.append(obj.__name__ + '()' if callable(obj) else obj)

    keys = {'deprecated': 0, 'alternative': 1}
    warn(
        '{0} will be deprecated shortly. Use {1} instead.'.format(
            items[keys['deprecated']], items[keys['alternative']]
        ),
        DeprecationWarning, stacklevel=3
    )


class Module:
    def __init__(
            self, module=None,
            node_map: Optional[NodeMap] = None, parent=None):
        self._module = module
        self._node_map = node_map
        self._parent = parent

    @property
    def node_map(self):
        """
        The GenICam feature node map that belongs to the owner object.

        :getter: Returns itself.
        :type: genicam.genapi.NodeMap
        """
        return self._node_map

    @property
    def parent(self):
        """
        The parent GenTL entity.

        :getter: Returns itself.
        :type: Module
        """
        return self._parent

    @property
    def port(self) -> Port:
        """
        The GenTL Port entity that belongs to the GenTL entity.

        :getter: Returns itself.
        :type: Port
        """

        return self._module.port

    def register_event(self, event_type=None) -> EventToken:
        """
        Registers an even that is defined by the GenTL standard.

        :param event_type: Set an event type to register.
        :return: Returns an event token that is used to retrieve the event.
        :type: EventToken
        """
        return self._module.register_event(event_type)


class DataStream(Module):
    def __init__(
            self,
            module: Optional[Module] = None,
            node_map: Optional[NodeMap] = None,
            parent: Optional[Module] = None):
        super().__init__(module=module, node_map=node_map, parent=parent)

    def open(self, data_stream_id: str = None) -> None:
        """
        Opens the GenTL data stream entity.

        :param data_stream_id: Set a data stream ID to open.
        :return: None
        """
        self._module.open(data_stream_id)

    @property
    def id_(self):
        """
        The ID of the GenTL entity.

        :getter: Returns itself.
        :type: str
        """
        return self._module.id_

    @property
    def buffer_announce_min(self):
        """
        The minimum number that is required to run image acquisition process.

        :getter: Returns itself.
        :type: int
        """
        return self._module.buffer_announce_min

    def defines_payload_size(self) -> bool:
        """
        Returns the truth value of a proposition: The target GenTL Producer
        defines payload size.

        :return: The truth value.
        """
        return self._module.defines_payload_size()

    @property
    def payload_size(self) -> int:
        """
        The size of the payload. The unit is [Bytes].

        :getter: Returns itself.
        :type: int
        """
        return self._module.payload_size

    def queue_buffer(self, announced_buffer: Buffer_ = None) -> None:
        """
        Queues the announced buffer to the input buffer pool of the image
        acquisition engine.

        :param announced_buffer:
        :return: None
        """
        self._module.queue_buffer(announced_buffer)

    def start_acquisition(self, flags=None, num_images=None) -> None:
        """
        Starts image acquisition.

        :param flags:
        :param num_images:
        :return: None.
        """
        self._module.start_acquisition(flags, num_images)

    def is_open(self) -> bool:
        """
        Returns the truth value of a proposition: The DataStream entity has
        been opened.

        :return: :const:`True` if it's been opened. Otherwise :const:`False`.
        :rtype: bool
        """
        return self._module.is_open()

    def stop_acquisition(self, flags=None):
        """
        Stops image acquisition.

        :param flags:
        :return: None
        """
        self._module.stop_acquisition(flags)

    def revoke_buffer(self, buffer=None):
        """
        Revokes the specified buffer from the queue.

        :param buffer: Set an announced :class:`Buffer` object to revoke.
        :return: The revoked buffer object.
        :rtype: :class:`Buffer`
        """
        return self._module.revoke_buffer(buffer)

    def flush_buffer_queue(self, operation=None) -> None:
        """
        Flushes the queue.

        :param operation: Set an operation to execute.
        :return: None
        """
        self._module.flush_buffer_queue(operation)

    def close(self) -> None:
        """
        Closes the given DataStream entity.
        :return:  None
        """
        self._module.close()

    def announce_buffer(self, buffer_token=None) -> Buffer_:
        """
        Announces the give buffer.

        :param buffer_token: Set a buffer to announce.
        :return: An announced buffer.
        :type: :class:`Buffer_`
        """
        return self._module.announce_buffer(buffer_token)


class RemoteDevice(Module):
    def __init__(
            self, module=None, node_map: NodeMap = None, parent=None):
        super().__init__(module=module, node_map=node_map, parent=parent)

    @property
    def port(self):
        return self._parent.remote_port


class Device(Module):
    def __init__(self, module=None, node_map: NodeMap = None, parent=None):
        super().__init__(module=module, node_map=node_map, parent=parent)

    @property
    def data_stream_ids(self):
        return self._module.data_stream_ids

    def create_data_stream(self):
        return self._module.create_data_stream()

    @property
    def id_(self):
        return self._module.id_

    @property
    def tl_type(self):
        return self._module.tl_type

    def is_open(self):
        return self._module.is_open()

    def close(self):
        self._module.close()

    @property
    def port(self):
        return self._module.local_port


class Interface(Module):
    def __init__(
            self, module=None, node_map: Optional[NodeMap] = None,
            parent=None):
        super().__init__(module=module, node_map=node_map, parent=parent)


class System(Module):
    def __init__(
            self,
            module=None, node_map: Optional[NodeMap] = None, parent=None):
        assert parent is None
        super().__init__(module=module, node_map=node_map, parent=parent)


class DeviceInfo:
    def __init__(self, device_info=None):
        self._device_info = device_info

    def create_device(self):
        return self._device_info.create_device()

    def __repr__(self):
        properties = [
            'id_',
            'vendor',
            'model',
            'tl_type',
            'user_defined_name',
            'serial_number',
            'version',
        ]
        results = []
        for _property in properties:
            if _property is '':
                result = None
            else:
                try:
                    result = eval('self._device_info.' + _property)
                except:
                    result = None
            results.append(result)

        info = '('
        delimiter = ', '
        for i, r in enumerate(results):
            if r:
                r = '\'{0}\''.format(r)
            else:
                r = 'None'
            info += '{0}={1}'.format(properties[i], r)
            info += delimiter
        info = info[:-len(delimiter)]
        info += ')'
        return info

    @property
    def id_(self):
        return self._device_info.id_

    @property
    def vendor(self):
        return self._device_info.vendor

    @property
    def model(self):
        return self._device_info.model

    @property
    def tl_type(self):
        return self._device_info.tl_type

    @property
    def user_defined_name(self):
        return self._device_info.user_defined_name

    @property
    def serial_number(self):
        return self._device_info.serial_number

    @property
    def version(self):
        return self._device_info.version


class _SignalHandler:
    _event = None
    _threads = None

    def __init__(
            self, *,
            event=None, threads=None, logger: Optional[Logger] = None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        #
        assert event
        assert threads

        #
        self._event = event
        self._threads = threads

    def __call__(self, signum, frame):
        """
        A registered Python signal modules will call this method.
        """

        self._logger.debug(
            'Going to terminate threads having triggered '
            'by the event {0}.'.format(
                self._event
            )
        )

        # Set the Event:
        self._event.set()

        # Terminate the threads:
        for thread in self._threads:
            thread.stop()
            thread.join()

        self._logger.debug(
            'Has terminated threads having triggered by '
            'the event {0}.'.format(
                self._event
            )
        )


class ThreadBase:
    """
    Is a base class that is used to implement a thread that users want to
    use. For example, in general, PyQt application should implement a
    thread using QThread instead of Python's built-in Thread class.
    """
    def __init__(self, *, logger: Optional[Logger] = None, mutex=None):
        #
        super().__init__()
        #
        self._logger = logger or get_logger(name=__name__)
        #
        self._mutex = mutex
        self._is_running = False
        self._id = None

    def start(self) -> None:
        self._internal_start()
        self._logger.debug(
            'Started thread {:0X}.'.format(self.id_)
        )

    def _internal_start(self) -> None:
        """
        Releases the acquired mutex.

        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
        """
        raise NotImplementedError

    def stop(self) -> None:
        self._internal_stop()
        self._logger.debug(
            'Stopped thread {:0X}.'.format(self.id_)
        )

    def join(self):
        """
        Waits until the given task is completed.

        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
        """
        raise NotImplementedError

    def _internal_stop(self):
        """
        Releases the acquired mutex.

        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
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

        :return: None.
        """
        raise NotImplementedError

    def is_running(self) -> bool:
        """
        Returns the truth value of a proposition: The thread is running.

        This method is abstract and should be reimplemented in any sub-class.

        :return: :const:`True` if the thread is running. Otherwise it returns :const:`False`.
        :type: bool
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
        #
        assert thread
        #
        super().__init__()
        #
        self._thread = thread
        self._locked_mutex = None

    def __enter__(self):
        #
        if self._thread is None:
            return None

        #
        self._locked_mutex = self._thread.acquire()
        return self._locked_mutex

    def __exit__(self, exc_type, exc_val, exc_tb):
        #
        if self._thread is None:
            return

        #
        self._thread.release()


class _ImageAcquisitionThread(ThreadBase):
    def __init__(
            self, *,
            image_acquire=None, logger: Optional[Logger] = None):
        """

        :param image_acquire:
        :param logger:
        """
        #
        assert image_acquire
        #
        super().__init__(
            mutex=Lock(), logger=logger
        )

        #
        self._ia = image_acquire
        self._worker = self._ia.worker_image_acquisition
        self._sleep_duration = self._ia.sleep_duration
        self._thread = None

    def _internal_start(self):
        """

        :return: None.
        """
        self._thread = _NativeThread(
            thread_owner=self, worker=self._worker,
            sleep_duration=self._sleep_duration
        )
        self._id = self._thread.id_

        # Start running its worker method.
        self._is_running = True
        self._thread.start()

    def join(self):
        # Wait until the run methods is terminated.
        self._thread.join()

    def _internal_stop(self):
        #
        if self._thread is None:
            return

        # Prepare to terminate the worker method.
        self._thread.stop()
        self._is_running = False

    def acquire(self):
        #
        if self._thread:
            return self._thread.acquire()
        else:
            return None

    def release(self):
        #
        if self._thread:
            self._thread.release()
        else:
            return

    @property
    def worker(self):
        #
        if self._thread:
            return self._thread.worker
        else:
            return None

    @worker.setter
    def worker(self, obj):
        #
        if self._thread:
            self._thread.worker = obj
        else:
            return

    @property
    def mutex(self):
        return self._mutex

    @property
    def id_(self):
        return self._thread.id_

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

        #
        assert thread_owner

        #
        super().__init__(daemon=self._is_interactive())

        #
        self._worker = worker
        self._thread_owner = thread_owner
        self._sleep_duration = sleep_duration

    @staticmethod
    def _is_interactive():
        #
        if bool(getattr(sys, 'ps1', sys.flags.interactive)):
            return True

        #
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
        #
        assert buffer

        #
        super().__init__()

        #
        self._buffer = buffer
        self._data = None

    @property
    def data_format(self) -> str:
        """
        The type of the data component.

        :getter: Returns itself.
        :type: str
        """
        return self._buffer.data_format

    @property
    def data_format_namespace(self) -> PIXELFORMAT_NAMESPACE_IDS:
        """
        The data type namespace of the data component.

        :getter: Returns itself.
        :type: :class:`genicam.gentl.PIXELFORMAT_NAMESPACE_IDS`
        """
        return self._buffer.data_format

    @property
    def source_id(self) -> int:
        """
        The source ID of the data component.

        :getter: Returns itself.
        :type: int
        """
        return self._buffer.source_id

    @property
    def data(self) -> Optional[numpy.ndarray]:
        """
        The raw image data.

        :getter: Returns itself.
        :type: :class:`numpy.ndarray`
        """
        return self._data


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
            logger: Optional[Logger] = None):
        """
        :param buffer:
        :param part:
        :param node_map:
        """
        #
        assert buffer
        assert node_map

        #
        super().__init__(buffer=buffer)

        self._logger = logger or get_logger(name=__name__)

        #
        self._part = part
        self._node_map = node_map
        proxy = Dictionary.get_proxy(symbolic=self.data_format)
        self._nr_components = proxy.nr_components
        self._data = self._to_np_array(proxy)

    def _to_np_array(self, pf_proxy):
        #
        if self.has_part():
            nr_bytes = self._part.data_size
        else:
            try:
                w = self._buffer.width
            except NotImplementedException:
                w = self._node_map.Width.value
            try:
                h = self._buffer.height
            except NotImplementedException:
                h = self._node_map.Height.value
            nr_bytes = h * w
            nr_bytes *= pf_proxy.depth_in_byte
            try:
                padding_y = self._buffer.padding_y
            except NotImplementedException:
                padding_y = 0
            nr_bytes += padding_y

        array = numpy.frombuffer(
            self._buffer.raw_buffer, count=int(nr_bytes),
            dtype='uint8',
            offset=self.data_offset
        )
        return pf_proxy.expand(array)

    def represent_pixel_location(self) -> Optional[numpy.ndarray]:
        """
        Returns a NumPy array that represents the 2D pixel location,
        which is defined by PFNC, of the original image data.

        You may use the returned NumPy array for a calculation to map the
        original image to another format.

        :return: A NumPy array that represents the 2D pixel location.
        :rtype: numpy.ndarray
        """
        if self.data is None:
            return None

        #
        return self._data.reshape(
            self.height + self.y_padding,
            int(self.width * self._nr_components + self.x_padding)
        )

    @property
    def num_components_per_pixel(self) -> float:
        """
        The number of data components per pixel.

        :getter: Returns itself.
        :type: float
        """
        return self._nr_components

    def __repr__(self):
        return '{0} x {1}, {2}, {3} elements,\n{4}'.format(
            self.width,
            self.height,
            self.data_format,
            self.data.size,
            self.data
        )

    @property
    def width(self) -> int:
        """
        The width of the data component in the buffer in number of pixels.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.width
            else:
                value = self._buffer.width
        except GenericException:
            try:
                value = self._node_map.Width.value
            except AttributeError:
                value = 0
        return value

    @property
    def height(self) -> int:
        """
        The height of the data component in the buffer in number of pixels.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.height
            else:
                value = self._buffer.height
                if value == 0:
                    value = self._buffer.delivered_image_height
        except GenericException:
            try:
                value = self._node_map.Height.value
            except AttributeError:
                value = 0
        return value

    @property
    def data_format_value(self) -> int:
        """
        The data type of the data component as integer value.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.data_format
            else:
                value = self._buffer.pixel_format
        except GenericException:
            value = self._node_map.PixelFormat.get_int_value()
        assert type(value) is int
        return value

    @property
    def data_format(self) -> str:
        """
        The data type of the data component as string.

        :getter: Returns itself.
        :type: str
        """
        return dict_by_ints[self.data_format_value]

    @property
    def delivered_image_height(self) -> int:
        """
        The image height of the data component.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.delivered_image_height
            else:
                value = self._buffer.delivered_image_height
        except GenericException:
            value = 0
        return value

    @property
    def x_offset(self) -> int:
        """
        The X offset of the data in the buffer in number of pixels from the
        image origin to handle areas of interest.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.x_offset
            else:
                value = self._buffer.offset_x
        except GenericException:
            value = self._node_map.OffsetX.value
        return value

    @property
    def y_offset(self) -> int:
        """
        The Y offset of the data in the buffer in number of pixels from the
        image origin to handle areas of interest.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.y_offset
            else:
                value = self._buffer.offset_y
        except GenericException:
            value = self._node_map.OffsetY.value
        return value

    @property
    def x_padding(self) -> int:
        """
        The X padding of the data component in the buffer in number of pixels.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.x_padding
            else:
                value = self._buffer.padding_x
        except GenericException:
            value = 0
        return value

    @property
    def y_padding(self) -> int:
        """
        The Y padding of the data component in the buffer in number of pixels.

        :getter: Returns itself.
        :type: int
        """
        try:
            if self._part:
                value = self._part.y_padding
            else:
                value = self._buffer.padding_y
        except GenericException:
            value = 0
        return value

    def has_part(self):
        return self._part is not None

    @property
    def data_offset(self):
        if self.has_part():
            return self._part.data_offset
        else:
            return 0


class Buffer:
    """
    Is provided by an :class:`ImageAcquire` object when you call its
    :meth:`~harvesters.core.ImageAcquirer.fetch_buffer` method. It provides
    you a way to access acquired data and its relevant information.

    Note that it will never be necessary to create this object by yourself
    in general.
    """
    def __init__(
            self, *,
            buffer=None, node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """
        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        #
        self._buffer = buffer
        self._node_map = node_map

        self._payload = self._build_payload(
            buffer=buffer,
            node_map=node_map,
            logger=self._logger
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.queue()

    def __repr__(self):
        return '{0}'.format(self.payload.__repr__())

    @property
    def timestamp_ns(self) -> int:
        """
        The timestamp. The unit is [ns].

        :getter: Returns itself.
        :type: int
        """
        return self._buffer.timestamp_ns

    @property
    def timestamp(self) -> int:
        """
        The timestamp. The unit is GenTL Producer dependent.

        :getter: Returns itself.
        :type: int
        """
        try:
            timestamp = self._buffer.timestamp_ns
        except GenericException:
            try:
                timestamp = self._buffer.timestamp
            except GenericException:
                timestamp = 0

        return timestamp

    @property
    def timestamp_frequency(self) -> int:
        """
        The timestamp tick frequency which is used to represent a timestamp.
        The unit is [Hz].

        :getter: Returns itself.
        :type: int
        """
        #
        frequency = 1000000000  # Hz

        try:
            _ = self._buffer.timestamp_ns
        except GenericException:
            try:
                frequency = self._buffer.parent.parent.timestamp_frequency
            except GenericException:
                try:
                    frequency = self._node_map.GevTimestampTickFrequency.value
                except GenericException:
                    pass

        return frequency

    @property
    def payload_type(self):
        """
        The payload type that the :class:`Buffer` object contains.

        :getter: Returns itself.
        :type: TODO
        """

        return self._buffer.payload_type

    @property
    def payload(self):
        """
        A containing object which derives from :class:`PayloadBase` class.

        :getter: Returns itself.
        :type: :class:`PayloadBase`
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
        #
        if _is_logging_buffer_manipulation:
            self._logger.debug(
                'Queued Buffer module #{0}'
                ' containing frame #{1}'
                ' to DataStream module {2}'
                ' of Device module {3}'
                '.'.format(
                    self._buffer.context,
                    self._buffer.frame_id,
                    self._buffer.parent.id_,
                    self._buffer.parent.parent.id_
                )
            )

        self._buffer.parent.queue_buffer(self._buffer)

    @staticmethod
    def _build_payload(
            *,
            buffer=None, node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        #
        assert buffer
        assert node_map

        #
        p_type = buffer.payload_type
        if p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_UNKNOWN:
            payload = PayloadUnknown(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_IMAGE or \
                buffer.payload_type == \
                PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_DATA:
            payload = PayloadImage(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_RAW_DATA:
            payload = PayloadRawData(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_FILE:
            payload = PayloadFile(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG:
            payload = PayloadJPEG(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG2000:
            payload = PayloadJPEG2000(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_H264:
            payload = PayloadH264(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_ONLY:
            payload = PayloadChunkOnly(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif p_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_MULTI_PART:
            payload = PayloadMultiPart(
                buffer=buffer, node_map=node_map, logger=logger
            )
        else:
            payload = None

        return payload


class PayloadBase:
    """
    Is a base class of various payload types. The types are defined by the
    GenTL Standard. In general, you should not have to design a class that
    derives from this base class.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            logger: Optional[Logger] = None):
        """
        :param buffer:
        :param logger:
        """
        #
        assert buffer

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        self._buffer = buffer
        self._components = []

    @property
    def payload_type(self):
        """
        The type of the payload.

        :getter: Returns itself.
        :type: :class:`genicam.gentl.PAYLOADTYPE_INFO_IDS`
        """
        return self._buffer.payload_type

    def _build_component(
            self,
            buffer=None, part=None, node_map: Optional[NodeMap] = None):
        #
        try:
            if part:
                data_format = part.data_format
            else:
                data_format = buffer.pixel_format
        except GenericException:
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
                buffer=buffer, part=part, node_map=node_map,
                logger=self._logger
            )

        return None

    @property
    def components(self):
        """
        A :class:`list` containing objects that derive from
        :const:`ComponentBase` class.

        :getter: Returns itself.
        :type: ComponentBase
        """
        return self._components


class PayloadUnknown(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_UNKNOWN`
    by the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadImage(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_IMAGE` by
    the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)

        # Build data components.
        self._components.append(
            self._build_component(
                buffer=buffer, node_map=node_map
            )
        )

    def __repr__(self):
        return '{0}'.format(self.components[0].__repr__())


class PayloadRawData(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_RAW_DATA`
    by the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadFile(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_FILE` by
    the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadJPEG(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG` by
    the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadJPEG2000(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG2000`
    by the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadH264(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_H264` by
    the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadChunkOnly(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_ONLY`
    by the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer: Optional[Buffer] = None,
            node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)


class PayloadMultiPart(PayloadBase):
    """
    Represents a payload that is classified as
    :const:`genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_MULTI_PART`
    by the GenTL Standard.
    """
    def __init__(
            self, *,
            buffer=None, node_map: Optional[NodeMap] = None,
            logger: Optional[Logger] = None):
        """

        :param buffer:
        :param node_map:
        :param logger:
        """

        #
        assert buffer
        assert node_map

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(buffer=buffer, logger=self._logger)
        #

        # Build data components.
        # We know the buffer consists of a set of "part" that is
        # defined by the GenTL standard.
        for i, part in enumerate(self._buffer.parts):
            self._components.append(
                self._build_component(
                    buffer=buffer, part=part, node_map=node_map
                )
            )

    def __repr__(self):
        ret = ''
        for i, c in enumerate(self.components):
            ret += 'Component #{0}: {1}\n'.format(i, c.__repr__())
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

        :return: None.
        """
        raise NotImplementedError


class ImageAcquirer:
    """
    Manages everything you need to acquire images from the connecting device.
    """

    #
    _event = Event()
    _specialized_tl_type = ['U3V', 'GEV']

    class Events(IntEnum):
        TURNED_OBSOLETE = 0,
        NEW_BUFFER_AVAILABLE = 1,
        RETURN_ALL_BORROWED_BUFFERS = 2,
        READY_TO_STOP_ACQUISITION = 3,

    def _create_acquisition_thread(self) -> _ImageAcquisitionThread:
        return _ImageAcquisitionThread(
            image_acquire=self, logger=self._logger
        )

    def __init__(
            self, *, device=None,
            profiler=None, logger: Optional[Logger] = None,
            sleep_duration: float = _sleep_duration_default,
            file_path: Optional[str] = None
    ):
        """

        :param device:
        :param profiler:
        :param logger:
        :param sleep_duration:
        :param file_path: Set a path to camera description file which you want to load on the target node map instead of the one which the device declares.
        """

        #
        self._logger = logger or get_logger(name=__name__)

        #
        assert device

        #
        super().__init__()

        #
        interface = device.parent
        system = interface.parent

        env_var = 'HARVESTERS_XML_FILE_DIR'
        if env_var in os.environ:
            self._xml_dir = os.getenv(env_var)
        else:
            self._xml_dir = None

        #
        exceptions = (GenericException, LogicalErrorException)

        self._system = None
        self._interface = None
        self._device = None
        self._remote_device = None

        sources = [system, interface, device, device]
        ports = [
            system.port, interface.port, device.local_port, device.remote_port
        ]
        destinations = [
            '_system', '_interface', '_device', '_remote_device'
        ]
        ctors = [System, Interface, Device, RemoteDevice]
        parents = [None, self._system, self._interface, self._device]
        file_paths = [None, None, None, file_path]

        for (ctor, destination, file_path_, parent, port, source) in \
                zip(ctors, destinations, file_paths, parents, ports, sources):
            #
            try:
                node_map = _get_port_connected_node_map(
                    port=port, logger=self._logger,
                    xml_dir_to_store=self._xml_dir, file_path=file_path_
                )
            except exceptions as e:
                # Accept a case where the target GenTL entity does not
                # provide any device description XML file:
                self._logger.error(e, exc_info=True)
                node_map = None
            #
            setattr(
                self, destination, ctor(
                    module=source, node_map=node_map, parent=parent
                )
            )

        if self._remote_device:
            # Providing an device description file is mandatory for
            # a GenICam compliant cameras (= remote devices):
            assert self._remote_device.node_map

        #
        self._data_streams = []
        self._event_new_buffer_managers = []

        self._create_ds_at_connection = True
        if self._create_ds_at_connection:
            self._setup_data_streams()

        #
        self._profiler = profiler

        #
        self._num_filled_buffers_to_hold = 1
        self._queue = Queue(maxsize=self._num_filled_buffers_to_hold)

        #
        self._sleep_duration = sleep_duration
        self._thread_image_acquisition = self._create_acquisition_thread()

        # Prepare handling the SIGINT event:
        self._threads = []
        self._threads.append(self._thread_image_acquisition)

        # Create a signal handler if it's being run in the main thread:
        self._sigint_handler = None
        if current_thread() is main_thread():
            self._sigint_handler = _SignalHandler(
                event=self._event, threads=self._threads, logger=self._logger
            )
            signal.signal(signal.SIGINT, self._sigint_handler)
            self._logger.info('Created a signal handler for SIGINT.')

        #
        self._num_images_to_acquire = -1

        #
        self._timeout_for_image_acquisition = 1  # ms

        #
        self._statistics = Statistics()

        #
        self._announced_buffers = []

        #
        self._has_acquired_1st_image = False
        self._is_acquiring = False
        self._buffer_handling_mode = 'OldestFirstOverwrite'

        # Determine the default value:
        num_buffers_default = 16
        try:
            self._min_num_buffers = self._data_streams[0].buffer_announce_min
        except InvalidParameterException as e:
            # In general, a GenTL Producer should not raise the
            # InvalidParameterException to the inquiry for
            # STREAM_INFO_BUF_ANNOUNCE_MIN because it is totally legal
            # but we have observed a fact that there is at least one on
            # the market. As a workaround we involve this try-except block:
            self._logger.debug(e, exc_info=True)
            self._min_num_buffers = num_buffers_default
            self._num_buffers = num_buffers_default
        else:
            self._num_buffers = max(
                num_buffers_default, self._min_num_buffers
            )

        #
        self._logger.info(
            'Instantiated an ImageAcquirer object for {0}.'.format(
                self._device.id_
            )
        )

        #
        self._chunk_adapter = self._get_chunk_adapter(
            device=self.device, node_map=self.remote_device.node_map
        )

        #
        self._finalizer = weakref.finalize(self, self.destroy)

        #
        self._supported_events = [
            self.Events.TURNED_OBSOLETE,
            self.Events.RETURN_ALL_BORROWED_BUFFERS,
            self.Events.READY_TO_STOP_ACQUISITION,
            self.Events.NEW_BUFFER_AVAILABLE
        ]
        self._callback_dict = dict()
        for event in self._supported_events:
            self._callback_dict[event] = None

    def _emit_callbacks(self, event: Events) -> None:
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

    def destroy(self) -> None:
        """
        Destroys itself; releases all preserved external resources such as
        buffers or the connected remote device.

        :return: None
        """
        id_ = None
        if self.device:
            #
            self.stop_acquisition()
            #
            self._release_data_streams()
            #
            id_ = self._device.id_
            #
            if self.remote_device.node_map:
                self.remote_device.node_map.disconnect()
            #
            if self._device.is_open():
                self._device.close()

        self._device = None

        #
        if id_:
            self._logger.info(
                'Destroyed the ImageAcquirer object which {0} '
                'had belonged to.'.format(id_)
            )
        else:
            self._logger.info(
                'Destroyed an ImageAcquirer.'
            )

        if self._profiler:
            self._profiler.print_diff()

        #
        self._emit_callbacks(self.Events.TURNED_OBSOLETE)

    @property
    def buffer_handling_mode(self) -> str:
        """
        The buffer handling mode that's been applied.

        :getter: Returns itself.
        :setter: Overwrites itself with the given value.
        :type: str
        """
        return self._buffer_handling_mode

    @buffer_handling_mode.setter
    def buffer_handling_mode(self, value):
        self._buffer_handling_mode = value

    @property
    def num_buffers(self) -> int:
        """
        The number of buffers that is prepared for the image acquisition
        process. The buffers will be announced to the target GenTL Producer.

        :getter: Returns itself.
        :setter: Overwrites itself with the given value.
        :type: int
        """
        return self._num_buffers

    @num_buffers.setter
    def num_buffers(self, value: int = 1):
        #
        if value >= self._min_num_buffers:
            self._num_buffers = value
        else:
            raise ValueError(
                'The number of buffers must be '
                'greater than or equal to {0}'.format(
                    self._min_num_buffers
                )
            )

    @property
    def sleep_duration(self) -> float:
        """
        The duration that lets the image acquisition thread sleeps at
        every execution. The unit is [ms].

        :getter: Returns itself.
        :type: float
        """
        return self._sleep_duration

    @property
    def min_num_buffers(self) -> int:
        """
        The minimum number of the buffers for image acquisition. You have to
        set a value to :meth:`num_buffers` so that is greater than or equal
        to this.

        :getter: Returns itself.
        :type: int
        """
        return self._min_num_buffers

    @property
    def num_filled_buffers_to_hold(self) -> int:
        """
        The number of buffers that is used for a case where the image
        acquisition process runs in the background. You will fetch buffers
        from the buffers when you call the :meth:`fetch_buffer` method in a
        case you started the image acquisition passing :const:`True` to
        :data:`run_in_background` of the :meth:`start_acquisition` method.

        :getter: Returns itself.
        :setter: Overwrites itself with the given value.
        :type: int
        """
        return self._num_filled_buffers_to_hold

    @num_filled_buffers_to_hold.setter
    def num_filled_buffers_to_hold(self, value: int = 1):
        if value > 0:
            # Update the value:
            self._num_filled_buffers_to_hold = value

            # Move the stored buffers to the temporary list object:
            buffers = []
            while not self._queue.empty():
                buffers.append(
                    self._queue.get_nowait()
                )

            # Newly create a Queue object:
            self._queue = Queue(maxsize=self._num_filled_buffers_to_hold)

            # Move the buffers back to the newly created Queue object:
            while len(buffers) > 0:
                try:
                    self._queue.put(buffers.pop(0))
                except Full as e:
                    # Can't put it because the queue is full.
                    # Discard the buffer:
                    self._logger.debug(e, exc_info=True)
                    buffer = buffers.pop(0)
                    buffer.parent.queue_buffer(buffer)

        else:
            raise ValueError(
                'The number of filled buffers to hold must be > 0.'
            )

    @property
    def num_holding_filled_buffers(self) -> int:
        """
        The number of available buffers, i.e., the buffers that contain
        images.

        :getter: Returns itself.
        :type: int
        """
        return self._queue.qsize()

    @property
    def data_streams(self) -> List[DataStream]:
        """
        A list of GenTL :class:`DataStream` objects that the
        :class:`ImageAcquire` object is working with.

        :getter: Returns itself.
        :type: The associative :class:`DataStream` object.
        """
        return self._data_streams

    @property
    def remote_device(self) -> RemoteDevice:
        """
        The remote GenTL :class:`Device` object, typically a camera, that the
        :class:`ImageAcquire` object is working with.

        :getter: Returns itself.
        :type: RemoteDevice
        """
        return self._remote_device

    @property
    def device(self) -> Device:
        """
        The local GenTL :class:`Device` proxy object that the
        :class:`ImageAcquire` object is working with.

        :getter: Returns itself.
        :type: Device
        """
        return self._device

    @property
    def interface(self) -> Interface:
        """
        The GenTL :class:`Interface` object that the
        :class:`ImageAcquire` object is working with.

        :getter: Returns itself.
        :type: Interface
        """
        return self._interface

    @property
    def system(self) -> System:
        """
        The GenTL :class:`System` object that the
        :class:`ImageAcquire` object is working with.

        :getter: Returns itself.
        :type: System
        """
        return self._system

    def is_acquiring_images(self):
        """
        Will be deprecated shortly.
        """
        _deprecated(self.is_acquiring_images, self.is_acquiring)
        return self.is_acquiring()

    def is_acquiring(self) -> bool:
        """
        Returns the truth value of a proposition: It's acquiring images.

        :return: :const:`True` if it's acquiring images. Otherwise :const:`False`.
        :rtype: bool
        """
        return self._is_acquiring

    @property
    def timeout_for_image_acquisition(self) -> int:
        """
        The unit is [ms].

        :getter:
        :setter:
        :type: int
        """
        return self._timeout_for_image_acquisition

    @timeout_for_image_acquisition.setter
    def timeout_for_image_acquisition(self, ms):
        self._timeout_for_image_acquisition = ms

    @property
    def thread_image_acquisition(self) -> ThreadBase:
        """
        The thread object that runs image acquisition.

        :getter: Returns itself.
        :setter: Overwrites itself with the given value.
        :type: :class:`ThreadBase`
        """
        return self._thread_image_acquisition

    @thread_image_acquisition.setter
    def thread_image_acquisition(self, obj):
        self._thread_image_acquisition = obj
        self._thread_image_acquisition.worker = self.worker_image_acquisition

    @property
    def statistics(self) -> Statistics:
        """
        The statistics about image acquisition.

        :getter: Returns itself.
        :type: :class:`Statistics`
        """
        return self._statistics

    def _setup_data_streams(self):
        for i, stream_id in enumerate(self._device.data_stream_ids):
            #
            _data_stream = self._device.create_data_stream()

            try:
                _data_stream.open(stream_id)
            except GenericException as e:
                self._logger.debug(e, exc_info=True)
            else:
                self._logger.info(
                    'Opened DataStream module {0} of {1}.'.format(
                        _data_stream.id_, _data_stream.parent.id_
                    )
                )

            #
            exceptions = (GenericException, LogicalErrorException)
            try:
                node_map = _get_port_connected_node_map(
                    port=_data_stream.port, logger=self._logger
                )
            except exceptions as e:
                # Accept a case where the target GenTL entity does not
                # provide any device description XML file:
                self._logger.error(e, exc_info=True)
                node_map = None

            self._data_streams.append(
                DataStream(
                    module=_data_stream, node_map=node_map,
                    parent=self._device
                )
            )
            # Create an Event Manager object for image acquisition.
            event_token = self._data_streams[i].register_event(
                EVENT_TYPE_LIST.EVENT_NEW_BUFFER
            )
            self._event_new_buffer_managers.append(
                EventManagerNewBuffer(event_token)
            )

    def start_image_acquisition(self, run_in_background=False):
        """
        Will be deprecated shortly.
        """
        _deprecated(self.start_image_acquisition, self.start_acquisition)
        self.start_acquisition(run_in_background=run_in_background)

    def start_acquisition(self, run_in_background: bool = False) -> None:
        """
        Starts image acquisition.

        :param run_in_background: Set `True` if you want to let the ImageAcquire keep acquiring images in the background and the images you get calling `fetch_buffer` will be from the ImageAcquirer. Otherwise, the images will directly come from the target GenTL Producer.

        :return: None.
        """
        if not self._create_ds_at_connection:
            self._setup_data_streams()

        #
        num_required_buffers = self._num_buffers
        for data_stream in self._data_streams:
            try:
                num_buffers = data_stream.buffer_announce_min
                if num_buffers < num_required_buffers:
                    num_buffers = num_required_buffers
            except GenericException as e:
                num_buffers = num_required_buffers
                self._logger.debug(e, exc_info=True)

            if data_stream.defines_payload_size():
                buffer_size = data_stream.payload_size
            else:
                buffer_size = self.remote_device.node_map.PayloadSize.value

            raw_buffers = self._create_raw_buffers(
                num_buffers, buffer_size
            )

            buffer_tokens = self._create_buffer_tokens(
                raw_buffers
            )

            self._announced_buffers = self._announce_buffers(
                data_stream=data_stream, _buffer_tokens=buffer_tokens
            )

            self._queue_announced_buffers(
                data_stream=data_stream, buffers=self._announced_buffers
            )

        # Reset the number of images to acquire.
        try:
            acq_mode = self.remote_device.node_map.AcquisitionMode.value
            if acq_mode == 'Continuous':
                num_images_to_acquire = -1
            elif acq_mode == 'SingleFrame':
                num_images_to_acquire = 1
            elif acq_mode == 'MultiFrame':
                num_images_to_acquire = \
                    self.remote_device.node_map.AcquisitionFrameCount.value
            else:
                num_images_to_acquire = -1
        except GenericException as e:
            # The node doesn't exist.
            num_images_to_acquire = -1
            self._logger.debug(e, exc_info=True)

        self._num_images_to_acquire = num_images_to_acquire

        try:
            # We're ready to start image acquisition. Lock the device's
            # transport layer related features:
            self.remote_device.node_map.TLParamsLocked.value = 1
        except GenericException:
            # SFNC < 2.0
            pass

        # Start image acquisition.
        self._is_acquiring = True

        for data_stream in self._data_streams:
            data_stream.start_acquisition(
                ACQ_START_FLAGS_LIST.ACQ_START_FLAGS_DEFAULT,
                self._num_images_to_acquire
            )

        #
        if run_in_background:
            if self.thread_image_acquisition:
                self.thread_image_acquisition.start()

        #
        self.remote_device.node_map.AcquisitionStart.execute()

        self._logger.info(
            '{0} started image acquisition.'.format(self._device.id_)
        )

        if self._profiler:
            self._profiler.print_diff()

    def worker_image_acquisition(self) -> None:
        """
        The worker method of the image acquisition task.

        :return: None
        """
        #
        queue = self._queue

        #
        for event_manager in self._event_new_buffer_managers:
            try:
                if self.is_acquiring():
                    event_manager.update_event_data(
                        self._timeout_for_image_acquisition
                    )
                else:
                    return
            except TimeoutException:
                continue
            else:
                # Check if the delivered buffer is complete:
                if event_manager.buffer.is_complete():
                    #
                    if _is_logging_buffer_manipulation:
                        self._logger.debug(
                            'Acquired Buffer module #{0}'
                            ' containing frame #{1}'
                            ' from DataStream module {2}'
                            ' of Device module {3}'
                            '.'.format(
                                event_manager.buffer.context,
                                event_manager.buffer.frame_id,
                                event_manager.parent.id_,
                                event_manager.parent.parent.id_
                            )
                        )
                    #
                    if self.buffer_handling_mode == 'OldestFirstOverwrite':
                        # We want to keep the latest ones:
                        with MutexLocker(self.thread_image_acquisition):
                            if not self._is_acquiring:
                                return

                            if queue.full():
                                # Pick up the oldest one:
                                _buffer = queue.get()

                                if _is_logging_buffer_manipulation:
                                    self._logger.debug(
                                        'Queued Buffer module #{0}'
                                        ' containing frame #{1}'
                                        ' to DataStream module {2}'
                                        ' of Device module {3}'
                                        '.'.format(
                                            _buffer.context,
                                            _buffer.frame_id,
                                            _buffer.parent.id_,
                                            _buffer.parent.parent.id_
                                        )
                                    )
                                # Then discard/queue it:
                                _buffer.parent.queue_buffer(_buffer)

                            # Get the latest buffer:
                            _buffer = event_manager.buffer

                            # Then append it to the list which the user
                            # fetches later:
                            queue.put(_buffer)

                            # Then update the statistics using the buffer:
                            self._update_statistics(_buffer)
                    else:
                        # Get the latest buffer:
                        _buffer = event_manager.buffer

                        # Then update the statistics using the buffer:
                        self._update_statistics(_buffer)

                        # We want to keep the oldest ones:
                        with MutexLocker(self.thread_image_acquisition):
                            #
                            if not self._is_acquiring:
                                return

                            #
                            if queue.full():
                                # We have not space to keep the latest one.
                                # Discard/queue the latest buffer:
                                _buffer.parent.queue_buffer(_buffer)
                            else:
                                # Just append it to the list:
                                if queue:
                                    queue.put(_buffer)

                    # Call the registered callback:
                    self._emit_callbacks(self.Events.NEW_BUFFER_AVAILABLE)

                    #
                    self._update_num_images_to_acquire()

                else:
                    # Discard/queue the latest buffer when incomplete
                    self._logger.debug(
                        'Acquired buffer is complete: {0}'.format(
                            event_manager.buffer.is_complete()
                        )
                    )

                    # Queue the incomplete buffer; we have nothing to do
                    # with it:
                    data_stream = event_manager.buffer.parent
                    data_stream.queue_buffer(event_manager.buffer)

                    #
                    with MutexLocker(self.thread_image_acquisition):
                        if not self._is_acquiring:
                            return

    def _update_chunk_data(self, buffer: Optional[Buffer] = None):
        try:
            if buffer.num_chunks == 0:
                """
                self._logger.debug(
                    'The buffer does not contain any chunk data.'
                )
                """
                return
        except (ParsingChunkDataException, ErrorException) as e:
            #self._logger.error(e, exc_info=True)
            pass
        except (
                NotImplementedException, NoDataException,
                InvalidBufferException
            ) as e:
            #self._logger.debug(e, exc_info=True)
            pass
        else:
            """
            self._logger.debug(
                'The buffer contains chunk data.'
            )
            """

            #
            is_generic = False
            if buffer.tl_type not in self._specialized_tl_type:
                is_generic = True

            try:
                if is_generic:
                    self._chunk_adapter.attach_buffer(
                        buffer.raw_buffer, buffer.chunk_data_info_list
                    )
                else:
                    self._chunk_adapter.attach_buffer(buffer.raw_buffer)
            except GenericException as e:
                # Failed to parse the chunk data. Something must be wrong.
                self._logger.error(e, exc_info=True)
            else:
                """
                self._logger.debug(
                    'Updated the node map of {0}.'.format(
                        buffer.parent.parent.id_
                    )
                )
                """
                pass

    def fetch_buffer(
            self, *,
            timeout: float = 0, is_raw: bool = False,
            cycle_s: float = None) -> Optional[Buffer]:
        """
        Fetches an available :class:`Buffer` object that has been filled up
        with a single image and returns it.

        :param timeout: Set the period that defines the expiration for an available buffer delivery; if no buffer is fetched within the period then TimeoutException will be raised. The unit is [s].
        :param is_raw: Set :const:`True` if you need a raw GenTL Buffer module; note that you'll have to manipulate the object by yourself.
        :param cycle_s: Set the cycle that defines how frequently check if a buffer is available. The unit is [s].

        :return: A :class:`Buffer` object.
        :rtype: Buffer
        """
        #
        if not self.is_acquiring():
            # Does not make any sense. Raise TimeoutException:
            raise TimeoutException

        #
        _buffer = None

        watch_timeout = True if timeout > 0 else False
        base = time.time()

        if self.thread_image_acquisition and \
                self.thread_image_acquisition.is_running():
            # Case #1:
            if cycle_s:
                # Use the specified cycle:
                _cycle_s = cycle_s
            else:
                # Use the library default value:
                _cycle_s = 0.0001

            while _buffer is None:
                # Expired the suggested period; give it up:
                """
                if watch_timeout and (time.time() - base) > timeout:
                    raise TimeoutException
                """

                with MutexLocker(self.thread_image_acquisition):
                    try:
                        _buffer = self._queue.get(
                            block=True, timeout=_cycle_s
                        )
                    except Empty:
                        continue
        else:
            # Case #2:
            #
            event_manager = self._event_new_buffer_managers[0]
            while _buffer is None:
                # Expired the suggested period; give it up:
                if watch_timeout and (time.time() - base) > timeout:
                    raise TimeoutException
                #
                try:
                    event_manager.update_event_data(
                        self._timeout_for_image_acquisition
                    )
                except TimeoutException:
                    continue
                else:
                    # Check if the delivered buffer is complete:
                    if event_manager.buffer.is_complete():
                        #
                        if _is_logging_buffer_manipulation:
                            self._logger.debug(
                                'Acquired Buffer module #{0}'
                                ' containing frame #{1}'
                                ' from DataStream module {2}'
                                ' of Device module {3}'
                                '.'.format(
                                    event_manager.buffer.context,
                                    event_manager.buffer.frame_id,
                                    event_manager.parent.id_,
                                    event_manager.parent.parent.id_
                                )
                            )

                    # Get the latest buffer:
                    _buffer = event_manager.buffer

        if _buffer:
            #
            self._update_chunk_data(buffer=_buffer)

            # Then update the statistics using the buffer:
            self._update_statistics(_buffer)

            #
            if not is_raw:
                _buffer = Buffer(
                    buffer=_buffer,
                    node_map=self.remote_device.node_map,
                    logger=self._logger
                )

        #
        self._update_num_images_to_acquire()

        return _buffer

    def _update_num_images_to_acquire(self) -> None:
        #
        if self._num_images_to_acquire >= 1:
            self._num_images_to_acquire -= 1

        #
        if self._num_images_to_acquire == 0:
            #
            self._emit_callbacks(self.Events.READY_TO_STOP_ACQUISITION)

    def _update_statistics(self, buffer) -> None:
        #
        assert buffer

        #
        self._statistics.increment_num_images()
        self._statistics.update_timestamp(buffer)

    @staticmethod
    def _create_raw_buffers(
            num_buffers: int = 0, size: int = 0) -> List[bytes]:
        #
        assert num_buffers >= 0
        assert size >= 0

        # Instantiate a list object.
        raw_buffers = []

        # Append bytes objects to the list.
        # The number is specified by num_buffer and the buffer size is
        # specified by size.
        for _ in range(num_buffers):
            raw_buffers.append(bytes(size))

        # Then return the list.
        return raw_buffers

    @staticmethod
    def _create_buffer_tokens(raw_buffers: List[bytes] = None):
        #
        assert raw_buffers

        # Instantiate a list object.
        _buffer_tokens = []

        # Append Buffer Token object to the list.
        for i, buffer in enumerate(raw_buffers):
            _buffer_tokens.append(
                BufferToken(buffer, i)
            )

        # Then returns the list.
        return _buffer_tokens

    def _announce_buffers(
            self,
            data_stream: DataStream = None,
            _buffer_tokens: List[BufferToken] = None) -> List[Buffer]:
        #
        assert data_stream

        #
        announced_buffers = []

        # Iterate announcing buffers in the Buffer Tokens.
        for token in _buffer_tokens:
            # Get an announced buffer.
            announced_buffer = data_stream.announce_buffer(token)

            # And append it to the list.
            announced_buffers.append(announced_buffer)

            #
            self._logger.debug(
                'Announced Buffer #{0} to DataStraem {1}.'.format(
                    announced_buffer.context,
                    data_stream.id_
                )
            )

        # Then return the list of announced Buffer objects.
        return announced_buffers

    def _queue_announced_buffers(
            self,
            data_stream: Optional[DataStream] = None,
            buffers: Optional[List[Buffer]] = None) -> None:
        #
        assert data_stream

        #
        for buffer in buffers:
            data_stream.queue_buffer(buffer)
            self._logger.debug(
                'Queued Buffer module #{0}'
                ' to DataStream module {1}'
                ' of Device module {2}'
                '.'.format(
                    buffer.context,
                    data_stream.id_,
                    data_stream.parent.id_
                )
            )

    def stop_image_acquisition(self):
        """
        Will be deprecated shortly.
        """
        _deprecated(self.stop_image_acquisition, self.stop_acquisition)
        self.stop_acquisition()

    def stop_acquisition(self) -> None:
        """
        Stops image acquisition.

        :return: None.
        """
        if self.is_acquiring():
            #
            self._is_acquiring = False

            #
            if self.thread_image_acquisition.is_running():
                self.thread_image_acquisition.stop()
                self.thread_image_acquisition.join()

            with MutexLocker(self.thread_image_acquisition):
                #
                self.remote_device.node_map.AcquisitionStop.execute()

                try:
                    # Unlock TLParamsLocked in order to allow full device
                    # configuration:
                    self.remote_device.node_map.TLParamsLocked.value = 0
                except GenericException:
                    # SFNC < 2.0
                    pass

                for data_stream in self._data_streams:
                    # Stop image acquisition.
                    try:
                        data_stream.stop_acquisition(
                            ACQ_STOP_FLAGS_LIST.ACQ_STOP_FLAGS_KILL
                        )
                    except GenericException as e:
                        self._logger.error(e, exc_info=True)

                    # Flash the queue for image acquisition process.
                    self._flush_buffers(data_stream)

                for event_manager in self._event_new_buffer_managers:
                    event_manager.flush_event_queue()

                if self._create_ds_at_connection:
                    self._release_buffers()
                else:
                    self._release_data_streams()

            #
            self._has_acquired_1st_image = False

            #
            self._chunk_adapter.detach_buffer()

            #
            self._logger.info(
                '{0} stopped image acquisition.'.format(self._device.id_)
            )

        if self._profiler:
            self._profiler.print_diff()

    def _flush_buffers(self, data_stream: DataStream) -> None:
        # Notify the client that he has to return/queue buffers back:
        self._emit_callbacks(
            self.Events.RETURN_ALL_BORROWED_BUFFERS
        )
        data_stream.flush_buffer_queue(
            ACQ_QUEUE_TYPE_LIST.ACQ_QUEUE_ALL_DISCARD
        )

    def _release_data_streams(self) -> None:
        #
        self._release_buffers()

        #
        for data_stream in self._data_streams:
            if data_stream and data_stream.is_open():
                name_ds = data_stream.id_
                name_dev = data_stream.parent.id_
                data_stream.close()
                self._logger.info(
                    'Closed DataStream module {0} of {1}.'.format(
                        name_ds, name_dev
                    )
                )

        #
        self._data_streams.clear()
        self._event_new_buffer_managers.clear()

    def _release_buffers(self) -> None:
        #
        for data_stream in self._data_streams:
            if data_stream.is_open():
                #
                for buffer in self._announced_buffers:
                    self._logger.debug(
                        'Revoked Buffer module #{0}.'.format(
                            buffer.context,
                            data_stream.id_,
                            data_stream.parent.id_
                        )
                    )
                    _ = data_stream.revoke_buffer(buffer)

        self._announced_buffers.clear()

        # Flush the queue; we don't need the buffers anymore:
        while not self._queue.empty():
            _ = self._queue.get_nowait()


def _retrieve_file_path(
        *,
        port: Optional[Port] = None,
        url: Optional[str] = None,
        file_path_to_load: Optional[str] = None,
        logger: Optional[Logger] = None,
        xml_dir_to_store: Optional[str] = None):
    #
    _logger = logger or get_logger(name=__name__)

    #
    if file_path_to_load:
        # A file that is specified by the client will be used:
        if not os.path.exists(file_path_to_load):
            raise LogicalErrorException(
                '{0} does not exist.'.format(file_path_to_load)
            )
    else:
        if url is None:
            # Inquire its URL information.
            if len(port.url_info_list) > 0:
                url = port.url_info_list[0].url
            else:
                raise LogicalErrorException(
                    'The target port does not hold any URL.'
                )

        _logger.info('URL: {0}'.format(url))

        # And parse the URL.
        location, others = url.split(':', 1)
        location = location.lower()

        if location == 'local':
            file_name, address, size = others.split(';')
            address = int(address, 16)
            # Remove optional /// after local: See section 4.1.2 in GenTL
            # v1.4 Standard
            file_name = file_name.lstrip('/')

            # It may specify the schema version.
            delimiter = '?'
            if delimiter in size:
                size, _ = size.split(delimiter)
            size = int(size, 16)  # From Hex to Dec

            # Now we get the file content.
            size, binary_data = port.read(address, size)

            # Store the XML file on the host side; it may be a Zipped XML
            # file or a plain XML file:
            file_path_to_load = _save_file(
                xml_dir_to_store=xml_dir_to_store, file_name=file_name,
                binary_data=binary_data
            )

        elif location == 'file':
            file_path_to_load = urlparse(url).path

        elif location == 'http' or location == 'https':
            raise NotImplementedError(
                'Failed to parse URL {0}: Harvester has not supported '
                'downloading a device description file from vendor '
                'web site. If you must rely on the current condition,'
                'just try to make a request to the Harvester '
                'maintainer.'.format(url)
            )
        else:
            raise LogicalErrorException(
                'Failed to parse URL {0}: Unknown format.'.format(url)
            )

    return file_path_to_load


def _save_file(
        *,
        xml_dir_to_store: Optional[str] = None,
        file_name: Optional[str] = None,
        binary_data=None):
    #
    assert binary_data
    assert file_name

    #
    bytes_io = io.BytesIO(binary_data)

    if xml_dir_to_store is not None:
        # Create the directory if it didn't exist:
        if not os.path.exists(xml_dir_to_store):
            os.makedirs(xml_dir_to_store)
    else:
        xml_dir_to_store = tempfile.mkdtemp(
            prefix=datetime.now().strftime('%Y%m%d%H%M%S_'),
        )

    #
    _file_name = ntpath.basename(file_name)
    file_path = os.path.join(xml_dir_to_store, _file_name)

    #
    mode = 'w+'
    data_to_write = bytes_content = bytes_io.getvalue()
    if pathlib.Path(file_path).suffix.lower() == '.zip':
        mode += 'b'
    else:
        data_to_write = bytes_content.decode()
        pos = data_to_write.find('\x00')
        if pos != -1:
            # Found a \x00:
            data_to_write = data_to_write[:pos]
    #
    with open(file_path, mode) as f:
        f.write(data_to_write)

    return file_path


def _get_port_connected_node_map(
        *,
        port: Optional[Port] = None,
        logger: Optional[Logger] = None,
        file_path: Optional[str] = None,
        xml_dir_to_store: Optional[str] = None):
    #
    assert port

    #
    _logger = logger or get_logger(name=__name__)

    # Instantiate a GenICam node map object.
    node_map = NodeMap()

    #
    file_path = _retrieve_file_path(
        port=port, file_path_to_load=file_path, logger=logger, xml_dir_to_store=xml_dir_to_store
    )

    #
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
        except RuntimeException:
            try:
                node_map.load_xml_from_file(file_path)
            except RuntimeException as e:
                _logger.error(e, exc_info=True)
                has_valid_file = False

        if has_valid_file:
            # Instantiate a concrete port object of the remote device's
            # port.
            concrete_port = ConcretePort(port)

            # And finally connect the concrete port on the node map
            # object.
            node_map.connect(concrete_port, port.name)

    # Then return the node map:
    return node_map


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
    def __init__(
            self, *,
            profile=False, logger: Optional[Logger] = None):
        """

        :param profile:
        :param logger:
        """

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        #
        self._cti_files = []
        self._producers = []
        self._systems = []
        self._interfaces = []
        self._device_info_list = []
        self._ias = []

        #
        self._has_revised_device_list = False
        self._timeout_for_update = 1000  # ms

        #
        if profile:
            from harvesters._private.core.helper.profiler import Profiler
            self._profiler = Profiler()
        else:
            self._profiler = None

        if self._profiler:
            self._profiler.print_diff()

        #
        self._finalizer = weakref.finalize(self, self._reset)

    @property
    def image_acquirers(self):
        """
        The ImageAcquire objects.

        :getter: Returns its value.
        :type: ImageAcquire
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
        Will be deprecated shortly.
        """
        _deprecated('cti_files', 'files')
        return self.files

    @property
    def files(self) -> List[str]:
        """
        A list of associative CTI files.

        :getter: Returns itself.
        :type: list[str]
        """
        return self._cti_files

    @property
    def device_info_list(self) -> List[DeviceInfo]:
        """
        A list of available device information.

        :getter: Returns itself.
        :type: list[DeviceInfo]
        """
        return self._device_info_list

    @property
    def timeout_for_update(self) -> int:
        """
        The duration that is used as the time limit for the device
        enumeration process. The unit is [ms].

        :getter: Returns itself.
        :setter: Overwrites itself with the given value.
        :type: int
        """
        return self._timeout_for_update

    @timeout_for_update.setter
    def timeout_for_update(self, ms: Optional[int] = 0) -> None:
        self._timeout_for_update = ms

    @property
    def has_revised_device_info_list(self) -> bool:
        return self._has_revised_device_list

    @has_revised_device_info_list.setter
    def has_revised_device_info_list(self, value):
        self._has_revised_device_list = value

    def create_image_acquirer(
            self, list_index: Optional[int] = None, *,
            id_: Optional[str] = None,
            vendor: Optional[str] = None,
            model: Optional[str] = None,
            tl_type: Optional[str] = None,
            user_defined_name: Optional[str] = None,
            serial_number: Optional[str] = None,
            version: Optional[str] = None,
            sleep_duration: Optional[float] = _sleep_duration_default,
            file_path: Optional[str] = None,
            privilege: str = 'exclusive'
        ):
        """
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
        :param privilege: Set an access privilege. `exclusive`, `contorl`, and `read_only` are supported. The default is `exclusive`.

        :return: An :class:`ImageAcquirer` object that associates with the specified device.

        Note that you have to close it when you are ready to release the
        device that you have been controlled. As long as you hold it, the
        controlled device will be not available from other clients.

        """
        #
        if self.device_info_list is None:
            # TODO: Throw an exception to tell clients that there's no
            # device to connect.
            return None

        # Instantiate a GenTL Device module.
        if list_index is not None:
            device = self.device_info_list[list_index].create_device()
        else:
            keys = [
                'id_', 'vendor', 'model', 'tl_type',
                'user_defined_name', 'serial_number', 'version',
            ]

            # Create a copy of the list. Do not use the original list:
            candidates = self.device_info_list.copy()

            for key in keys:
                key_value = eval(key)
                if key_value:
                    items_to_be_removed = []
                    # Find out the times to be removed from the candidates.
                    for item in candidates:
                        try:
                            if key_value != eval('item.' + key):
                                items_to_be_removed.append(item)
                        except GenericException as e:
                            # The candidate doesn't support the information.
                            self._logger.warn(e, exc_info=True)
                            pass
                    # Remove irrelevant items from the candidates.
                    for item in items_to_be_removed:
                        candidates.remove(item)

            num_candidates = len(candidates)
            if num_candidates > 1:
                raise ValueError(
                    'You have two or more candidates. '
                    'You have to pass one or more keys so that '
                    'a single candidate is specified.'
                )
            elif num_candidates == 0:
                raise ValueError(
                    'You have no candidate. '
                    'You have to pass one or more keys so that '
                    'a single candidate is specified.'
                )
            else:
                device = candidates[0].create_device()

        # Then open it.
        try:
            #
            if privilege == 'exclusive':
                _privilege = DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_EXCLUSIVE
            elif privilege == 'control':
                _privilege = DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_CONTROL
            elif privilege == 'read_only':
                _privilege = DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_READONLY
            else:
                raise NotImplementedError(
                    '{0} is not supported.'.format(privilege)
                )

            #
            device.open(_privilege)

        except GenericException as e:
            self._logger.debug(e, exc_info=True)
            # Just re-throw the exception. The decision should be made by
            # the client but not Harvester:
            raise
        else:
            self._logger.info(
                'Opened Device module, {0}.'.format(device.id_)
            )

            # Create an :class:`ImageAcquirer` object and return it.
            ia = ImageAcquirer(
                device=device, profiler=self._profiler,
                logger=self._logger, sleep_duration=sleep_duration,
                file_path=file_path
            )
            self._ias.append(ia)

            if self._profiler:
                self._profiler.print_diff()

        return ia

    def add_cti_file(self, file_path: str):
        """
        Will be deprecated shortly.
        """
        _deprecated(self.add_cti_file, self.add_file)
        self.add_file(file_path)

    def add_file(self, file_path: str) -> None:
        """
        Adds a CTI file as one of GenTL Producers to work with.

        :param file_path: Set a file path to the target CTI file.

        :return: None.
        """
        if not os.path.exists(file_path):
            self._logger.warning(
                'Attempted to add {0} which does not exist.'.format(file_path)
            )

        if file_path not in self._cti_files:
            self._cti_files.append(file_path)
            self._logger.info(
                'Added {0} to the CTI file list.'.format(file_path)
            )

    def remove_cti_file(self, file_path: str):
        """
        Will be deprecated shortly.
        """
        _deprecated(self.remove_cti_file, self.remove_file)
        self.remove_file(file_path)

    def remove_file(self, file_path: str) -> None:
        """
        Removes the specified CTI file from the list.

        :param file_path: Set a file path to the target CTI file.

        :return: None.
        """
        if file_path in self._cti_files:
            self._cti_files.remove(file_path)
            self._logger.info(
                'Removed {0} from the CTI file list.'.format(file_path)
            )

    def remove_cti_files(self) -> None:
        """
        Will be deprecated shortly.
        """
        _deprecated(self.remove_cti_files, self.remove_files)
        self.remove_files()

    def remove_files(self) -> None:
        """
        Removes all CTI files in the list.

        :return: None.
        """

        self._cti_files.clear()

        #
        self._logger.info('Removed the all CTI file from the list.')

    def _open_gentl_producers(self) -> None:
        #
        for file_path in self._cti_files:
            producer = GenTLProducer.create_producer()
            try:
                producer.open(file_path)
            except GenericException as e:
                self._logger.debug(e, exc_info=True)
            else:
                self._producers.append(producer)
                self._logger.info(
                    'Initialized GenTL Producer, {0}.'.format(
                        producer.path_name
                    )
                )

    def _open_systems(self) -> None:
        for producer in self._producers:
            system = producer.create_system()
            try:
                system.open()
            except GenericException as e:
                self._logger.debug(e, exc_info=True)
            else:
                self._systems.append(system)
                self._logger.info('Opened System module, {0}.'.format(
                        system.id_
                    )
                )

    def _reset(self) -> None:
        """
        Initializes the :class:`Harvester` object. Once you reset the
        :class:`Harvester` object, all allocated resources, including buffers
        and remote device, will be released.

        :return: None.
        """
        #
        for ia in self._ias:
            ia.destroy()

        self._ias.clear()

        #
        self._logger.info('Started resetting the Harvester object.')
        self.remove_files()
        self._release_gentl_producers()

        if self._profiler:
            self._profiler.print_diff()

        #
        self._logger.info('Completed resetting the Harvester object.')

    def _release_gentl_producers(self) -> None:
        #
        self._release_systems()

        #
        for producer in self._producers:
            if producer and producer.is_open():
                name = producer.path_name
                producer.close()
                self._logger.info('Closed {0}.'.format(name))

        #
        self._producers.clear()

    def _release_systems(self) -> None:
        #
        self._release_interfaces()

        #
        for system in self._systems:
            if system is not None and system.is_open():
                name = system.id_
                system.close()
                self._logger.info('Closed System module, {0}.'.format(name))

        #
        self._systems.clear()

    def _release_interfaces(self) -> None:
        #
        self._release_device_info_list()

        #
        if self._interfaces is not None:
            for iface in self._interfaces:
                if iface.is_open():
                    name = iface.id_
                    iface.close()
                    self._logger.info(
                        'Closed Interface module, {0}.'.format(name)
                    )

        #
        self._interfaces.clear()

    def _release_device_info_list(self) -> None:
        #
        if self.device_info_list is not None:
            self._device_info_list.clear()

        #
        self._logger.info('Discarded the device information list.')

    def update_device_info_list(self):
        """
        Will be deprecated shortly.
        """
        _deprecated(self.update_device_info_list, self.update)
        self.update()

    def update(self) -> None:
        """
        Updates the list that holds available devices. You'll have to call
        this method every time you added CTI files or plugged/unplugged
        devices.

        :return: None.
        """
        #
        self._release_gentl_producers()

        try:
            self._open_gentl_producers()
            self._open_systems()
            #
            for system in self._systems:
                #
                system.update_interface_info_list(self.timeout_for_update)

                #
                for i_info in system.interface_info_list:
                    iface = i_info.create_interface()
                    try:
                        iface.open()
                    except GenericException as e:
                        self._logger.debug(e, exc_info=True)
                    else:
                        self._logger.info(
                            'Opened Interface module, {0}.'.format(iface.id_)
                        )
                        iface.update_device_info_list(self.timeout_for_update)
                        self._interfaces.append(iface)
                        for d_info in iface.device_info_list:
                            self.device_info_list.append(
                                DeviceInfo(device_info=d_info)
                            )

        except GenericException as e:
            self._logger.error(e, exc_info=True)
            self._has_revised_device_list = False
        else:
            self._has_revised_device_list = True

        #
        self._logger.info('Updated the device information list.')


if __name__ == '__main__':
    pass
