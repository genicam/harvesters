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
import pathlib
from threading import Lock, Thread
import time
import zipfile

# Related third party imports
import numpy as np

from genicam2.genapi import NodeMap
from genicam2.genapi import LogicalErrorException
from genicam2.gentl import TimeoutException, AccessDeniedException, \
    LoadLibraryException, InvalidParameterException, \
    NotImplementedException, NotAvailableException, ClosedException, \
    ResourceInUseException
from genicam2.gentl import GenTLProducer, BufferToken, EventManagerNewBuffer
from genicam2.gentl import DEVICE_ACCESS_FLAGS_LIST, EVENT_TYPE_LIST, \
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST

# Local application/library specific imports
from harvesters._private.core.port import ConcretePort
from harvesters._private.core.statistics import Statistics
from harvesters.pfnc import symbolics
from harvesters.pfnc import uint8_formats, uint16_formats


class ThreadBase:
    def __init__(self, mutex=None):
        """

        :param mutex:
        """
        #
        super().__init__()

        #
        self._is_running = False
        self._mutex = mutex

    def start(self):
        self._is_running = True
        self._start()

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


class PyThread(ThreadBase):
    def __init__(self, mutex=None, worker=None):
        """
        
        :param mutex:
        :param worker:
        """
        #
        super().__init__(mutex=mutex)

        #
        self._thread = None
        self._worker = worker

    def _start(self):
        # Create a Thread object. The object is not reusable.
        self._thread = _PyThreadImpl(
            base=self,
            worker=self._worker
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


class _PyThreadImpl(Thread):
    def __init__(self, base=None, worker=None):
        #
        super().__init__()

        #
        self._worker = worker
        self._base = base

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


class BufferManager:
    def __init__(self, data_stream=None, buffer=None, node_map=None, payload=None):
        """

        :param data_stream:
        :param buffer:
        :param node_map:
        :param payload:
        """
        #
        super().__init__()

        #
        self._data_stream = data_stream
        self._buffer = buffer
        self._node_map = node_map
        self._payload = payload
        self._pixel_format = symbolics[int(self.buffer.pixel_format)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Queue the buffer when it goes outside of the scope.
        if self._data_stream and self._buffer:
            self._data_stream.queue_buffer(self._buffer)

    def __repr__(self):
        return 'W: {0} x H: {1}, {2}, {3} elements\n{4}'.format(
            self.buffer.width,
            self.buffer.height,
            self.pixel_format,
            len(self.payload),
            self.payload
        )

    @property
    def data_stream(self):
        return self._data_stream

    @property
    def buffer(self):
        return self._buffer

    @property
    def node_map(self):
        return self._node_map

    @property
    def payload(self):
        return self._payload

    @property
    def pixel_format(self):
        return self._pixel_format


class ProcessorBase:
    def __init__(self, description):
        """

        :param description: Set description about this process.
        """
        #
        super().__init__()

        #
        self._description = description
        self._processors = []

    @property
    def description(self):
        """

        :return: A description about this process.

        """
        return self._description

    def process(self, input):
        """

        :param input: Set an arbitrary object. It will be treated as the input source of the sequence of processes.

        :return: An arbitrary object as the output of the sequence of processes.
        """
        output = None

        for p in self._processors:
            output = p.process(input)
            input = output

        return output


class _ProcessorConvertPyBytesToNumpy1D(ProcessorBase):
    def __init__(self):
        #
        super().__init__(
            description='Converts a Python bytes object to a Numpy 1D array'
        )

    def process(self, input: BufferManager):
        symbolic = None
        try:
            pixel_format_int = input.buffer.pixel_format
        except InvalidParameterException:
            pass
        else:
            symbolic = symbolics[int(pixel_format_int)]

        if symbolic in uint8_formats:
            dtype = 'uint8'
        elif symbolic in uint16_formats:
            dtype = 'uint16'
        else:
            dtype = 'uint8'

        output = BufferManager(
            data_stream=input.data_stream,
            buffer=input.buffer,
            node_map=input.node_map,
            payload=np.frombuffer(
                input.buffer.raw_buffer, dtype=dtype
            )
        )
        return output


class ImageAcquisitionManager:
    def __init__(
            self, data_type='numpy', min_num_buffers=16, device=None,
            frontend=None, profiler=None
    ):
        #
        super().__init__()

        #
        self._device = device
        self._device.node_map = _get_port_connected_node_map(
            self.device.remote_port
        )  # Remote device's node map
        self._device.local_node_map = _get_port_connected_node_map(
            self.device.local_port
        )  # Local device's node map

        #
        self._interface = self._device.parent
        self._interface.local_node_map = _get_port_connected_node_map(
            self._interface.port
        )

        #
        self._system = self._interface.parent
        self._system.local_node_map = _get_port_connected_node_map(
            self._system.port
        )

        #
        self._data_streams = []
        self._event_managers = []
        self._setup_ds_and_event_manager()

        #
        self._frontend = frontend
        self._profiler = profiler

        #
        self._mutex = Lock()
        self._thread_image_acquisition = PyThread(
            mutex=self._mutex,
            worker=self._worker_image_acquisition
        )
        self._thread_statistics_measurement = PyThread(
            mutex=self._mutex,
            worker=self._worker_acquisition_statistics
        )

        #
        self._current_width = 0
        self._current_height = 0
        self._current_pixel_format = ''

        #
        self._processors = []
        self._system_defined_processors = []

        if data_type == 'numpy':  # numpy.ndarray
            self._system_defined_processors.append(
                _ProcessorConvertPyBytesToNumpy1D()
            )
        elif data_type == 'bytes':  # Python built-in 'bytes'
            pass

        #
        self._user_defined_processors = []

        #
        self._num_images_to_hold_min = 1
        self._num_images_to_hold = self._num_images_to_hold_min

        #
        self._num_images_to_acquire = -1

        #
        self._timeout_for_image_acquisition = 1  # ms

        #
        self._statistics_update_cycle = 1  # s
        self._statistics_latest = Statistics()
        self._statistics_overall = Statistics()
        self._statistics_list = [
            self._statistics_latest, self._statistics_overall
        ]

        #
        self._announced_buffers = []
        self._fetched_buffer_managers = []

        #
        self._has_acquired_1st_image = False

        #
        self._updated_statistics = None
        self._signal_stop_image_acquisition = None

        #
        self._is_acquiring_images = False

        #
        self._min_num_buffers = min_num_buffers

        self._feature_tree_model = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        self.destroy()

    @property
    def device(self):
        return self._device

    @property
    def interface(self):
        return self._interface

    @property
    def system(self):
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
    def updated_statistics(self):
        return self._updated_statistics

    @updated_statistics.setter
    def updated_statistics(self, obj):
        self._updated_statistics = obj

    @property
    def timeout_for_image_acquisition(self):
        return self._timeout_for_image_acquisition

    @timeout_for_image_acquisition.setter
    def timeout_for_image_acquisition(self, ms):
        with MutexLocker(self.thread_image_acquisition):
            self._timeout_for_image_acquisition = ms

    @property
    def user_defined_processors(self):
        return self._user_defined_processors

    @property
    def num_images_to_hold(self):
        return self._num_images_to_hold

    @num_images_to_hold.setter
    def num_images_to_hold(self, value):
        if value >= self._num_images_to_hold_min:
            self._num_images_to_hold = value
        else:
            self._num_images_to_hold = self._num_images_to_hold_min

    @property
    def thread_image_acquisition(self):
        return self._thread_image_acquisition

    @thread_image_acquisition.setter
    def thread_image_acquisition(self, obj):
        self._thread_image_acquisition = obj
        self._thread_image_acquisition.worker = self._worker_image_acquisition

    @property
    def thread_statistics_measurement(self):
        return self._thread_statistics_measurement

    @thread_statistics_measurement.setter
    def thread_statistics_measurement(self, obj):
        self._thread_statistics_measurement = obj
        self._thread_statistics_measurement.worker = self._worker_acquisition_statistics

    @property
    def signal_stop_image_acquisition(self):
        return self._signal_stop_image_acquisition

    @property
    def feature_tree_model(self):
        return self._feature_tree_model

    @feature_tree_model.setter
    def feature_tree_model(self, value):
        self._feature_tree_model = value

    @signal_stop_image_acquisition.setter
    def signal_stop_image_acquisition(self, obj):
        self._signal_stop_image_acquisition = obj

    def _setup_ds_and_event_manager(self):
        #
        for i, stream_id in enumerate(self._device.data_stream_ids):
            data_stream = self._device.create_data_stream()
            data_stream.open(stream_id)
            data_stream.local_node_map = _get_port_connected_node_map(
                data_stream.port
            )

            # Create an Event Manager object for image acquisition.
            event_token = data_stream.register_event(
                EVENT_TYPE_LIST.EVENT_NEW_BUFFER
            )

            self._event_managers.append(EventManagerNewBuffer(event_token))
            self._data_streams.append(data_stream)

    def start_image_acquisition(self):
        """
        Starts image acquisition.

        :return: None
        """
        if self.is_acquiring_images:
            # If it's pausing drawing images, just resume it and
            # immediately return this method.
            if self._frontend:
                if self._frontend.canvas.is_pausing:
                    self._frontend.canvas.resume_drawing()
        else:
            #
            num_required_buffers = self._min_num_buffers
            try:
                num_buffers = self._data_streams[0].buffer_announce_min
                if num_buffers < num_required_buffers:
                    num_buffers = num_required_buffers
            except InvalidParameterException as e:
                num_buffers = num_required_buffers

            if self._data_streams[0].defines_payload_size():
                buffer_size = self._data_streams[0].payload_size
            else:
                buffer_size = self.device.node_map.PayloadSize.value

            raw_buffers = self._create_raw_buffers(
                num_buffers, buffer_size
            )
            buffer_tokens = self._create_buffer_tokens(
                raw_buffers
            )

            self._announced_buffers = self._announce_buffers(
                buffer_tokens
            )
            self._queue_announced_buffers(self._announced_buffers)

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
            except LogicalErrorException:
                # The node doesn't exist.
                num_images_to_acquire = -1

            self._num_images_to_acquire = num_images_to_acquire

            # Update the sequence of image processors.
            self._processors.clear()

            for p in self._system_defined_processors:
                self._processors.append(p)

            for p in self.user_defined_processors:
                self._processors.append(p)

            # Start image acquisition.
            self._data_streams[0].start_acquisition(
                ACQ_START_FLAGS_LIST.ACQ_START_FLAGS_DEFAULT,
                self._num_images_to_acquire
            )

            #
            self._is_acquiring_images = True

            #
            self.reset_statistics()
            if self.thread_statistics_measurement:
                self.thread_statistics_measurement.start()

            #
            if self.thread_image_acquisition:
                self.thread_image_acquisition.start()

            #
            self.device.node_map.AcquisitionStart.execute()

    def _worker_acquisition_statistics(self):
        if not self.is_acquiring_images:
            return

        time.sleep(self._statistics_update_cycle)

        with MutexLocker(self.thread_statistics_measurement):
            #
            if self._frontend:
                #
                message_config = 'W: {0} x H: {1}, {2}, '.format(
                    self._current_width,
                    self._current_height,
                    self._current_pixel_format,
                )

                #
                message_latest = ''
                if self._statistics_latest.num_images > 0:
                    message_latest = '{0:.1f} fps in the last {1:.1f} s, '.format(
                        self._statistics_latest.fps,
                        self._statistics_update_cycle
                    )

                #
                message_overall = '{0:.1f} fps in the last {1}, {2} images'.format(
                    self._statistics_overall.fps,
                    str(datetime.timedelta(
                        seconds=int(self._statistics_overall.elapsed_time_s)
                    )),
                    self._statistics_overall.num_images
                )

                #
                if self.updated_statistics:
                    self.updated_statistics.emit(
                        '{0}'.format(
                            message_config + message_latest + message_overall
                        )
                    )

            self._statistics_latest.reset()

    def _worker_image_acquisition(self):
        try:
            if self.is_acquiring_images:
                time.sleep(0.001)
                self._event_managers[0].update_event_data(
                    self._timeout_for_image_acquisition
                )
            else:
                return
        except TimeoutException as e:
            pass
        else:
            #
            buffer = self._event_managers[0].buffer

            #
            self._update_statistics(buffer)

            # Put the buffer in the process flow.
            input = BufferManager(
                data_stream=self._data_streams[0],
                buffer=buffer,
                node_map=self.device.node_map,
                payload=None
            )
            output = None

            for p in self._processors:
                output = p.process(input)
                input = output

            if output:
                # We've got a new image so now we can reuse the buffer that
                # we had kept.
                with MutexLocker(self.thread_image_acquisition):
                    if len(self._fetched_buffer_managers) >= self._num_images_to_hold:
                        # We have a buffer now so we queue it; it's discarded
                        # before being used.
                        self.queue_buffer(self._fetched_buffer_managers.pop(0))

                    if output.payload is not None:
                        # Append the recently fetched buffer.
                        # Then one buffer remains for our client.
                        self._fetched_buffer_managers.append(output)

            #
            if self._num_images_to_acquire >= 1:
                self._num_images_to_acquire -= 1

            if self._num_images_to_acquire == 0:
                #
                if self.signal_stop_image_acquisition:
                    self.signal_stop_image_acquisition.emit()

    def fetch_buffer_manager(self, timeout_ms=0):
        """
        Fetches the oldest :class:`~harvesters.buffer.Buffer` object and returns it.

        :param timeout_ms: Set timeout value in ms.

        :return: A :class:`~harvesters.buffer.Buffer` object.
        """
        if not self.is_acquiring_images:
            return None

        watch_timeout = True if timeout_ms > 0 else False
        bm = None
        base = time.time()

        while bm is None:
            if watch_timeout and (time.time() - base) > timeout_ms:
                break
            else:
                with MutexLocker(self.thread_image_acquisition):
                    if len(self._fetched_buffer_managers) > 0:
                        bm = self._fetched_buffer_managers.pop(0)

        return bm

    def queue_buffer(self, buffer_manager: BufferManager):
        """
        Queues a buffer for the image acquisition.

        :param buffer_manager: Set a :class:`~harvesters.core.BufferManager` object that is holding a buffer to queue.

        :return: None
        """
        if self._data_streams[0] and buffer_manager:
            self._data_streams[0].queue_buffer(
                buffer_manager.buffer
            )

    def _update_statistics(self, gentl_buffer):
        #
        frequency = 1000000000.  # Hz
        try:
            timestamp = gentl_buffer.timestamp_ns
        except (InvalidParameterException, NotImplementedException, NotAvailableException):
            try:
                # The unit is device/implementation dependent.
                timestamp = gentl_buffer.timestamp
            except (NotImplementedException, NotAvailableException):
                timestamp = 0  # Not available
            else:
                try:
                    frequency = self.device.timestamp_frequency
                except (InvalidParameterException, NotImplementedException,
                        NotAvailableException):
                    try:
                        frequency = self.device.node_map.GevTimestampTickFrequency.value
                    except LogicalErrorException:
                        pass

        #
        for statistics in self._statistics_list:
            statistics.increment_num_images()
            statistics.set_timestamp(timestamp, frequency)

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

    def _announce_buffers(self, _buffer_tokens):
        #
        announced_buffers = []

        # Iterate announcing buffers in the Buffer Tokens.
        for token in _buffer_tokens:
            # Get an announced buffer.
            announced_buffer = self._data_streams[0].announce_buffer(token)

            # And append it to the list.
            announced_buffers.append(announced_buffer)

        # Then return the list of announced Buffer objects.
        return announced_buffers

    def _queue_announced_buffers(self, buffers):
        for buffer in buffers:
            self._data_streams[0].queue_buffer(buffer)

    def stop_image_acquisition(self):
        """
        Stops image acquisition.

        :return: None
        """
        if self.is_acquiring_images:
            #
            self._is_acquiring_images = False

            #
            if self.thread_image_acquisition.is_running:
                self.thread_image_acquisition.stop()

            if self.thread_statistics_measurement.is_running:
                self.thread_statistics_measurement.stop()

            with MutexLocker(self.thread_image_acquisition):
                #
                self.device.node_map.AcquisitionStop.execute()

                # Stop image acquisition.
                try:
                    self._data_streams[0].stop_acquisition(
                        ACQ_STOP_FLAGS_LIST.ACQ_STOP_FLAGS_KILL
                    )
                except ResourceInUseException:
                    # Device throw RESOURCE_IN_USE exception
                    # if the acquisition has already terminated or
                    # it has not been started.
                    pass
                except TimeoutException as e:
                    print(e)

                # Flash the queue for image acquisition process.
                self._data_streams[0].flush_buffer_queue(
                    ACQ_QUEUE_TYPE_LIST.ACQ_QUEUE_ALL_DISCARD
                )

                #
                self._event_managers[0].flush_event_queue()

                #
                # Release buffers but keep holding the Data Stream module.
                self._release_buffers()

            #
            self._initialize_buffers()

            for statistics in self._statistics_list:
                statistics.reset()

    def reset_statistics(self):
        self._current_width = self.device.node_map.Width.value
        self._current_height = self.device.node_map.Height.value
        self._current_pixel_format = self.device.node_map.PixelFormat.value

    def destroy(self):
        """
        Releases all external resources including the controlling device.

        :return: None

        Please don't forget to call this method if you create an image acquisition manager without using the with method.
        """
        #
        if self.device:
            #
            self.stop_image_acquisition()
            self._release_data_streams()

            #
            if self.device.node_map:
                self.device.node_map.disconnect()

            #
            if self._device.is_open():
                self._device.close()

        self._device = None
        self._event_managers.clear()

        if self._profiler:
            self._profiler.print_diff()

    def _release_data_streams(self):
        #
        self._release_buffers()

        #
        for ds in self._data_streams:
            if ds and ds.is_open():
                ds.close()

        #
        self._data_streams.clear()

    def _release_buffers(self):
        for ds in self._data_streams:
            if ds and ds.is_open():
                #
                for buffer in self._announced_buffers:
                    ds.revoke_buffer(buffer)
                self._announced_buffers.clear()

        self._fetched_buffer_managers.clear()
        self._announced_buffers.clear()

    def _initialize_buffers(self):
        self._fetched_buffer_managers.clear()
        self._has_acquired_1st_image = False


def _get_port_connected_node_map(port=None):
    # Inquire it's URL information.
    # TODO: Consider a case where len(url_info_list) > 1.
    url = port.url_info_list[0].url

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
    def __init__(
            self, frontend=None, profile=False, parent=None
    ):
        """
        Is a Python class that works as Harvester Core. You can image
        acquisition related task through this class.

        :param frontend:
        :param profile:
        :param min_num_buffers:
        :param parent:
        """
        #
        super().__init__()

        #
        self._parent = parent
        self._frontend = frontend

        #
        self._cti_files = []
        self._producers = []
        self._systems = []
        self._interfaces = []
        self._device_info_list = []

        #
        self._has_revised_device_list = False
        self._timeout_for_update = 1000  # ms

        #
        if profile:
            from harvesters._private.core.helper import Profiler
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

    def create_image_acquisition_manager(
            self, list_index=None, data_type='numpy', unique_id=None,
            vendor=None, model=None, tl_type=None, user_defined_name=None,
            serial_number=None, version=None,
        ):
        """
        Opens an image acquisition manager for the specified device and return it.

        :param list_index: Set an item index of the list of :class:`~genicam2.gentl.DeviceInfo` objects.
        :param data_type: Set a data type that you want to have. The default is numpy's ndarray.
        :param unique_id:
        :param vendor:
        :param model:
        :param tl_type:
        :param user_defined_name:
        :param serial_number:
        :param version:

        :return: None

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
                'unique_id', 'vendor', 'model', 'tl_type',
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
                        except (AttributeError, NotAvailableException):
                            # The candidate doesn't support the information.
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
        except (AccessDeniedException, ResourceInUseException):
            return None

        # Create an image acquisition manager object and return it.
        iaa = ImageAcquisitionManager(
            data_type=data_type, device=device, frontend=self._frontend
        )

        if self._profiler:
            self._profiler.print_diff()

        return iaa

    def add_cti_file(self, file_path: str):
        """
        Adds a CTI file to work with to the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None
        """
        if file_path not in self._cti_files:
            self._cti_files.append(file_path)

    def remove_cti_file(self, file_path: str):
        """
        Remove the specified CTI file from the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None
        """
        if file_path in self._cti_files:
            self._cti_files.remove(file_path)

    def remove_cti_files(self):
        """
        Removes all CTI files in the CTI file list.

        :return: None
        """

        self._cti_files.clear()

    def _open_gentl_producers(self):
        #
        for file_path in self._cti_files:
            producer = GenTLProducer.create_producer()
            try:
                producer.open(file_path)
            except ClosedException as e:
                print(e)
            else:
                self._producers.append(producer)

    def _open_systems(self):
        for producer in self._producers:
            system = producer.create_system()
            try:
                system.open()
            except ClosedException as e:
                print(e)
            else:
                self._systems.append(system)

    def reset(self):
        """
        Initializes the Harvester object.

        :return: None
        """
        self.remove_cti_files()
        self._release_gentl_producers()

    def _release_gentl_producers(self):
        #
        self._release_systems()

        #
        for producer in self._producers:
            if producer and producer.is_open():
                producer.close()

        #
        self._producers.clear()

    def _release_systems(self):
        #
        self._release_interfaces()

        #
        for system in self._systems:
            if system is not None and system.is_open():
                system.close()

        #
        self._systems.clear()

    def _release_interfaces(self):
        #
        self._release_device_info_list()

        #
        if self._interfaces is not None:
            for iface in self._interfaces:
                if iface.is_open():
                    iface.close()

        #
        self._interfaces.clear()

    def _release_device_info_list(self):
        #
        if self.device_info_list is not None:
            self._device_info_list.clear()

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
                    iface.open()
                    iface.update_device_info_list(self.timeout_for_update)
                    self._interfaces.append(iface)
                    for d_info in iface.device_info_list:
                        self.device_info_list.append(d_info)

        except LoadLibraryException as e:
            print(e)
            self._has_revised_device_list = False
        else:
            self._has_revised_device_list = True


if __name__ == '__main__':
    pass
