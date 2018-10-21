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
import datetime
import os
import pathlib
import signal
import sys
from threading import Lock, Thread, Event
import time
import zipfile

# Related third party imports
import numpy as np

from genicam2.genapi import NodeMap
from genicam2.genapi import LogicalErrorException, RuntimeException
from genicam2.genapi import ChunkAdapterGeneric, ChunkAdapterU3V, \
    ChunkAdapterGEV

from genicam2.gentl import TimeoutException, AccessDeniedException, \
    LoadLibraryException, InvalidParameterException, \
    NotImplementedException, NotAvailableException, ClosedException, \
    ResourceInUseException, ParsingChunkDataException, NoDataException, \
    NotInitializedException, InvalidHandleException, InvalidIdException, \
    ErrorException
from genicam2.gentl import GenTLProducer, BufferToken, EventManagerNewBuffer
from genicam2.gentl import DEVICE_ACCESS_FLAGS_LIST, EVENT_TYPE_LIST, \
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST, \
    PAYLOADTYPE_INFO_IDS

# Local application/library specific imports
from harvesters._private.core.port import ConcretePort
from harvesters._private.core.statistics import Statistics
from harvesters_util.logging import get_logger
from harvesters_util.pfnc import symbolics
from harvesters_util.pfnc import uint8_formats, uint16_formats, uint32_formats, \
    float32_formats
from harvesters_util.pfnc import component_2d_formats
from harvesters_util.pfnc import mono_formats, rgb_formats, \
    rgba_formats, bayer_formats


_is_logging_buffer_manipulation = True if 'HARVESTER_LOG_BUFFER_MANIPULATION' in os.environ else False


class _SignalHandler:
    _event = None
    _threads = None

    def __init__(self, *, event=None, threads=None, logger=None):
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

        self._logger.debug(
            'Has terminated threads having triggered by '
            'the event {0}.'.format(
                self._event
            )
        )


class ThreadBase:
    """
    By default, Harvester internally uses Python's built-in `treading` module. However, you may want to use your preferred threading module such as QThread of PyQt for some technical reasons. To allow us your preferred threading module, Harvester provides you a base proxy class to allow you implementing your threading functionality.
    """
    def __init__(self, *, mutex=None, logger=None):
        """
        :param mutex:
        """
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        #
        self._is_running = False
        self._mutex = mutex

    def start(self):
        self._is_running = True
        self._start()
        self._logger.debug(
            'Started thread {:0X}.'.format(self.id_)
        )

    def _start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def acquire(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    @property
    def is_running(self):
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value

    @property
    def worker(self):
        raise NotImplementedError

    @worker.setter
    def worker(self, obj):
        raise NotImplementedError

    @property
    def mutex(self):
        raise NotImplementedError

    @property
    def id_(self):
        raise NotImplementedError


class MutexLocker:
    def __init__(self, thread: ThreadBase=None):
        """

        :param thread:
        """
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


class _BuiltInThread(ThreadBase):
    def __init__(self, *, mutex=None, worker=None, logger=None,
                 sleep_duration_s=0.0):
        """

        :param mutex:
        :param worker:
        """
        #
        super().__init__(mutex=mutex, logger=logger)

        #
        self._thread = None
        self._worker = worker
        self._sleep_duration_s = sleep_duration_s

    def _start(self):
        # Create a Thread object. The object is not reusable.
        self._thread = _ThreadImpl(
            base=self, worker=self._worker,
            sleep_duration_s=self._sleep_duration_s
        )

        # Start running its worker method.
        self._thread.start()

    def stop(self):
        #
        if self._thread is None:
            return

        # Prepare to terminate the worker method.
        self._thread.stop()

        # Wait until the run methods is terminated.
        self._thread.join()

        self._logger.debug(
            'Stopped thread {:0X}.'.format(self._thread.id_)
        )

    def acquire(self):
        #
        if self._thread is None:
            return None

        #
        return self._thread.acquire()

    def release(self):
        #
        if self._thread is None:
            return

        #
        self._thread.release()

    @property
    def worker(self):
        #
        if self._thread is None:
            return None

        #
        return self._thread.worker

    @worker.setter
    def worker(self, obj):
        #
        if self._thread is None:
            return

        #
        self._thread.worker = obj

    @property
    def mutex(self):
        return self._mutex

    @property
    def id_(self):
        return self._thread.id_


class _ThreadImpl(Thread):
    def __init__(self, base=None, worker=None, sleep_duration_s=0.0):
        #
        super().__init__(daemon=self._is_interactive())

        #
        self._worker = worker
        self._base = base
        self._sleep_duration_s = sleep_duration_s

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
        with self._base.mutex:
            self._base.is_running = False

    def run(self):
        """
        Runs its worker method.

        This method will be terminated once its parent's is_running
        property turns False.
        """
        while self._base.is_running:
            if self._worker:
                self._worker()
                time.sleep(self._sleep_duration_s)

    def acquire(self):
        return self._base.mutex.acquire()

    def release(self):
        self._base.mutex.release()

    @property
    def worker(self):
        return self._worker

    @worker.setter
    def worker(self, obj):
        self._worker = obj

    @property
    def id_(self):
        return self.ident


class ComponentBase:
    """
    Is a base class of various (image) data component types.
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
    def data_format(self):
        """
        Returns the data type of the data component.
        :return:
        """
        return self._buffer.data_format

    @property
    def data_format_namespace(self):
        """
        Returns the data type namespace of the data component.
        :return:
        """
        return self._buffer.data_format

    @property
    def source_id(self):
        """
        TODO:
        :return:
        """
        return self._buffer.source_id

    @property
    def data(self):
        """
        Returns the component data.
        :return:
        """
        return self._data


class ComponentRaw(ComponentBase):
    def __init__(self):
        #
        super().__init__()


class Component2D(ComponentBase):
    """
    Represents a 2D image.
    """
    def __init__(self, *, buffer=None, part=None, node_map=None):
        """
        :param buffer:
        :param part:
        :param node_map:
        """
        #
        assert node_map
        assert buffer

        #
        super().__init__(buffer=buffer)

        #
        self._part = part
        self._node_map = node_map
        self._data = None

        # Identify the data type.
        symbolic = self.data_format

        if symbolic in uint16_formats:
            dtype = 'uint16'
            component_per_bytes = 2
        elif symbolic in uint32_formats:
            dtype = 'uint32'
            component_per_bytes = 4
        elif symbolic in float32_formats:
            dtype = 'float32'
            component_per_bytes = 4
        else:
            dtype = 'uint8'
            component_per_bytes = 1

        if symbolic in rgb_formats:
            num_pixel_components = 3
        elif symbolic in rgba_formats:
            num_pixel_components = 4
        else:
            num_pixel_components = 1

        #
        if self._part:
            count = self._part.data_size
            count //= component_per_bytes
            data_offset = self._part.data_offset
        else:
            count = self.width * self.height
            count *= num_pixel_components
            data_offset = 0

        # Convert the Python's built-in bytes array to a Numpy array.
        self._data = np.frombuffer(
            self._buffer.raw_buffer,
            count=count,
            dtype=dtype,
            offset=data_offset
        )

        #
        if num_pixel_components > 1:
            self._data = self._data.reshape(
                self.height, self.width, num_pixel_components
            )
        else:
            self._data = self._data.reshape(
                self.height, self.width
            )

    def __repr__(self):
        return '{0} x {1}, {2}, {3} elements,\n{4}'.format(
            self.width,
            self.height,
            self.data_format,
            self.data.size,
            self.data
        )

    @property
    def width(self):
        """
        Returns the width of the data component in the buffer in number of pixels.
        :return:
        """
        try:
            if self._part:
                value = self._part.width
            else:
                value = self._buffer.width
        except InvalidParameterException:
            value = self._node_map.Width.value
        return value

    @property
    def height(self):
        """
        Returns the height of the data component in the buffer in number of pixels.
        :return:
        """
        try:
            if self._part:
                value = self._part.height
            else:
                value = self._buffer.height
        except InvalidParameterException:
            value = self._node_map.Height.value
        return value

    @property
    def data_format_value(self):
        """
        Returns the data type of the data component as integer value.
        :return:
        """
        try:
            if self._part:
                value = self._part.data_format
            else:
                value = self._buffer.pixel_format
        except InvalidParameterException:
            value = self._node_map.PixelFormat.value
        return value

    @property
    def data_format(self):
        """
        Returns the data type of the data component as string.
        :return:
        """
        return symbolics[self.data_format_value]

    @property
    def delivered_image_height(self):
        """
        Returns the image height of the data component.
        :return:
        """
        try:
            if self._part:
                value = self._part.delivered_image_height
            else:
                value = self._buffer.delivered_image_height
        except InvalidParameterException:
            value = 0
        return value

    @property
    def x_offset(self):  # TODO: Check the naming convention.
        """
        Returns the X offset of the data in the buffer in number of pixels from the image origin to handle areas of interest.
        :return:
        """
        try:
            if self._part:
                value = self._part.x_offset
            else:
                value = self._buffer.offset_x
        except InvalidParameterException:
            value = self._node_map.OffsetX.value
        return value

    @property
    def y_offset(self):
        """
        Returns the Y offset of the data in the buffer in number of pixels from the image origin to handle areas of interest.
        :return:
        """
        try:
            if self._part:
                value = self._part.y_offset
            else:
                value = self._buffer.offset_y
        except InvalidParameterException:
            value = self._node_map.OffsetY.value
        return value

    @property
    def x_padding(self):
        """
        Returns the X padding of the data component in the buffer in number of pixels.
        TODO:
        :return:
        """
        try:
            if self._part:
                value = self._part.x_padding
            else:
                value = self._buffer.padding_x
        except InvalidParameterException:
            value = 0
        return value

    @property
    def y_padding(self):
        """
        Returns the Y padding of the data component in the buffer in number of pixels.
        TODO:
        :return:
        """
        try:
            if self._part:
                value = self._part.y_padding
            else:
                value = self._buffer.padding_y
        except InvalidParameterException:
            value = 0
        return value


class Buffer:
    """
    TODO:
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        """
        :param buffer:
        :param data_stream:
        :param node_map:
        """
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
    def timestamp_ns(self):
        """
        TODO:
        :return:
        """
        return self._buffer.timestamp_ns

    @property
    def timestamp(self):
        """
        TODO:
        :return:
        """
        timestamp = 0
        try:
            timestamp = self._buffer.timestamp_ns
        except (InvalidParameterException, NotImplementedException,
                NotAvailableException):
            try:
                _ = self.timestamp_frequency
            except InvalidParameterException:
                pass
            else:
                try:
                    timestamp = self._buffer.timestamp
                except (InvalidParameterException, NotAvailableException):
                    timestamp = 0

        return timestamp

    @property
    def timestamp_frequency(self):
        """
        TODO:
        :return:
        """
        #
        frequency = 1000000000  # Hz

        try:
            _ = self._buffer.timestamp_ns
        except (InvalidParameterException, NotImplementedException,
                NotAvailableException):
            try:
                frequency = self._buffer.parent.parent.timestamp_frequency
            except (InvalidParameterException, NotImplementedException,
                    NotAvailableException):
                try:
                    frequency = self._node_map.GevTimestampTickFrequency.value
                except (LogicalErrorException, NotImplementedException):
                    pass

        return frequency

    @property
    def payload_type(self):
        """
        Returns a payload type of the payload.

        :rtype: genicam2.gentl.PAYLOADTYPE_INFO_IDS

        """

        return self._buffer.payload_type

    @property
    def payload(self):
        """
        Returns the payload that the Buffer object contains.
        :return:
        """
        return self._payload

    def queue(self):
        """
        Queues the buffer to prepare for the upcoming image acquisition. Once the buffer is queued, the Buffer object will be obsolete. You'll have nothing to do with it.
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
    def _build_payload(*, buffer=None, node_map=None, logger=None):
        #
        assert buffer
        assert node_map

        #
        if buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_UNKNOWN:
            payload = PayloadUnknown(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_IMAGE or \
                buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_DATA:
            payload = PayloadImage(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_RAW_DATA:
            payload = PayloadRawData(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_FILE:
            payload = PayloadFile(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG:
            payload = PayloadJPEG(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_JPEG2000:
            payload = PayloadJPEG2000(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_H264:
            payload = PayloadH264(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_ONLY:
            payload = PayloadChunkOnly(
                buffer=buffer, node_map=node_map, logger=logger
            )
        elif buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_MULTI_PART:
            payload = PayloadMultiPart(
                buffer=buffer, node_map=node_map, logger=logger
            )
        else:
            payload = None

        return payload


class PayloadBase:
    """
    Is a base class of various payload types.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        """
        :param buffer:
        """
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        self._buffer = buffer
        self._components = []

    @property
    def payload_type(self):
        """
        TODO:
        :return:
        """
        return self._buffer.payload_type

    @staticmethod
    def _build_component(buffer=None, part=None, node_map=None):
        #
        if part:
            data_format = part.data_format
        else:
            data_format = buffer.pixel_format

        #
        symbolic = symbolics[data_format]
        if symbolic in component_2d_formats:
            return Component2D(buffer=buffer, part=part, node_map=node_map)

        return None

    @property
    def components(self):
        """
        Returns a list containing Component objects.
        :return:
        """
        return self._components


class PayloadUnknown(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadImage(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )

        # Build data components.
        self._components.append(
            self._build_component(
                buffer=buffer, node_map=node_map
            )
        )

    def __repr__(self):
        return '{0}'.format(self.components[0].__repr__())


class PayloadRawData(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadFile(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadJPEG(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadJPEG2000(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadH264(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadChunkOnly(PayloadBase):
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )


class PayloadMultiPart(PayloadBase):
    """
    TODO:
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
        """
        :param buffer:
        :param node_map:
        """
        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__(
            buffer=buffer, node_map=node_map, logger=self._logger
        )
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


class ImageAcquirer:
    """
    Manages everything you need to acquire images from the connecting image transmitter device.
    """

    #
    _event = Event()
    _specialized_tl_type = ['U3V', 'GEV']

    def __init__(
            self, *, parent=None, min_num_buffers=8, device=None,
            create_ds_at_connection=True, profiler=None, logger=None,
            tear_down=None, sleep_duration=0.0
    ):
        """
        :param min_num_buffers:
        :param device:
        :param profiler:
        """
        #
        self._logger = logger or get_logger(name=__name__)

        #
        assert device
        assert parent

        #
        super().__init__()

        #
        self._parent = parent

        #
        self._device = device
        self._device.node_map = _get_port_connected_node_map(
            port=self.device.remote_port, logger=self._logger
        )  # Remote device's node map
        try:
            self._device.local_node_map = _get_port_connected_node_map(
                port=self.device.local_port, logger=self._logger
            )  # Local device's node map
        except RuntimeException as e:
            self._logger.error(e, exc_info=True)
            self._device.local_node_map = None

        #
        self._interface = self._device.parent
        try:
            self._interface.local_node_map = _get_port_connected_node_map(
                port=self._interface.port, logger=self._logger
            )
        except RuntimeException as e:
            self._logger.error(e, exc_info=True)
            self._interface.local_node_map = None

        #
        self._system = self._interface.parent
        try:
            self._system.local_node_map = _get_port_connected_node_map(
                port=self._system.port, logger=self._logger
            )
        except RuntimeException as e:
            self._logger.error(e, exc_info=True)
            self._system.local_node_map = None

        #
        self._data_streams = []
        self._event_new_buffer_managers = []

        self._create_ds_at_connection = create_ds_at_connection
        if self._create_ds_at_connection:
            self._setup_data_streams()

        #
        self._profiler = profiler

        #
        self._mutex = Lock()
        self._thread_image_acquisition = _BuiltInThread(
            mutex=self._mutex,
            worker=self._worker_image_acquisition,
            logger=self._logger,
            sleep_duration_s=sleep_duration
        )

        # Prepare handling the SIGINT event:
        self._threads = []
        self._threads.append(self._thread_image_acquisition)

        self._sigint_handler = _SignalHandler(
            event=self._event, threads=self._threads, logger=self._logger
        )
        signal.signal(signal.SIGINT, self._sigint_handler)

        #
        self._num_images_to_hold = 1

        #
        self._num_images_to_acquire = -1

        #
        self._timeout_for_image_acquisition = 1  # ms

        #
        self._statistics = Statistics()

        #
        self._announced_buffers = []
        self._fetched_buffers = []

        #
        self._has_acquired_1st_image = False

        #
        self._signal_stop_image_acquisition = None

        #
        self._is_acquiring_images = False

        #
        self._min_num_buffers = min_num_buffers

        #
        self._logger.info(
            'Instantiated an ImageAcquirer object for {0}.'.format(
                self._device.id_
            )
        )

        #
        self._chunk_adapter = self._get_chunk_adapter(device=self._device)
        self._tear_down = tear_down

    @staticmethod
    def _get_chunk_adapter(*, device=None):
        if device.tl_type == 'U3V':
            return ChunkAdapterU3V(device.node_map.pointer)
        elif device.tl_type == 'GEV':
            return ChunkAdapterGEV(device.node_map.pointer)
        else:
            return ChunkAdapterGeneric(device.node_map.pointer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        self.destroy()

    @property
    def device(self):
        """
        Returns the proxy Device module object of the connecting remote
        device.
        :return:
        """
        return self._device

    @property
    def interface(self):
        """
        Returns the parent Interface module object of the connecting remote
        device.
        :return:
        """
        return self._interface

    @property
    def system(self):
        """
        Returns the parent System module object of the connecting remote
        device.
        :return:
        """
        return self._system

    @property
    def is_acquiring_images(self):
        """
        Returns a truth value of the following proposition: The
        :class:`~harvesters.core.Harvester` object is acquiring images.

        :rtype: bool
        """
        return self._is_acquiring_images

    @property
    def timeout_for_image_acquisition(self):
        return self._timeout_for_image_acquisition

    @timeout_for_image_acquisition.setter
    def timeout_for_image_acquisition(self, ms):
        with self.thread_image_acquisition:
            self._timeout_for_image_acquisition = ms

    @property
    def thread_image_acquisition(self):
        return self._thread_image_acquisition

    @thread_image_acquisition.setter
    def thread_image_acquisition(self, obj):
        self._thread_image_acquisition = obj
        self._thread_image_acquisition.worker = self._worker_image_acquisition

    @property
    def signal_stop_image_acquisition(self):
        return self._signal_stop_image_acquisition

    @signal_stop_image_acquisition.setter
    def signal_stop_image_acquisition(self, obj):
        self._signal_stop_image_acquisition = obj

    @property
    def tear_down(self):
        return self._tear_down

    @tear_down.setter
    def tear_down(self, value):
        self._tear_down = value

    @property
    def statistics(self):
        return self._statistics

    def _setup_data_streams(self):
        #
        for i, stream_id in enumerate(self._device.data_stream_ids):
            data_stream = self._device.create_data_stream()
            try:
                data_stream.open(stream_id)
            except (
                NotInitializedException, InvalidHandleException,
                ResourceInUseException, InvalidIdException,
                InvalidParameterException, AccessDeniedException,
                NotAvailableException,
            ) as e:
                self._logger.debug(e, exc_info=True)
            else:
                self._logger.info(
                    'Opened DataStream module {0} of {1}.'.format(
                        data_stream.id_, data_stream.parent.id_
                    )
                )
                try:
                    data_stream.local_node_map = _get_port_connected_node_map(
                        port=data_stream.port, logger=self._logger
                    )
                except RuntimeException as e:
                    self._logger.error(e, exc_info=True)
                    data_stream.local_node_map = None

                # Create an Event Manager object for image acquisition.
                event_token = data_stream.register_event(
                    EVENT_TYPE_LIST.EVENT_NEW_BUFFER
                )

                self._event_new_buffer_managers.append(EventManagerNewBuffer(event_token))
                self._data_streams.append(data_stream)

    def start_image_acquisition(self):
        """
        Starts image acquisition.

        :return: None
        """
        if not self._create_ds_at_connection:
            self._setup_data_streams()

        #
        num_required_buffers = self._min_num_buffers
        for data_stream in self._data_streams:
            try:
                num_buffers = data_stream.buffer_announce_min
                if num_buffers < num_required_buffers:
                    num_buffers = num_required_buffers
            except InvalidParameterException as e:
                num_buffers = num_required_buffers
                self._logger.debug(e, exc_info=True)

            if data_stream.defines_payload_size():
                buffer_size = data_stream.payload_size
            else:
                buffer_size = self.device.node_map.PayloadSize.value

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
            acq_mode = self.device.node_map.AcquisitionMode.value
            if acq_mode == 'Continuous':
                num_images_to_acquire = -1
            elif acq_mode == 'SingleFrame':
                num_images_to_acquire = 1
            elif acq_mode == 'MultiFrame':
                num_images_to_acquire = self.device.node_map.AcquisitionFrameCount.value
            else:
                num_images_to_acquire = -1
        except LogicalErrorException as e:
            # The node doesn't exist.
            num_images_to_acquire = -1
            self._logger.debug(e, exc_info=True)

        self._num_images_to_acquire = num_images_to_acquire

        # Start image acquisition.
        self._is_acquiring_images = True

        for data_stream in self._data_streams:
            data_stream.start_acquisition(
                ACQ_START_FLAGS_LIST.ACQ_START_FLAGS_DEFAULT,
                self._num_images_to_acquire
            )

        #
        if self.thread_image_acquisition:
            self.thread_image_acquisition.start()

        #
        self.device.node_map.AcquisitionStart.execute()

        self._logger.info(
            '{0} started image acquisition.'.format(self._device.id_)
        )

        if self._profiler:
            self._profiler.print_diff()

    def _worker_image_acquisition(self):
        for event_manager in self._event_new_buffer_managers:
            try:
                if self.is_acquiring_images:
                    event_manager.update_event_data(
                        self._timeout_for_image_acquisition
                    )
                else:
                    return
            except TimeoutException as e:
                continue
            else:
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
                # We've got a new image so now we can reuse the buffer that
                # we had kept.
                with MutexLocker(self.thread_image_acquisition):
                    if not self._is_acquiring_images:
                        return

                    if len(self._fetched_buffers) >= self._num_images_to_hold:
                        # We have a buffer now so we queue it; it's discarded
                        # before being used.
                        buffer = self._fetched_buffers.pop(0)
                        buffer.parent.queue_buffer(buffer)

                # Append the recently fetched buffer.
                # Then one buffer remains for our client.
                buffer = event_manager.buffer

                self._fetched_buffers.append(buffer)

                #
                self._update_statistics(buffer)

            #
            if self._num_images_to_acquire >= 1:
                self._num_images_to_acquire -= 1

            if self._num_images_to_acquire == 0:
                #
                if self.signal_stop_image_acquisition:
                    self.signal_stop_image_acquisition.emit()

    def _update_chunk_data(self, buffer=None):
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
        except (NotImplementedException, NoDataException) as e:
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
            except RuntimeException as e:
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

    def fetch_buffer(self, *, timeout_s=0, is_raw=False):
        """
        Fetches the oldest :class:`~harvesters.buffer.Buffer` object and returns it.

        :param timeout_s: Set timeout value in second.
        :param is_raw: Set True if you need a raw GenTL Buffer module.

        :return: A :class:`~harvesters.buffer.Buffer` object.
        """
        if not self.is_acquiring_images:
            raise TimeoutException

        watch_timeout = True if timeout_s > 0 else False
        buffer = None
        base = time.time()

        while buffer is None:
            if watch_timeout and (time.time() - base) > timeout_s:
                raise TimeoutException
            else:
                with MutexLocker(self.thread_image_acquisition):
                    if len(self._fetched_buffers) > 0:
                        if is_raw:
                            buffer = self._fetched_buffers.pop(0)
                        else:
                            # Update the chunk data:
                            _buffer = self._fetched_buffers.pop(0)
                            self._update_chunk_data(buffer=_buffer)
                            #
                            buffer = Buffer(
                                buffer=_buffer,
                                node_map=self.device.node_map,
                                logger=self._logger
                            )


        if _is_logging_buffer_manipulation:
            self._logger.debug(
                'Fetched Buffer module #{0}'
                ' containing frame #{1}'
                ' that belongs to DataStream module {2}'
                ' of Device module {2}'
                '.'.format(
                    buffer._buffer.context,
                    buffer._buffer.frame_id,
                    buffer._buffer.parent.id_,
                    buffer._buffer.parent.parent.id_
                )
            )

        return buffer

    def _update_statistics(self, buffer):
        #
        self._statistics.increment_num_images()
        self._statistics.update_timestamp(buffer)

    @staticmethod
    def _create_raw_buffers(num_buffers, size):
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
    def _create_buffer_tokens(raw_buffers):
        # Instantiate a list object.
        _buffer_tokens = []

        # Append Buffer Token object to the list.
        for i, buffer in enumerate(raw_buffers):
            _buffer_tokens.append(
                BufferToken(buffer, i)
            )

        # Then returns the list.
        return _buffer_tokens

    def _announce_buffers(self, data_stream=None, _buffer_tokens=None):
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

    def _queue_announced_buffers(self, data_stream=None, buffers=None):
        #
        assert data_stream

        #
        for buffer in buffers:
            data_stream.queue_buffer(buffer)
            self._logger.debug(
                'Queued Buffer module #{0}'
                ' to DataStream module {1}'
                ' that belongs to Device module {2}'
                '.'.format(
                    buffer.context,
                    data_stream.id_,
                    data_stream.parent.id_
                )
            )

    def stop_image_acquisition(self):
        """
        Stops image acquisition.

        :return: None
        """
        if self.is_acquiring_images:
            #
            self._is_acquiring_images = False

            #
            if self._tear_down:
                self._tear_down()

            #
            if self.thread_image_acquisition.is_running:  # TODO
                self.thread_image_acquisition.stop()

            with MutexLocker(self.thread_image_acquisition):
                #
                self.device.node_map.AcquisitionStop.execute()

                for data_stream in self._data_streams:
                    # Stop image acquisition.
                    try:
                        data_stream.stop_acquisition(
                            ACQ_STOP_FLAGS_LIST.ACQ_STOP_FLAGS_KILL
                        )
                    except (ResourceInUseException, TimeoutException) as e:
                        self._logger.error(e, exc_info=True)

                    # Flash the queue for image acquisition process.
                    data_stream.flush_buffer_queue(
                        ACQ_QUEUE_TYPE_LIST.ACQ_QUEUE_ALL_DISCARD
                    )

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

    def destroy(self):
        # Ask its parent to destroy it:
        if self._device:
            self._parent._destroy_image_acquirer(self)

    def _release_data_streams(self):
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

    def _release_buffers(self):
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

        self._fetched_buffers.clear()
        self._announced_buffers.clear()


def _get_port_connected_node_map(*, port=None, logger=None):
    # Inquire it's URL information.
    # TODO: Consider a case where len(url_info_list) > 1.
    url = port.url_info_list[0].url
    if logger:
        logger.info('URL: {0}'.format(url))

    # And parse the URL.
    location, others = url.split(':', 1)
    file_name, address, size = others.split(';')
    address = int(address, 16)

    # It may specify the schema version.
    delimiter = '?'
    if delimiter in size:
        size, _ = size.split(delimiter)
    size = int(size, 16)

    # Now we get the file content.
    content = port.read(address, size)

    # But wait, we have to check if it's a zip file or not.
    content = content[1]
    file_content = io.BytesIO(content)

    #
    directory = os.path.dirname(__file__)
    with open(os.path.join(directory, 'xml', file_name), 'w+b') as f:
        f.write(content)

    # Let's check the reality.
    if zipfile.is_zipfile(file_content):
        # Yes, that's a zip file.
        file_content = zipfile.ZipFile(file_content, 'r')

        # Extract the file content from the zip file.
        for file_info in file_content.infolist():
            if pathlib.Path(
                    file_info.filename).suffix.lower() == '.xml':
                #
                content = file_content.read(file_info).decode('utf8')
                break

    # Instantiate a GenICam node map object.
    node_map = NodeMap()

    # Then load the XML file content on the node map object.
    node_map.load_xml_from_string(content)

    # Instantiate a concrete port object of the remote device's
    # port.
    concrete_port = ConcretePort(port)

    # And finally connect the concrete port on the node map
    # object.
    node_map.connect(concrete_port, port.name)

    # Then return the node mpa.
    return node_map


class Harvester:
    """
    Is the class that works for you as Harvester Core. Everything starts with this class.
    """
    #
    def __init__(self, *, profile=False, logger=None):
        """

        :param profile:
        :param min_num_buffers:
        :param parent:
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        self.reset()

    @property
    def cti_files(self):
        """
        Returns a :class:`list` containing CTI file paths.

        :return: A list object containing str objects.
        """
        return self._cti_files

    @property
    def device_info_list(self):
        """
        Returns a :class:`list` containing :class:`~genicam2.gentl.DeviceInfo` objects.

        :return: A list object containing :class:`~genicam2.gentl.DeviceInfo` objects
        """
        return self._device_info_list

    @property
    def timeout_for_update(self):
        return self._timeout_for_update

    @timeout_for_update.setter
    def timeout_for_update(self, ms):
        self._timeout_for_update = ms

    @property
    def has_revised_device_info_list(self):
        return self._has_revised_device_list

    @has_revised_device_info_list.setter
    def has_revised_device_info_list(self, value):
        self._has_revised_device_list = value

    def create_image_acquirer(
            self, list_index=None, *, id_=None,
            vendor=None, model=None, tl_type=None, user_defined_name=None,
            serial_number=None, version=None
        ):
        """
        Creates an image acquirer for the specified device and return it.

        :param list_index: Set an item index of the list of :class:`~genicam2.gentl.DeviceInfo` objects.
        :param id_:
        :param vendor:
        :param model:
        :param tl_type:
        :param user_defined_name:
        :param serial_number:
        :param version:

        :return: An `ImageAcquirer` object that associates with the specified device.

        Note that you have to close it when you are ready to release the device that you have been controlled. As long as you hold it, the controlled device will be not available from other clients.

        """
        #
        if self.device_info_list is None:
            # TODO: Throw an exception to tell clients that there's no
            # device to connect.
            return

        # Instantiate a GenTL Device module.
        if list_index is not None:
            device = self.device_info_list[list_index].create_device()
        else:
            keys = [
                'id_', 'vendor', 'model', 'tl_type',
                'user_defined_name', 'serial_number', 'version',
            ]

            candidates = self.device_info_list

            for key in keys:
                key_value = eval(key)
                if key_value:
                    items_to_be_removed = []
                    # Find out the times to be removed from the candidates.
                    for item in candidates:
                        try:
                            if key_value != eval('item.' + key):
                                items_to_be_removed.append(item)
                        except (AttributeError, NotAvailableException) as e:
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
            device.open(
                DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_EXCLUSIVE
            )
        except (
            NotInitializedException, InvalidHandleException,
            InvalidIdException, ResourceInUseException,
            InvalidParameterException, NotImplementedException,
            AccessDeniedException,
        ) as e:
            self._logger.debug(e, exc_info=True)
            # Just re-throw the exception. The decision should be made by
            # the client but not Harvester:
            raise
        else:
            self._logger.info(
                'Opened Device module, {0}.'.format(device.id_)
            )

            # Create an image acquirer object and return it.
            ia = ImageAcquirer(
                parent=self, device=device, profiler=self._profiler,
                logger=self._logger
            )
            self._ias.append(ia)

            if self._profiler:
                self._profiler.print_diff()

        return ia

    def add_cti_file(self, file_path: str):
        """
        Adds a CTI file to work with to the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None
        """
        if file_path not in self._cti_files:
            self._cti_files.append(file_path)
            self._logger.info(
                'Added {0} to the CTI file list.'.format(file_path)
            )

    def remove_cti_file(self, file_path: str):
        """
        Remove the specified CTI file from the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None
        """
        if file_path in self._cti_files:
            self._cti_files.remove(file_path)
            self._logger.info(
                'Removed {0} from the CTI file list.'.format(file_path)
            )

    def remove_cti_files(self):
        """
        Removes all CTI files in the CTI file list.

        :return: None
        """

        self._cti_files.clear()

        #
        self._logger.info('Removed the all CTI file from the list.')

    def _open_gentl_producers(self):
        #
        for file_path in self._cti_files:
            producer = GenTLProducer.create_producer()
            try:
                producer.open(file_path)
            except (
                NotInitializedException, InvalidHandleException,
                InvalidIdException, ResourceInUseException,
                InvalidParameterException, NotImplementedException,
                AccessDeniedException, ClosedException,
            ) as e:
                self._logger.debug(e, exc_info=True)
            else:
                self._producers.append(producer)
                self._logger.info(
                    'Initialized GenTL Producer, {0}.'.format(
                        producer.path_name
                    )
                )

    def _open_systems(self):
        for producer in self._producers:
            system = producer.create_system()
            try:
                system.open()
            except (
                NotInitializedException, ResourceInUseException,
                InvalidParameterException, AccessDeniedException,
                ClosedException,
            ) as e:
                self._logger.debug(e, exc_info=True)
            else:
                self._systems.append(system)
                self._logger.info('Opened System module, {0}.'.format(
                        system.id_
                    )
                )

    def reset(self):
        """
        Initializes the Harvester object.

        :return: None
        """
        #
        for ia in self._ias:
            ia.destroy()

        self._ias.clear()

        #
        self._logger.info('Started resetting the Harvester object.')
        self.remove_cti_files()
        self._release_gentl_producers()

        if self._profiler:
            self._profiler.print_diff()

        #
        self._logger.info('Completed resetting the Harvester object.')

    def _release_gentl_producers(self):
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

    def _release_systems(self):
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

    def _release_interfaces(self):
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

    def _release_device_info_list(self):
        #
        if self.device_info_list is not None:
            self._device_info_list.clear()

        #
        self._logger.info('Discarded the device information list.')

    def update_device_info_list(self):
        """
        Updates the device information list. You'll have to call this method
        every time you added CTI files or plugged/unplugged devices.

        :return: None
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
                    except (
                        NotInitializedException, ResourceInUseException,
                        InvalidHandleException, InvalidHandleException,
                        InvalidParameterException, AccessDeniedException,
                    ) as e:
                        self._logger.debug(e, exc_info=True)
                    else:
                        self._logger.info(
                            'Opened Interface module, {0}.'.format(iface.id_)
                        )
                        iface.update_device_info_list(self.timeout_for_update)
                        self._interfaces.append(iface)
                        for d_info in iface.device_info_list:
                            self.device_info_list.append(d_info)

        except LoadLibraryException as e:
            self._logger.error(e, exc_info=True)
            self._has_revised_device_list = False
        else:
            self._has_revised_device_list = True

        #
        self._logger.info('Updated the device information list.')

    def _destroy_image_acquirer(self, ia):
        """
        Releases all external resources including the controlling device.
        """

        id_ = None
        if ia.device:
            #
            ia.stop_image_acquisition()

            #
            ia._release_data_streams()

            #
            id_ = ia._device.id_

            #
            if ia.device.node_map:
                #
                if ia._chunk_adapter:
                    ia._chunk_adapter.detach_buffer()
                    ia._chunk_adapter = None
                    self._logger.info(
                        'Detached a buffer from the chunk adapter of {0}.'.format(
                            id_
                        )
                    )

                ia.device.node_map.disconnect()
                self._logger.info(
                    'Disconnected the port from the NodeMap of {0}.'.format(
                        id_
                    )
                )

            #
            if ia._device.is_open():
                ia._device.close()
                self._logger.info(
                    'Closed Device module, {0}.'.format(id_)
                )

        ia._device = None

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

        self._ias.remove(ia)


if __name__ == '__main__':
    pass
