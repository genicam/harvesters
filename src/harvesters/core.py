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
import os
import pathlib
import signal
import sys
from threading import Lock, Thread, Event
import time
from urllib.parse import unquote
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
    ErrorException, InvalidBufferException
from genicam2.gentl import GenTLProducer, BufferToken, EventManagerNewBuffer
from genicam2.gentl import DEVICE_ACCESS_FLAGS_LIST, EVENT_TYPE_LIST, \
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST, \
    PAYLOADTYPE_INFO_IDS

# Local application/library specific imports
from harvesters._private.core.port import ConcretePort
from harvesters._private.core.statistics import Statistics
from harvesters.util.logging import get_logger
from harvesters.util.pfnc import symbolics
from harvesters.util.pfnc import uint16_formats, uint32_formats, \
    float32_formats, uint8_formats
from harvesters.util.pfnc import component_2d_formats
from harvesters.util.pfnc import lmn_444_location_formats, \
    lmno_4444_location_formats, lmn_422_location_formats, \
    lmn_411_location_formats, mono_location_formats, bayer_location_formats


_is_logging_buffer_manipulation = True if 'HARVESTERS_LOG_BUFFER_MANIPULATION' in os.environ else False
_sleep_duration_default = 0.000001  # s

#
_env_var_xml_file_dir = 'HARVESTERS_XML_FILE_DIR'
if _env_var_xml_file_dir in os.environ:
    _xml_file_dir = os.getenv(_env_var_xml_file_dir)
else:
    _xml_file_dir = None


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
    By default, :class:`ImageAcquirer` class internally uses Python's
    built-in :mod:`threading` module. However, you may want to use your
    preferred threading module such as :class:`QThread` of PyQt for some
    technical reasons. To allow us your preferred threading module, Harvester
    provides you a base proxy class to allow you implementing your threading
    functionality.
    """
    def __init__(self, *, mutex=None, logger=None):
        """

        :param mutex:
        :param logger:
        """

        #
        self._logger = logger or get_logger(name=__name__)

        #
        super().__init__()

        #
        self._is_running = False
        self._mutex = mutex

    def start(self):
        """

        :return: None.
        """

        self._is_running = True
        self._start()
        self._logger.debug(
            'Started thread {:0X}.'.format(self.id_)
        )

    def _start(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        Starts its worker running.

        :return: None.
        """
        raise NotImplementedError

    def stop(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        Stops its worker running.

        :return: None.
        """
        raise NotImplementedError

    def acquire(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        Acquires a mutex.

        :return: None.
        """
        raise NotImplementedError

    def release(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        Releases the acquired mutex.

        :return: None.
        """
        raise NotImplementedError

    @property
    def is_running(self):
        """
        :return: :const:`True` if the worker is still running. Otherwise :const:`False`.
        """
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value

    @property
    def worker(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
        """
        raise NotImplementedError

    @worker.setter
    def worker(self, obj):
        """
        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
        """
        raise NotImplementedError

    @property
    def mutex(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
        """
        raise NotImplementedError

    @property
    def id_(self):
        """
        This method is abstract and should be reimplemented in any sub-class.

        :return: None.
        """
        raise NotImplementedError


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


class _BuiltInThread(ThreadBase):
    def __init__(self, *, mutex=None, worker=None, logger=None,
                 sleep_duration=_sleep_duration_default):
        """

        :param mutex:
        :param worker:
        :param logger:
        :param sleep_duration:
        """

        #
        super().__init__(mutex=mutex, logger=logger)

        #
        self._thread = None
        self._worker = worker
        self._sleep_duration = sleep_duration

    def _start(self):
        # Create a Thread object. The object is not reusable.
        self._thread = _ThreadImpl(
            base=self, worker=self._worker,
            sleep_duration=self._sleep_duration
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
    def __init__(self, base=None, worker=None,
                 sleep_duration=_sleep_duration_default):
        """

        :param base:
        :param worker:
        :param sleep_duration:
        """

        #
        assert base

        #
        super().__init__(daemon=self._is_interactive())

        #
        self._worker = worker
        self._base = base
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
                time.sleep(self._sleep_duration)

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
    def data_format(self):
        """
        :return: The data type of the data component.
        """
        return self._buffer.data_format

    @property
    def data_format_namespace(self):
        """
        :return: The data type namespace of the data component.
        """
        return self._buffer.data_format

    @property
    def source_id(self):
        """
        :return: The source ID of the data component.
        """
        return self._buffer.source_id

    @property
    def data(self):
        """
        :return: The component data.
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
    def __init__(self, *, buffer=None, part=None, node_map=None):
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

        #
        self._part = part
        self._node_map = node_map
        self._data = None
        self._num_components_per_pixel = 0

        symbolic = self.data_format

        # Determine the data type:
        if self.x_padding > 0:
            # In this case, the client will have to trim the padding part.
            # so we create a NumPy array that consists of uint8 elements
            # first. The client will interpret the array in an appropriate
            # dtype in the end once he trimmed:
            dtype = 'uint8'
            bytes_per_pixel_data_component = 1
        else:
            if symbolic in uint16_formats:
                dtype = 'uint16'
                bytes_per_pixel_data_component = 2
            elif symbolic in uint32_formats:
                dtype = 'uint32'
                bytes_per_pixel_data_component = 4
            elif symbolic in float32_formats:
                dtype = 'float32'
                bytes_per_pixel_data_component = 4
            elif symbolic in uint8_formats:
                dtype = 'uint8'
                bytes_per_pixel_data_component = 1
            else:
                # Sorry, Harvester can't handle this:
                self._data = None
                return

        # Determine the number of components per pixel:
        if symbolic in lmn_444_location_formats:
            num_components_per_pixel = 3.
        elif symbolic in lmn_422_location_formats:
            num_components_per_pixel = 2.
        elif symbolic in lmn_411_location_formats:
            num_components_per_pixel = 1.5
        elif symbolic in lmno_4444_location_formats:
            num_components_per_pixel = 4.
        elif symbolic in mono_location_formats or \
                symbolic in bayer_location_formats:
            num_components_per_pixel = 1.
        else:
            # Sorry, Harvester can't handle this:
            self._data = None
            return

        self._num_components_per_pixel = num_components_per_pixel
        self._symbolic = symbolic

        #
        width = self.width
        height = self.height

        #
        if self._part:
            count = self._part.data_size
            count //= bytes_per_pixel_data_component
            data_offset = self._part.data_offset
        else:
            count = width * height
            count *= num_components_per_pixel
            count += self.y_padding
            data_offset = 0

        # Convert the Python's built-in bytes array to a Numpy array:
        self._data = np.frombuffer(
            self._buffer.raw_buffer,
            count=int(count),
            dtype=dtype,
            offset=data_offset
        )

    def represent_pixel_location(self):
        """
        Returns a NumPy array that represents the 2D pixel location,
        which is defined by PFNC, of the original image data.

        You may use the returned NumPy array for a calculation to map the
        original image to another format.

        :return: A NumPy array that represents the 2D pixel location.
        """
        if self.data is None:
            return None

        #
        return self._data.reshape(
            self.height + self.y_padding,
            int(self.width * self._num_components_per_pixel + self.x_padding)
        )

    @property
    def num_components_per_pixel(self):
        """
        :return: The number of data components per pixel.
        """
        return self._num_components_per_pixel

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
        :return: The width of the data component in the buffer in number of pixels.
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
        :return: The height of the data component in the buffer in number of pixels.
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
        :return: The data type of the data component as integer value.
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
        :return: The data type of the data component as string.
        """
        return symbolics[self.data_format_value]

    @property
    def delivered_image_height(self):
        """
        :return: The image height of the data component.
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
        :return: The X offset of the data in the buffer in number of pixels from the image origin to handle areas of interest.
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
        :return: The Y offset of the data in the buffer in number of pixels from the image origin to handle areas of interest.
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
        Returns
        :return: The X padding of the data component in the buffer in number of pixels.
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
        :return: The Y padding of the data component in the buffer in number of pixels.
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
    Is provided by an :class:`ImageAcquire` object when you call its
    :meth:`~harvesters.core.ImageAcquirer.fetch_buffer` method. It provides
    you a way to access acquired data and its relevant information.

    Note that it will never be necessary to create this object by yourself
    in general.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    def timestamp_ns(self):
        """
        :return: The timestamp in nano-second.
        """
        return self._buffer.timestamp_ns

    @property
    def timestamp(self):
        """
        :return: The timestamp in the TL specific unit.
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
        :return: The timestamp frequency which is used to represent a timestamp.
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
        :return: The payload type that the :class:`Buffer` object contains.
        """

        return self._buffer.payload_type

    @property
    def payload(self):
        """
        :return: A containing object which derives from :class:`PayloadBase` class.
        """
        return self._payload

    def queue(self):
        """
        Queues the buffer to prepare for the upcoming image acquisition. Once
        the buffer is queued, the :class:`Buffer` object will be obsolete.
        You'll have nothing to do with it.

        Note that you have to return the ownership of the fetched buffers to
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
    def _build_payload(*, buffer=None, node_map=None, logger=None):
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
                buffer.payload_type == PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_CHUNK_DATA:
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
    GenTL Standard.
    """
    def __init__(self, *, buffer=None, logger=None):
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
            return Component2DImage(buffer=buffer, part=part, node_map=node_map)

        return None

    @property
    def components(self):
        """
        :return: A :class:`list` containing objects that derive from :const:`ComponentBase` class.
        """
        return self._components


class PayloadUnknown(PayloadBase):
    """
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_UNKNOWN`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_IMAGE` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_RAW_DATA`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_FILE` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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


class PayloadJPEG(PayloadBase):
    """
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_JPEG` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_JPEG2000`
    by the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    Represents a payload that is classified as :const:`PAYLOAD_TYPE_H264` by
    the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    :const:`PAYLOAD_TYPE_CHUNK_ONLY` by the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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
    :const:`PAYLOAD_TYPE_MULTI_PART` by the GenTL Standard.
    """
    def __init__(self, *, buffer=None, node_map=None, logger=None):
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


class ImageAcquirer:
    """
    Manages everything you need to acquire images from the connecting device.
    """

    #
    _event = Event()
    _specialized_tl_type = ['U3V', 'GEV']

    def __init__(
            self, *, parent=None, device=None,
            profiler=None, logger=None,
            sleep_duration=_sleep_duration_default,
            file_path=None
    ):
        """

        :param parent:
        :param device:
        :param profiler:
        :param logger:
        :param sleep_duration:
        :param file_path: (Optional) Set a path to camera description file which you want to load on the target node map instead of the one which the device declares.
        """

        #
        self._logger = logger or get_logger(name=__name__)

        #
        assert parent
        assert device

        #
        super().__init__()

        #
        self._parent = parent

        #
        self._device = device
        self._device.node_map = _get_port_connected_node_map(
            port=self.device.remote_port, logger=self._logger,
            file_path=file_path
        )  # Remote device's node map

        #
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

        self._create_ds_at_connection = True
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
            sleep_duration=sleep_duration
        )

        # Prepare handling the SIGINT event:
        self._threads = []
        self._threads.append(self._thread_image_acquisition)

        self._sigint_handler = _SignalHandler(
            event=self._event, threads=self._threads, logger=self._logger
        )
        signal.signal(signal.SIGINT, self._sigint_handler)

        #
        self._num_filled_buffers_to_hold = 1

        #
        self._num_images_to_acquire = -1

        #
        self._timeout_for_image_acquisition = 1  # ms

        #
        self._statistics = Statistics()

        #
        self._announced_buffers = []
        self._holding_filled_buffers = []

        #
        self._has_acquired_1st_image = False
        self._is_acquiring_images = False
        self._keep_latest = True

        # Determine the default value:
        self._min_num_buffers = self._data_streams[0].buffer_announce_min
        self._num_buffers = max(
            16, self._data_streams[0].buffer_announce_min
        )

        #
        self._signal_stop_image_acquisition = None

        #
        self._logger.info(
            'Instantiated an ImageAcquirer object for {0}.'.format(
                self._device.id_
            )
        )

        #
        self._chunk_adapter = self._get_chunk_adapter(device=self._device)

        # A callback method when it's called when a new buffer is delivered:
        self._on_new_buffer_arrival = None

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
    def on_new_buffer_arrival(self):
        return self._on_new_buffer_arrival

    @on_new_buffer_arrival.setter
    def on_new_buffer_arrival(self, value):
        self._on_new_buffer_arrival = value

    @property
    def keep_latest(self):
        return self._keep_latest

    @keep_latest.setter
    def keep_latest(self, value):
        self._keep_latest = value

    @property
    def num_buffers(self):
        return self._num_buffers

    @num_buffers.setter
    def num_buffers(self, value):
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
    def num_filled_buffers_to_hold(self):
        return self._num_filled_buffers_to_hold

    @num_filled_buffers_to_hold.setter
    def num_filled_buffers_to_hold(self, value):
        if 0 < value <= self._num_buffers:
            self._num_filled_buffers_to_hold = value
        else:
            raise ValueError(
                'The number of filled buffers to hold must be '
                'greater than zero and '
                'smaller than or equal to {0}'.format(
                    self._num_buffers
                )
            )

    @property
    def num_holding_filled_buffers(self):
        return len(self._holding_filled_buffers)

    @property
    def device(self):
        """
        :return: The proxy :class:`Device` module object of the connecting remote device.
        """
        return self._device

    @property
    def interface(self):
        """
        :return: The parent :class:`Interface` module object of the connecting remote device.
        """
        return self._interface

    @property
    def system(self):
        """
        :return: The parent :class:`System` module object of the connecting remote device.
        """
        return self._system

    @property
    def is_acquiring_images(self):
        """
        :return: :const:`True` if it's acquiring images. Otherwise :const:`False`.
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
    def statistics(self):
        return self._statistics

    @keep_latest.setter
    def keep_latest(self, value):
        self._keep_latest = value

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

        # We're ready to start image acquisition. Lock the device's transport
        # layer related features:
        self.device.node_map.TLParamsLocked.value = 1

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

                if self.keep_latest:
                    # We want to keep the latest ones:
                    with MutexLocker(self.thread_image_acquisition):
                        if not self._is_acquiring_images:
                            return

                        if len(self._holding_filled_buffers) >= self._num_filled_buffers_to_hold:
                            # Pick up the oldest one:
                            buffer = self._holding_filled_buffers.pop(0)

                            if _is_logging_buffer_manipulation:
                                self._logger.debug(
                                    'Queued Buffer module #{0}'
                                    ' containing frame #{1}'
                                    ' to DataStream module {2}'
                                    ' of Device module {3}'
                                    '.'.format(
                                        buffer.context,
                                        buffer.frame_id,
                                        buffer.parent.id_,
                                        buffer.parent.parent.id_
                                    )
                                )
                            # Then discard/queue it:
                            buffer.parent.queue_buffer(buffer)

                    # Get the latest buffer:
                    buffer = event_manager.buffer

                    # Then append it to the list which the user fetches later:
                    self._holding_filled_buffers.append(buffer)

                    # Then update the statistics using the buffer:
                    self._update_statistics(buffer)
                else:
                    # Get the latest buffer:
                    buffer = event_manager.buffer

                    # Then update the statistics using the buffer:
                    self._update_statistics(buffer)

                    # We want to keep the oldest ones:
                    with MutexLocker(self.thread_image_acquisition):
                        if not self._is_acquiring_images:
                            return

                        if len(self._holding_filled_buffers) >= self._num_filled_buffers_to_hold:
                            # We have not space to keep the latest one.
                            # Discard/queue the latest buffer:
                            buffer.parent.queue_buffer(buffer)
                        else:
                            # Just append it to the list:
                            self._holding_filled_buffers.append(buffer)

            #
            if self._num_images_to_acquire >= 1:
                self._num_images_to_acquire -= 1

            if self._on_new_buffer_arrival:
                self._on_new_buffer_arrival()

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

    def fetch_buffer(self, *, timeout=0, is_raw=False):
        """
        Fetches the latest :class:`Buffer` object and returns it.

        :param timeout: Set timeout value in second.
        :param is_raw: Set :const:`True` if you need a raw GenTL Buffer module.

        :return: A :class:`Buffer` object.
        """
        if not self.is_acquiring_images:
            raise TimeoutException

        watch_timeout = True if timeout > 0 else False
        buffer = None
        base = time.time()

        while buffer is None:
            if watch_timeout and (time.time() - base) > timeout:
                raise TimeoutException
            else:
                with MutexLocker(self.thread_image_acquisition):
                    if len(self._holding_filled_buffers) > 0:
                        if is_raw:
                            buffer = self._holding_filled_buffers.pop(0)
                        else:
                            # Update the chunk data:
                            _buffer = self._holding_filled_buffers.pop(0)
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
                ' of DataStream module {2}'
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
        assert buffer

        #
        self._statistics.increment_num_images()
        self._statistics.update_timestamp(buffer)

    @staticmethod
    def _create_raw_buffers(num_buffers, size):
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
    def _create_buffer_tokens(raw_buffers):
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
                ' of Device module {2}'
                '.'.format(
                    buffer.context,
                    data_stream.id_,
                    data_stream.parent.id_
                )
            )

    def stop_image_acquisition(self):
        """
        Stops image acquisition.

        :return: None.
        """
        if self.is_acquiring_images:
            #
            self._is_acquiring_images = False

            #
            if self.thread_image_acquisition.is_running:  # TODO
                self.thread_image_acquisition.stop()

            with MutexLocker(self.thread_image_acquisition):
                #
                self.device.node_map.AcquisitionStop.execute()

                # Unlock TLParamsLocked in order to allow full device
                # configuration:
                self.device.node_map.TLParamsLocked.value = 0

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
        """
        Destroys the :class:`ImageAcquirer` object. Once you called this
        method, all allocated resources, including buffers and the remote
        device, are released.

        :return: None.
        """
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

        self._holding_filled_buffers.clear()
        self._announced_buffers.clear()


def _parse_description_file(*, port=None, url=None, file_path=None, logger=None):
    #
    file_name, text, bytes_object, content = None, None, None, None

    if file_path:
        file_name = os.path.basename(file_path)
        with open(file_path, 'r+b') as f:
            content = f.read()
            bytes_object = io.BytesIO(content)
    else:
        if url is None:
            # Inquire it's URL information.
            # TODO: Consider a case where len(url_info_list) > 1.
            if len(port.url_info_list) > 0:
                url = port.url_info_list[0].url
            else:
                return file_name, text, bytes_object

        if logger:
            logger.info('URL: {0}'.format(url))

        # And parse the URL.
        location, others = url.split(':', 1)
        location = location.lower()

        if location == 'local':
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
            bytes_object = io.BytesIO(content)

        elif location == 'file':
            # '///c|/program%20files/foo.xml' ->
            # '///', 'c|/program%20files/foo.xml'
            _, _file_path = others.split('///')

            # 'c|/program%20files/foo.xml' -> 'c|/program files/foo.xml'
            _file_path = unquote(_file_path)

            # 'c|/program files/foo.xml' -> 'c:/program files/foo.xml')
            _file_path.replace('|', ':')

            # Extract the file name from the file path:
            file_name = os.path.basename(_file_path)

            #
            with open(_file_path, 'r+b') as f:
                content = f.read()
                bytes_object = io.BytesIO(content)

        elif location == 'http' or location == 'https':
            raise NotImplementedError(
                'Failed to parse URL {0}: Harvester has not supported '
                'downloading a device description file from vendor '
                'web site.'.format(url)
            )
        else:
            raise LogicalErrorException(
                'Failed to parse URL {0}: Unknown format.'.format(url)
            )

    # Let's check the reality.
    if zipfile.is_zipfile(bytes_object):
        # Yes, that's a zip file.
        zipped_content = zipfile.ZipFile(bytes_object, 'r')

        # Extract the file content from the zip file.
        for file_info in zipped_content.infolist():
            if pathlib.Path(
                    file_info.filename).suffix.lower() == '.xml':
                #
                text = zipped_content.read(file_info)
                break
    else:
        text = content

    return file_name, text, bytes_object


def _get_port_connected_node_map(*, port=None, logger=None, file_path=None):
    #
    assert port

    #
    file_name, text, bytes_object = _parse_description_file(
        port=port, file_path=file_path, logger=logger
    )

    # There's no description file content to work with the node map:
    if (file_name is None) and (text is None) and (bytes_object is None):
        return None

    # Store the XML file if the client has specified a location:
    if _xml_file_dir:
        directory = _xml_file_dir
        # Create the directory if it didn't exist:
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Store the XML file:
        with open(os.path.join(directory, file_name), 'w+b') as f:
            f.write(bytes_object.getvalue())

    # Instantiate a GenICam node map object.
    node_map = NodeMap()

    # Then load the XML file content on the node map object.
    node_map.load_xml_from_string(text)

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
    Is the class that works for you as Harvester Core. Everything begins with
    this class.
    """
    #
    def __init__(self, *, profile=False, logger=None):
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        self.reset()

    @property
    def cti_files(self):
        """
        :return: A :class:`list` object containing :class:`str` objects.
        """
        return self._cti_files

    @property
    def device_info_list(self):
        """
        :return: A :class:`list` object containing :class:`DeviceInfo` objects
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
            serial_number=None, version=None,
            sleep_duration=_sleep_duration_default, file_path=None,
            privilege='exclusive'
        ):
        """
        Creates an image acquirer for the specified remote device and return
        the created :class:`ImageAcquirer` object.

        :param list_index: (Optional) Set an item index of the list of :class:`DeviceInfo` objects.
        :param id_: (Optional) Set an index of the device information list.
        :param vendor: (Optional) Set a vendor name of the target device.
        :param model: (Optional) Set a model name of the target device.
        :param tl_type: (Optional) Set a transport layer type of the target device.
        :param user_defined_name: (Optional) Set a user defined name string of the target device.
        :param serial_number: (Optional) Set a serial number string of the target device.
        :param version: (Optional) Set a version number string of the target device.
        :param sleep_duration: (Optional) Set a sleep duration in second that is inserted after the image acquisition worker is executed.
        :param file_path: (Optional) Set a path to camera description file which you want to load on the target node map instead of the one which the device declares.
        :param privilege: (Optional) Set an access privilege. `exclusive`, `contorl`, and `read_only` are supported. The default is `exclusive`.

        :return: An :class:`ImageAcquirer` object that associates with the specified device.

        Note that you have to close it when you are ready to release the
        device that you have been controlled. As long as you hold it, the
        controlled device will be not available from other clients.

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

            # Create an :class:`ImageAcquirer` object and return it.
            ia = ImageAcquirer(
                parent=self, device=device, profiler=self._profiler,
                logger=self._logger, sleep_duration=sleep_duration,
                file_path=file_path
            )
            self._ias.append(ia)

            if self._profiler:
                self._profiler.print_diff()

        return ia

    def add_cti_file(self, file_path: str):
        """
        Adds a CTI file to work with to the CTI file list.

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
        Removes the specified CTI file from the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None.
        """
        if file_path in self._cti_files:
            self._cti_files.remove(file_path)
            self._logger.info(
                'Removed {0} from the CTI file list.'.format(file_path)
            )

    def remove_cti_files(self):
        """
        Removes all CTI files in the CTI file list.

        :return: None.
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
