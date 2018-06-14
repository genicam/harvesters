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
#from scipy import ndimage

from genapi import NodeMap
from genapi import LogicalErrorException
from gentl import TimeoutException, AccessDeniedException, \
    LoadLibraryException, InvalidParameterException, \
    NotImplementedException, NotAvailableException, ClosedException, \
    ResourceInUseException
from gentl import GenTLProducer, BufferToken, EventManagerNewBuffer
from gentl import DEVICE_ACCESS_FLAGS_LIST, EVENT_TYPE_LIST, \
    ACQ_START_FLAGS_LIST, ACQ_STOP_FLAGS_LIST, ACQ_QUEUE_TYPE_LIST, \
    TL_CHAR_ENCODING_LIST

# Local application/library specific imports
from core.buffer import Buffer
from core.port import ConcretePort
from core.processor import Processor
from core.statistics import Statistics
from core.thread import PyThread
from core.thread_ import MutexLocker


class _FromBytesToNumpy1D(Processor):
    def __init__(self):
        #
        super().__init__(
            brief_description='Converts a Python bytes object to a Numpy 1D array'
        )

    def process(self, input_buffer: Buffer):
        output_buffer = Buffer(
            input_buffer.gentl_buffer,
            input_buffer.node_map,
            np.frombuffer(input_buffer.gentl_buffer.raw_buffer, dtype='uint8')
        )
        return output_buffer


class _FromNumpy1DToNumpy2D(Processor):
    def __init__(self):
        #
        super().__init__(
            brief_description='Reshape a Numpy 1D array into a Numpy 2D array')

    def process(self, input_buffer: Buffer):
        #
        symbolic = input_buffer.image.pixel_format

        #
        mono_formats = ['Mono8']
        rgb_formats = ['RGB8', 'RGB8Packed']
        bayer_formats = ['BayerGR8', 'BayerGB8', 'BayerRG8', 'BayerBG8']

        #
        ndarray = None
        try:
            if symbolic in mono_formats or symbolic in bayer_formats:
                ndarray = input_buffer.image.ndarray.reshape(
                    input_buffer.image.height, input_buffer.image.width
                )
            elif symbolic in rgb_formats:
                ndarray = input_buffer.image.ndarray.reshape(
                    input_buffer.image.height, input_buffer.image.width, 3
                )
        except ValueError as e:
            print(e)

        output_buffer = Buffer(
            input_buffer.gentl_buffer, input_buffer.node_map, ndarray
        )

        return output_buffer


class _Rotate(Processor):
    def __init__(self, angle=0):
        #
        super().__init__(brief_description='Rotate a Numpy 2D array')

        #
        self._angle = angle

    def process(self, input: Buffer):
        #
        #ndarray = ndimage.rotate(input.ndarray, self._angle)  # Import scipy.
        ndarray = None
        output = Buffer(
            input.gentl_buffer, input.node_map, ndarray
        )
        return output


class Harvester:
    #
    _encodings = {
        TL_CHAR_ENCODING_LIST.TL_CHAR_ENCODING_ASCII: 'ascii',
        TL_CHAR_ENCODING_LIST.TL_CHAR_ENCODING_UTF8: 'utf8'
    }

    def __init__(self, frontend=None, profile=False, min_num_buffers=16):
        #
        super().__init__()

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
        self._raw_buffers = []
        self._buffer_tokens = []
        self._announced_buffers = []
        self._fetched_buffers = []
        self._latest_buffer = None

        self._data_stream = None
        self._event_manager = None

        self._node_map = None
        self._connecting_device = None

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
        self._timeout_for_image_acquisition = 100  # ms

        #
        self._processors = []
        self.add_processor(_FromBytesToNumpy1D())
        self.add_processor(_FromNumpy1DToNumpy2D())
        # You may want to add other processors.

        #
        self._num_images_to_acquire = -1
        self._commands = []

        #
        if profile:
            from core.helper.profiler import Profiler
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
    def node_map(self):
        return self._node_map

    @property
    def connecting_device(self):
        return self._connecting_device

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
    def processors(self):
        return self._processors

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

    def add_processor(self, processor: Processor):
        self._processors.append(processor)

    def connect_device(self, index):
        if self.connecting_device:
            return

        # Instantiate a GenTL Device module.
        self._connecting_device = self._device_info_list[
            index].create_device()

        # Then open it.
        try:
            self.connecting_device.open(
                DEVICE_ACCESS_FLAGS_LIST.DEVICE_ACCESS_EXCLUSIVE
            )
        except AccessDeniedException as e:
            print(e)
            self.disconnect_device()
        else:
            # And get an alias of its GenTL Port module.
            port = self.connecting_device.remote_port

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
                        try:
                            # device -> interface -> system
                            encoding = self.connecting_device.parent.parent.char_encoding
                        except InvalidParameterException as e:
                            encoding = TL_CHAR_ENCODING_LIST.TL_CHAR_ENCODING_UTF8

                        #
                        content = file_content.read(file_info).decode(
                            self._encodings[encoding]
                        )
                        break

            # Instantiate a GenICam node map object.
            self._node_map = NodeMap()

            # Then load the XML file content on the node map object.
            self.node_map.load_xml_from_string(content)

            # Instantiate a concrete port object of the remote device's
            # port.
            self._concrete_port = ConcretePort(self.connecting_device.remote_port)

            # And finally connect the concrete port on the node map
            # object.
            self.node_map.connect(self._concrete_port, port.name)

            if self._profiler:
                self._profiler.print_diff()

    def disconnect_device(self):
        #
        if self.connecting_device:
            if self.connecting_device.is_open():
                self.stop_image_acquisition()
                self.connecting_device.close()

        if self._node_map:
            self._node_map.disconnect()
        self._node_map = None

        self._connecting_device = None
        self._concrete_port = None

        if self._profiler:
            self._profiler.print_diff()

    def start_image_acquisition(self):
        if self.is_acquiring_images:
            # If it's pausing drawing images, just resume it and
            # immediately return this method.
            if self._frontend:
                if self._frontend.canvas.is_pausing:
                    self._frontend.canvas.resume_drawing()
        else:
            #
            self._data_stream = self.connecting_device.create_data_stream()
            self._data_stream.open(self.connecting_device.data_stream_ids[0])

            #
            self._initialize_buffers()

            #
            num_required_buffers = self._min_num_buffers + self._num_extra_buffers
            try:
                num_buffers = self._data_stream.buffer_announce_min
                if num_buffers < num_required_buffers:
                    num_buffers = num_required_buffers
            except InvalidParameterException as e:
                num_buffers = num_required_buffers

            if self._data_stream.defines_payload_size():
                buffer_size = self._data_stream.payload_size
            else:
                buffer_size = self.node_map.PayloadSize.value

            self._raw_buffers = self._create_raw_buffers(
                num_buffers, buffer_size
            )
            self._buffer_tokens = self._create_buffer_tokens(
                self._raw_buffers
            )
            self._announced_buffers = self._announce_buffers(
                self._buffer_tokens
            )
            self._queue_announced_buffers(self._announced_buffers)

            #
            et = self._data_stream.register_event(
                EVENT_TYPE_LIST.EVENT_NEW_BUFFER
            )
            self._event_manager = EventManagerNewBuffer(et)

            # Reset the number of images to acquire.
            try:
                acq_mode = self.node_map.AcquisitionMode.value
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
            self.node_map.AcquisitionStart.execute()

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
            print(e)
        else:
            #
            if self._num_images_to_acquire >= 1:
                self._num_images_to_acquire -= 1

            #
            if not self.is_acquiring_images:
                return

            gentl_buffer = self._event_manager.buffer

            #
            self._update_statistics(gentl_buffer)

            #
            input_buffer = Buffer(gentl_buffer, self.node_map, None)
            output_buffer = None

            for p in self._processors:
                output_buffer = p.process(input_buffer)
                input_buffer = output_buffer

            #
            if not self._has_acquired_1st_image:
                if self._frontend:
                    self._frontend.canvas.set_rect(
                        output_buffer.image.width, output_buffer.image.height
                    )
                self._has_acquired_1st_image = True

            # We've got a new image so now we can reuse the buffer that
            # we had kept.
            with MutexLocker(self.thread_image_acquisition):
                if len(self._fetched_buffers) > self._num_extra_buffers:
                    # We have 2 buffers now so we queue the oldest buffer.
                    self.queue_buffer(self._fetched_buffers.pop(0))
                    # Then one buffer remains for our client.

                if output_buffer.image.ndarray is not None:
                    # Append the recently fetched buffer.
                    self._fetched_buffers.append(output_buffer)

            if self._num_images_to_acquire == 0:
                #
                if self.signal_stop_image_acquisition:
                    self.signal_stop_image_acquisition.emit()

    def fetch_buffer(self, timeout_ms=0):
        if not self.is_acquiring_images:
            return None

        watch_timeout = True if timeout_ms > 0 else False
        buffer = None

        while True:
            if watch_timeout and time.time() > timeout_ms:
                print('Detected timeout before fetching a buffer.')
                break
            else:
                if self._fetched_buffers:
                    # Return the oldest buffer.
                    buffer = self._fetched_buffers.pop(0)
                    break

        return buffer

    def queue_buffer(self, buffer):
        if self._data_stream:
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
                    frequency = self.connecting_device.timestamp_frequency
                except (InvalidParameterException, NotImplementedException,
                        NotAvailableException):
                    try:
                        frequency = self.node_map.GevTimestampTickFrequency.value
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

                self.node_map.AcquisitionStop.execute()

                # Flash the queue for image acquisition process.
                self._data_stream.flush_buffer_queue(
                    ACQ_QUEUE_TYPE_LIST.ACQ_QUEUE_ALL_DISCARD
                )

                # Unregister the registered event.
                self._event_manager.unregister_event()

                #
                self._release_data_stream()

            for statistics in self._statistics_list:
                statistics.reset()

    def reset_statistics(self):
        self._current_width = self.node_map.Width.value
        self._current_height = self.node_map.Height.value
        self._current_pixel_format = self.node_map.PixelFormat.value

    def add_cti_file(self, file_path: str):
        if file_path not in self._cti_files:
            self._cti_files.append(file_path)

    def remove_cti_file(self, file_path: str):
        if file_path in self._cti_files:
            self._cti_files.remove(file_path)

    def discard_cti_files(self):
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
        if self._data_stream:
            for buffer in self._announced_buffers:
                _ = self._data_stream.revoke_buffer(buffer)

    def _initialize_buffers(self):
        self._raw_buffers = []
        self._buffer_tokens = []
        self._announced_buffers = []
        self._fetched_buffers = []
        self._latest_buffer = None
        self._has_acquired_1st_image = False

    def update_device_info_list(self):
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
