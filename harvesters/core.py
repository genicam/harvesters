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
from threading import Lock
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
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST, \
    TL_CHAR_ENCODING_LIST

# Local application/library specific imports
from harvesters._private.core.buffer import Buffer
from harvesters._private.core.port import ConcretePort
from harvesters._private.core.statistics import Statistics
from harvesters._private.core.thread import PyThread
from harvesters._private.core.thread_ import MutexLocker
from harvesters.processor import Processor
from harvesters._private.core.pfnc import symbolics
from harvesters._private.core.pfnc import uint8_formats, uint16_formats


class _ProcessorConvertPyBytesToNumpy1D(Processor):
    def __init__(self):
        #
        super().__init__(
            description='Converts a Python bytes object to a Numpy 1D array'
        )

    def process(self, input_buffer: Buffer):
        symbolic = None
        try:
            pixel_format_int = input_buffer.gentl_buffer.pixel_format
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

        output_buffer = Buffer(
            data_stream=input_buffer.data_stream,
            gentl_buffer=input_buffer.gentl_buffer,
            node_map=input_buffer.node_map,
            image=np.frombuffer(
                input_buffer.gentl_buffer.raw_buffer, dtype=dtype
            )
        )
        return output_buffer


class Harvester:
    def __init__(self, frontend=None, profile=False, min_num_buffers=16, parent=None):
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

        #
        self._frontend = frontend

        #
        self._is_acquiring_images = False

        #
        self._cti_files = []
        self._producers = []
        self._systems = []
        self._interfaces = []
        self._device_info_list = []
        self._concrete_port = None

        #
        self._announced_buffers = []
        self._fetched_buffers = []

        self._data_stream = None
        self._event_manager = None

        self._device = None

        #
        self._min_num_buffers = min_num_buffers
        self._num_extra_buffers = 1

        #
        self._has_revised_device_list = False
        self._timeout_for_update = 1000  # ms
        self._has_acquired_1st_image = False

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
        self._feature_tree_model = None

        #
        self._current_width = 0
        self._current_height = 0
        self._current_pixel_format = ''

        self._updated_statistics = None
        self._signal_stop_image_acquisition = None

        #
        self._statistics_update_cycle = 1  # s
        self._statistics_latest = Statistics()
        self._statistics_overall = Statistics()
        self._statistics_list = [
            self._statistics_latest, self._statistics_overall
        ]

        #
        self._timeout_for_image_acquisition = 1  # ms

        #
        self._processors = []
        self._system_defined_processors = [_ProcessorConvertPyBytesToNumpy1D()]
        self._user_defined_processors = []

        #
        self._num_images_to_acquire = -1
        self._commands = []

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
        self.reset()

    @property
    def updated_statistics(self):
        return self._updated_statistics

    @updated_statistics.setter
    def updated_statistics(self, obj):
        self._updated_statistics = obj

    @property
    def signal_stop_image_acquisition(self):
        return self._signal_stop_image_acquisition

    @signal_stop_image_acquisition.setter
    def signal_stop_image_acquisition(self, obj):
        self._signal_stop_image_acquisition = obj

    @property
    def device(self):
        return self._device

    @property
    def cti_files(self):
        return self._cti_files

    @property
    def is_acquiring_images(self):
        return self._is_acquiring_images

    @property
    def device_info_list(self):
        return self._device_info_list

    @property
    def timeout_for_update(self):
        return self._timeout_for_update

    @timeout_for_update.setter
    def timeout_for_update(self, ms):
        self._timeout_for_update = ms

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
    def has_revised_device_info_list(self):
        return self._has_revised_device_list

    @has_revised_device_info_list.setter
    def has_revised_device_info_list(self, value):
        self._has_revised_device_list = value

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

    def connect_device(self, item_id=0, id_info=None, model=None,
            serial_number=None, user_defined_name=None, vendor=None):
        """
        Connect the specified device to the Harvester object.

        :param item_id:
        :param id_info:
        :param model:
        :param serial_number:
        :param user_defined_name:
        :param vendor:

        :return: None.
        """
        #
        if self.device or self.device_info_list is None:
            # TODO: Throw an exception to tell clients that there's no
            # device to connect.
            return

        # Instantiate a GenTL Device module.
        self._device = \
            device=self.device_info_list[item_id].create_device()

        # Then open it.
        try:
            self.device.open(
                DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_EXCLUSIVE
            )
        except AccessDeniedException as e:
            print(e)
            self.disconnect_device()
        else:
            # And get an alias of its GenTL Port module.
            port = self.device.remote_port

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
            self.device.node_map = NodeMap()

            # Then load the XML file content on the node map object.
            self.device.node_map.load_xml_from_string(content)

            # Instantiate a concrete port object of the remote device's
            # port.
            self._concrete_port = ConcretePort(self.device.remote_port)

            # And finally connect the concrete port on the node map
            # object.
            self.device.node_map.connect(self._concrete_port, port.name)

            if self._profiler:
                self._profiler.print_diff()

    def disconnect_device(self):
        """
        Disconnect the device that has been connected to the Harvester
        object.

        :return: None.
        """
        #
        if self.device:
            if self.device.is_open():
                self.stop_image_acquisition()
                self.device.close()

            if self.device.node_map:
                self.device.node_map.disconnect()
            self.device.node_map = None

        self._device = None
        self._concrete_port = None

        if self._profiler:
            self._profiler.print_diff()

    def start_image_acquisition(self):
        """
        Starts image acquisition.

        :return: None.
        """
        if self.is_acquiring_images:
            # If it's pausing drawing images, just resume it and
            # immediately return this method.
            if self._frontend:
                if self._frontend.canvas.is_pausing:
                    self._frontend.canvas.resume_drawing()
        else:
            #
            self._data_stream = self.device.create_data_stream()
            self._data_stream.open(self.device.data_stream_ids[0])

            #
            num_required_buffers = self._min_num_buffers
            try:
                num_buffers = self._data_stream.buffer_announce_min
                if num_buffers < num_required_buffers:
                    num_buffers = num_required_buffers
            except InvalidParameterException as e:
                num_buffers = num_required_buffers

            if self._data_stream.defines_payload_size():
                buffer_size = self._data_stream.payload_size
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

            #
            event_token = self._data_stream.register_event(
                EVENT_TYPE_LIST.EVENT_NEW_BUFFER
            )
            self._event_manager = EventManagerNewBuffer(event_token)

            # Reset the number of images to acquire.
            try:
                acq_mode = self.device.node_map.AcquisitionMode.value
                if acq_mode == 'Continuous':
                    num_images_to_acquire = -1
                elif acq_mode == 'SingleFrame':
                    num_images_to_acquire = 1
                elif acq_mode == 'MultiFrame':
                    num_images_to_acquire = self.node_map.AcquisitionFrameCount.value
                else:
                    num_images_to_acquire = -1
            except LogicalErrorException:
                # The node doesn't exist.
                num_images_to_acquire = -1

            self._num_images_to_acquire = num_images_to_acquire

            # Update the sequence of image processors.
            self._processors = []

            for p in self._system_defined_processors:
                self._processors.append(p)

            for p in self.user_defined_processors:
                self._processors.append(p)

            # Start image acquisition.
            self._data_stream.start_acquisition(
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
                self._event_manager.update_event_data(
                    self._timeout_for_image_acquisition
                )
            else:
                return
        except TimeoutException as e:
            pass
        else:
            #
            if not self.is_acquiring_images:
                return

            gentl_buffer = self._event_manager.buffer

            #
            self._update_statistics(gentl_buffer)

            # Put the buffer in the process flow.
            input_buffer = Buffer(
                self._data_stream, gentl_buffer, self.device.node_map, None
            )
            output_buffer = None

            for p in self._processors:
                output_buffer = p.process(input_buffer)
                input_buffer = output_buffer

            if output_buffer:
                # We've got a new image so now we can reuse the buffer that
                # we had kept.
                with MutexLocker(self.thread_image_acquisition):
                    if len(self._fetched_buffers) > 0:
                        # We have a buffer now so we queue it; it's discarded
                        # before being used.
                        self.queue_buffer(self._fetched_buffers.pop(0))

                    if output_buffer.image.ndarray is not None:
                        # Append the recently fetched buffer.
                        # Then one buffer remains for our client.
                        self._fetched_buffers.append(output_buffer)

            #
            if self._num_images_to_acquire >= 1:
                self._num_images_to_acquire -= 1

            if self._num_images_to_acquire == 0:
                #
                if self.signal_stop_image_acquisition:
                    self.signal_stop_image_acquisition.emit()

    def fetch_buffer(self, timeout_ms=0):
        """
        Fetches the latest Buffer object and returns it.

        :param timeout_ms: Set timeout value in ms.
        :return: A Buffer object.
        """
        if not self.is_acquiring_images:
            return None

        watch_timeout = True if timeout_ms > 0 else False
        buffer = None
        base = time.time()

        while buffer is None:
            if watch_timeout and (time.time() - base) > timeout_ms:
                break
            else:
                with MutexLocker(self.thread_image_acquisition):
                    if len(self._fetched_buffers) > 0:
                        buffer = self._fetched_buffers.pop(0)

        return buffer

    def queue_buffer(self, buffer):
        """
        Queues the Buffer object.

        :param buffer: Set a Buffer object to queue.

        :return: None.
        """
        if self._data_stream and buffer:
            self._data_stream.queue_buffer(
                buffer.gentl_buffer
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
            announced_buffer = self._data_stream.announce_buffer(token)

            # And append it to the list.
            announced_buffers.append(announced_buffer)

        # Then return the list of announced Buffer objects.
        return announced_buffers

    def _queue_announced_buffers(self, buffers):
        for buffer in buffers:
            self._data_stream.queue_buffer(buffer)

    def stop_image_acquisition(self):
        """
        Stops image acquisition.

        :return: None.
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
                self._event_manager.flush_event_queue()

                # Stop image acquisition.
                try:
                    self._data_stream.stop_acquisition(
                        ACQ_STOP_FLAGS_LIST.ACQ_STOP_FLAGS_KILL
                    )
                except ResourceInUseException:
                    # Device throw RESOURCE_IN_USE exception
                    # if the acquisition has already terminated or
                    # it has not been started.
                    pass
                except TimeoutException as e:
                    print(e)

                self.device.node_map.AcquisitionStop.execute()

                # Flash the queue for image acquisition process.
                self._data_stream.flush_buffer_queue(
                    ACQ_QUEUE_TYPE_LIST.ACQ_QUEUE_ALL_DISCARD
                )

                # Unregister the registered event.
                self._event_manager.unregister_event()

                #
                self._release_data_stream()

            #
            self._initialize_buffers()

            for statistics in self._statistics_list:
                statistics.reset()

    def reset_statistics(self):
        self._current_width = self.device.node_map.Width.value
        self._current_height = self.device.node_map.Height.value
        self._current_pixel_format = self.device.node_map.PixelFormat.value

    def add_cti_file(self, file_path: str):
        """
        Adds a CTI file to work with to the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None.
        """
        if file_path not in self._cti_files:
            self._cti_files.append(file_path)

    def remove_cti_file(self, file_path: str):
        """
        Remove the specified CTI file from the CTI file list.

        :param file_path: Set a file path to the target CTI file.

        :return: None.
        """
        if file_path in self._cti_files:
            self._cti_files.remove(file_path)

    def discard_cti_files(self):
        """
        Remove all CTI files in the CTI file list.

        :return: None.
        """

        self._cti_files = []

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

        :return: None.
        """
        self.discard_cti_files()
        self._release_gentl_producers()

    def _release_gentl_producers(self):
        #
        self._release_systems()

        #
        for producer in self._producers:
            if producer and producer.is_open():
                producer.close()

        #
        self._producers = []

    def _release_systems(self):
        #
        self._release_interfaces()

        #
        for system in self._systems:
            if system is not None and system.is_open():
                system.close()

        #
        self._systems = []

    def _release_interfaces(self):
        #
        self._release_device_info_list()

        #
        if self._interfaces is not None:
            for iface in self._interfaces:
                if iface.is_open():
                    iface.close()

        #
        self._interfaces = []

    def _release_device_info_list(self):
        #
        self.disconnect_device()

        #
        if self.device_info_list is not None:
            self._device_info_list = []

    def _release_data_stream(self):
        #
        self._release_buffers()

        #
        if self._data_stream:
            if self._data_stream.is_open():
                self._data_stream.close()

        #
        self._data_stream = None
        self._event_manager = None

    def _release_buffers(self):
        #
        revoked_buffers = []
        if self._data_stream:
            for i, buffer in enumerate(self._announced_buffers):
                revoked_buffers.append(self._data_stream.revoke_buffer(buffer))

        self._announced_buffers = revoked_buffers

    def _initialize_buffers(self):
        self._fetched_buffers = []
        self._has_acquired_1st_image = False

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
