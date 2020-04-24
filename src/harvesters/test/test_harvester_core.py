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
import os
from queue import Queue, Empty
from shutil import rmtree
import sys
from tempfile import gettempdir
from typing import Optional
import threading
import time
import unittest
from urllib.parse import quote

# Related third party imports
from genicam.gentl import TimeoutException
import numpy as np

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvesterCoreBase
from harvesters.test.base_harvester import get_cti_file_path
from harvesters.core import _retrieve_file_path
from harvesters.core import Callback
from harvesters.core import Harvester
from harvesters.core import ImageAcquirer
from harvesters.test.helper import get_package_dir
from harvesters.util.pfnc import Dictionary


class TestHarvesterCore(TestHarvesterCoreBase):
    sleep_duration = .5  # Time to keep sleeping [s]

    def test_basic_usage_1(self):
        """
        We walk through a basic usage and manually close the image
        acquirer.

        :return: None.
        """

        # Prepare an image acquirer for device #0.
        ia = self.harvester.create_image_acquirer(0)

        # Acquire images.
        self._basic_usage(ia)

        # Discard the image acquirer.
        ia.destroy()

    def test_basic_usage_2(self):
        """
        We walk through a basic usage and omit manually closing the image
        acquirer using the with statement.

        :return: None.
        """

        # Prepare an image acquirer for device #0.
        with self.harvester.create_image_acquirer(0) as ia:

            # Acquire images.
            self._basic_usage(ia)

    def _basic_usage(self, ia: ImageAcquirer):
        # Start image acquisition.
        ia.start_acquisition()

        # Fetch a buffer that is filled with image data.
        with ia.fetch_buffer() as buffer:
            # Reshape it.
            self._logger.info('{0}'.format(buffer))

        # Stop image acquisition.
        ia.stop_acquisition()

    def test_multiple_image_acquirers(self):
        num_devices = len(self.harvester.device_info_list)
        self._test_image_acquirers(num_ias=num_devices)

    def _test_image_acquirers(self, num_ias=1):
        #
        self._logger.info('Number of devices: {0}'.format(num_ias))

        #
        ias = []  # Image Acquirers

        #
        for list_index in range(num_ias):
            ias.append(
                self.harvester.create_image_acquirer(
                    list_index=list_index
                )
                # Or you could simply do the same thing as follows:
                # self.harvester.create_image_acquirer(list_index)
            )

        #
        for i in range(3):
            #
            self._logger.info('---> Round {0}: Set up'.format(i))
            for index, ia in enumerate(ias):
                ia.start_acquisition()
                self._logger.info(
                    'Device #{0} has started image acquisition.'.format(index)
                )

            k = 0

            # Run it as fast as possible.
            frames = 10

            while k < frames:
                for ia in ias:
                    if k % 2 == 0:
                        # Option 1: This way is secure and preferred.
                        try:
                            # We know we've started image acquisition but this
                            # try-except block is demonstrating a case where
                            # a client called fetch_buffer method even though
                            # he'd forgotten to start image acquisition.
                            with ia.fetch_buffer() as buffer:
                                self._logger.info('{0}'.format(buffer))
                        except AttributeError:
                            # Harvester Core has not started image acquisition
                            # so calling fetch_buffer() raises AttributeError
                            # because None object is used for the with
                            # statement.
                            pass
                    else:
                        # Option 2: You can manually do the same job but not
                        # recommended because you might forget to queue the
                        # buffer.
                        buffer = ia.fetch_buffer()
                        self._logger.info('{0}'.format(buffer))

                #
                k += 1

            #
            self._logger.info('<--- Round {0}: Tear down'.format(i))
            for index, ia in enumerate(ias):
                ia.stop_acquisition()
                self._logger.info(
                    'Device #{0} has stopped image acquisition.'.format(index)
                )

        for ia in ias:
            ia.destroy()

    def test_controlling_a_specific_camera(self):
        if not self.is_running_with_default_target():
            return

        # The basic usage.
        ia = self.harvester.create_image_acquirer(0)
        ia.destroy()

        # The basic usage but it explicitly uses the parameter name.
        ia = self.harvester.create_image_acquirer(
            list_index=0
        )
        ia.destroy()

        # The key can't specify a unique device so it raises an exception.
        with self.assertRaises(ValueError):
            self.harvester.create_image_acquirer(
                vendor='EMVA_D'
            )

        # The key specifies a unique device.
        self._logger.info(self.harvester.device_info_list)
        ia = self.harvester.create_image_acquirer(
            serial_number='SN_InterfaceA_0'
        )
        ia.destroy()

    def test_timeout_on_fetching_buffer(self):
        if not self.is_running_with_default_target():
            return

        # Create an image acquirer:
        ia = self.harvester.create_image_acquirer(0)

        # We do not start image acquisition:
        #ia.start_acquisition()

        timeout = 3  # sec

        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will immediately raise
            # TimeoutException because it's not started image acquisition:
            _ = ia.fetch_buffer(timeout=timeout)

        # Then we setup the device for software trigger mode:
        ia.remote_device.node_map.TriggerMode.value = 'On'
        ia.remote_device.node_map.TriggerSource.value = 'Software'

        # We're ready to start image acquisition:
        ia.start_acquisition()

        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will raise TimeoutException
            # because we've not triggered the device so far:
            _ = ia.fetch_buffer(timeout=timeout)

        # We finally acquire an image triggering the device:
        buffer = None
        self.assertIsNone(buffer)

        ia.remote_device.node_map.TriggerSoftware.execute()
        buffer = ia.fetch_buffer(timeout=timeout)
        self.assertIsNotNone(buffer)
        self._logger.info('{0}'.format(buffer))
        buffer.queue()

        # Now we stop image acquisition:
        ia.stop_acquisition()
        ia.destroy()

    def test_stop_start_and_stop(self):
        # Create an image acquirer:
        ia = self.harvester.create_image_acquirer(0)

        # It's not necessary but we stop image acquisition first;
        #
        ia.stop_acquisition()

        # Then start it:
        ia.start_acquisition()

        # Fetch a buffer to make sure it's working:
        with ia.fetch_buffer() as buffer:
            self._logger.info('{0}'.format(buffer))

        # Then stop image acquisition:
        ia.stop_acquisition()

        # And destroy the ImageAcquirer:
        ia.destroy()

    def test_num_holding_filled_buffers(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list:
        self.ia = self.harvester.create_image_acquirer(0)

        # Setup the camera before starting image acquisition:
        self.setup_camera()

        #
        tests = [
            self._test_issue_120_1
        ]
        for test in tests:
            for num_images in [1, 2, 4, 8]:
                #
                self.ia.num_filled_buffers_to_hold = num_images

                # Start image acquisition:
                self.ia.start_acquisition(run_in_background=True)

                # Run a test:
                test(num_images)

                # Stop image acquisition:
                self.ia.stop_acquisition()

    def _test_issue_120_1(self, num_images):
        # Make sure num_holding_filled_buffers is incremented every trigger:
        for i in range(num_images):
            #
            self.assertEqual(
                self.ia.num_holding_filled_buffers, i
            )

            # Trigger it:
            self.generate_software_trigger(sleep_s=self.sleep_duration)

            # It must be incremented:
            self.assertEqual(
                self.ia.num_holding_filled_buffers, i + 1
            )

        # Trigger it again, we know it's redundant compared to the
        # maximum capacity:
        self.generate_software_trigger(sleep_s=self.sleep_duration)

        # Make sure num_holding_filled_buffers does not exceed
        # num_filled_buffers_to_hold:
        self.assertEqual(
            self.ia.num_filled_buffers_to_hold,
            self.ia.num_holding_filled_buffers
        )

        # Make sure num_holding_filled_buffers is decreased every time
        # a filled buffer is fetched:
        for i in range(num_images):
            #
            self.assertEqual(
                self.ia.num_holding_filled_buffers,
                num_images - i
            )
            #
            with self.ia.fetch_buffer():
                #
                self.assertEqual(
                    self.ia.num_holding_filled_buffers,
                    num_images - (i + 1)
                )

    def setup_camera(self):
        self.ia.remote_device.node_map.AcquisitionMode.value = 'Continuous'
        self.ia.remote_device.node_map.TriggerMode.value = 'On'
        self.ia.remote_device.node_map.TriggerSource.value = 'Software'

    def generate_software_trigger(self, sleep_s=0.):
        # Trigger the camera because you have already setup your
        # equipment for the upcoming image acquisition.
        self.ia.remote_device.node_map.TriggerSoftware.execute()
        #
        if sleep_s > 0:
            time.sleep(sleep_s)

    def test_issue_59(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        #
        min = self.ia._data_streams[0].buffer_announce_min
        with self.assertRaises(ValueError):
            self.ia.num_buffers = min - 1

        #
        with self.assertRaises(ValueError):
            self.ia.num_filled_buffers_to_hold = 0

        #
        self.ia.num_filled_buffers_to_hold = min

    def test_issue_60(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        # Check the number of buffers:
        self.assertEqual(16, self.ia.num_buffers)

    @unittest.skip('It has been obsolete; see issue #141.')
    def test_issue_61(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        # Register a call back method:
        self.ia.on_new_buffer_arrival = self._callback_on_new_buffer_arrival

        # We turn software trigger on:
        self.setup_camera()

        # We have not fetched any buffer:
        self.assertEqual(0, len(self._buffers))

        # Start image acquisition:
        self.ia.start_acquisition(run_in_background=True)

        # Trigger the target device:
        num_images = self.ia.num_buffers
        self.assertTrue(num_images > 0)

        # Trigger the target device:
        for _ in range(num_images):
            self.generate_software_trigger(sleep_s=self.sleep_duration)

        # If the callback method was called, then we should have the same
        # number of buffers with num_images:
        self.assertEqual(num_images, len(self._buffers))

        # Release the buffers before stopping image acquisition:
        for buffer in self._buffers:
            buffer.queue()

        self._buffers.clear()

        # Then stop image acquisition:
        self.ia.stop_acquisition()

    def _callback_on_new_buffer_arrival(self):
        # Fetch a buffer and keep it:
        self._buffers.append(self.ia.fetch_buffer())

    def test_issue_66(self):
        if not self.is_running_with_default_target():
            return

        file_names = ['altered_plain.xml', 'altered_zip.zip']
        expected_values = ['plain', 'zip']
        for i, file_name in enumerate(file_names):
            self._test_issue_66(
                'issue_66_' + file_name, expected_values[i]
            )

    def _test_issue_66(self, file_name, expected_value):
        #
        xml_dir = self._get_xml_dir()

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(
            0, file_path=os.path.join(xml_dir, file_name)
        )

        # Compare DeviceModelNames:
        self.assertEqual(
            'Altered TLSimu (' + expected_value + ')',
            self.ia.remote_device.node_map.DeviceModelName.value
        )

        #
        self.ia.destroy()

    def test_issue_67(self):
        if not self.is_running_with_default_target():
            return

        file_names = ['altered_plain.xml', 'altered_zip.zip']
        for i, file_name in enumerate(file_names):
            self._test_issue_67(
                'issue_67_' + file_name
            )

    def _test_issue_67(self, expected_file_name):
        #
        xml_dir = self._get_xml_dir()

        #
        url = 'file://'
        file_path = xml_dir + '/' + expected_file_name

        # '\' -> '/'
        file_path.replace('\\', '/')

        # ':' -> '|'
        file_path.replace(':', '|')

        # ' ' -> '%20'
        file_path = quote(file_path)

        #
        url += file_path

        # Parse the URL:
        retrieved_file_path = _retrieve_file_path(url=url)

        # Compare file names:
        self.assertEqual(
            os.path.basename(retrieved_file_path),
            expected_file_name
        )

    def test_issue_121(self):
        #
        expected_file_path = '/Foo.xml'

        #
        url = 'file://' + expected_file_path
        retrieved_file_path = _retrieve_file_path(url=url)

        # Compare file names:
        self.assertEqual(
            retrieved_file_path,
            expected_file_path
        )

    @staticmethod
    def _get_xml_dir():
        return os.path.join(get_package_dir('harvesters'), 'test', 'xml')

    def test_issue_70(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list:
        self.ia = self.harvester.create_image_acquirer(0)

        # Then check the minimum buffer number that a client can ask
        # the ImageAcquire object to prepare:
        self.assertEqual(5, self.ia.min_num_buffers)

    def test_issue_78(self):
        if not self.is_running_with_default_target():
            return

        # The device_info_list must not turn empty even if a given key
        # does not match to any candidate:
        self._logger.info(self.harvester.device_info_list)
        device_info_list = self.harvester.device_info_list.copy()
        try:
            self.harvester.create_image_acquirer(
                serial_number='abcdefghijklmnopqrstuwxyz!#$%&=~|<>'
            )
        except ValueError:
            self.assertEqual(
                device_info_list, self.harvester.device_info_list
            )

    def test_issue_130_1(self):
        #
        self.ia = self.harvester.create_image_acquirer(0)
        #
        self.ia.start_acquisition(run_in_background=False)
        #
        with self.ia.fetch_buffer() as buffer:
            self.assertIsNotNone(buffer)
        #
        self.ia.stop_acquisition()

    def test_issue_141(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        # We turn software trigger on:
        self.setup_camera()

        # Create a callback:
        self.on_new_buffer_available = _OnNewBufferAvailable(
            ia=self.ia, buffers=self._buffers
        )
        self.on_return_buffer_now = _OnReturnBufferNow(
            holder=self.on_new_buffer_available
        )

        # Trigger the target device:
        self.num_images = self.ia.num_buffers
        self.assertTrue(self.num_images > 0)

        #
        tests = [
            self._test_141_with_callback, self._test_141_without_callback
        ]
        for test in tests:
            # We have not yet fetched any buffer:
            self.assertEqual(0, len(self.on_new_buffer_available.buffers))

            # Run a sub-test:
            test()

            # Then stop image acquisition:
            self.ia.stop_acquisition()

    def _test_141_with_callback(self):
        # Add it to the image acquire so that it can get notified when the
        # event happened:
        self.ia.add_callback(
            ImageAcquirer.Events.NEW_BUFFER_AVAILABLE,
            self.on_new_buffer_available
        )
        self.ia.add_callback(
            ImageAcquirer.Events.RETURN_ALL_BORROWED_BUFFERS,
            self.on_return_buffer_now
        )

        #
        self._test_141_body()

        # If the callback method was called, then we should have the same
        # number of buffers with num_images:
        self.assertEqual(
            self.ia.num_buffers, len(self.on_new_buffer_available.buffers)
        )

    def _test_141_without_callback(self):
        # Remove all callbacks to not any callback work:
        self.ia.remove_callbacks()
        
        #
        self._test_141_body()
        
        # The list must be empty because the emit method has not been called:
        self.assertEqual(
            0, len(self.on_new_buffer_available.buffers)
        )

    def _test_141_body(self):
        # Start image acquisition:
        self.ia.start_acquisition(run_in_background=True)

        # Trigger the target device:
        for _ in range(self.num_images):
            self.generate_software_trigger(sleep_s=self.sleep_duration)

    def test_issue_146(self):
        #
        tests = [
            self._test_issue_146_group_packed_10,
            self._test_issue_146_group_packed_12,
            self._test_issue_146_packed_10,
            self._test_issue_146_packed_12,
        ]
        #
        for test in tests:
            test()

    def _test_issue_146_group_packed_10(self):
        _1st = 0xff
        _3rd = 0xff
        ba = bytes([_1st, 0x33, _3rd])
        packed = np.frombuffer(ba, dtype=np.uint8)
        pf = Dictionary.get_proxy('BayerRG10Packed')
        unpacked = pf.expand(packed)
        self.assertEqual(_1st * 4 + 3, unpacked[0])
        self.assertEqual(_3rd * 4 + 3, unpacked[1])

    def _test_issue_146_group_packed_12(self):
        _1st = 0xff
        _3rd = 0xff
        ba = bytes([_1st, 0xff, _3rd])
        packed = np.frombuffer(ba, dtype=np.uint8)
        pf = Dictionary.get_proxy('BayerRG12Packed')
        unpacked = pf.expand(packed)
        self.assertEqual(_1st * 16 + 0xf, unpacked[0])
        self.assertEqual(_3rd * 16 + 0xf, unpacked[1])

    def _test_issue_146_packed_10(self):
        element = 0xff
        ba = bytes([element, element, element, element])
        packed = np.frombuffer(ba, dtype=np.uint8)
        pf = Dictionary.get_proxy('Mono10p')
        unpacked = pf.expand(packed)
        self.assertEqual(0x3ff, unpacked[0])
        self.assertEqual(0x3ff, unpacked[1])
        self.assertEqual(0x7ff, unpacked[2])

    def _test_issue_146_packed_12(self):
        _1st = 0xff
        _3rd = 0xff
        ba = bytes([_1st, 0xff, _3rd])
        packed = np.frombuffer(ba, dtype=np.uint8)
        pf = Dictionary.get_proxy('Mono12p')
        unpacked = pf.expand(packed)
        self.assertEqual(0xf * 256 + _1st, unpacked[0])
        self.assertEqual(_3rd * 16 + 0xf, unpacked[1])


class _TestIssue81(threading.Thread):
    def __init__(self, message_queue=None, cti_file_path=None):
        super().__init__()
        self._message_queue = message_queue
        self._cti_file_path = cti_file_path

    def run(self):
        h = Harvester()
        h.add_file(self._cti_file_path)
        h.update()
        try:
            ia = h.create_image_acquirer(0)
        except:
            # Transfer the exception anyway:
            self._message_queue.put(sys.exc_info())
        else:
            ia.start_acquisition()
            ia.stop_acquisition()
            ia.destroy()
            h.reset()


class TestIssue81(unittest.TestCase):
    _cti_file_path = get_cti_file_path()
    sys.path.append(_cti_file_path)

    def test_issue_81(self):
        message_queue = Queue()
        t = _TestIssue81(
            message_queue=message_queue, cti_file_path=self._cti_file_path
        )
        t.start()
        t.join()
        try:
            result = message_queue.get(block=False)
        except Empty:
            # Nothing happened; everything is fine.
            pass
        else:
            exception, message, backtrace = result
            # Transfer the exception:
            raise exception(message)


class TestIssue85(unittest.TestCase):
    _cti_file_path = get_cti_file_path()
    sys.path.append(_cti_file_path)

    def setUp(self) -> None:
        #
        self.env_var = 'HARVESTERS_XML_FILE_DIR'
        self.original = None if os.environ else os.environ[self.env_var]

    def tearDown(self) -> None:
        if self.original:
            os.environ[self.env_var] = self.original

    def test_issue_85(self):
        #
        temp_dir = os.path.join(
            gettempdir(), 'harvester', self.test_issue_85.__name__
        )

        #
        if os.path.isdir(temp_dir):
            rmtree(temp_dir)
        os.makedirs(temp_dir)

        #
        os.environ[self.env_var] = temp_dir

        #
        self.assertFalse(os.listdir(temp_dir))

        #
        with Harvester() as h:
            h.add_file(self._cti_file_path)
            h.update()
            with h.create_image_acquirer(0):
                # Check if XML files have been stored in the expected
                # directory:
                self.assertTrue(os.listdir(temp_dir))


class _OnNewBufferAvailable(Callback):
    def __init__(self, ia: ImageAcquirer, buffers: list):
        super().__init__()
        self._ia = ia
        self._buffers = buffers

    def emit(self, context: Optional[object] = None) -> None:
        buffer = self._ia.fetch_buffer()
        self._buffers.append(buffer)

    @property
    def buffers(self):
        return self._buffers


class _OnReturnBufferNow(Callback):
    def __init__(self, holder: _OnNewBufferAvailable):
        super().__init__()
        self._holder = holder
        
    def emit(self, context: Optional[object] = None) -> None:
        # Return/Queue the buffers before stopping image acquisition:
        while len(self._holder.buffers) > 0:
            buffer = self._holder.buffers.pop(-1)
            buffer.queue()


if __name__ == '__main__':
    unittest.main()
