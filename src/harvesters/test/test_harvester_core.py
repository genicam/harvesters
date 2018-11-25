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
import time
import unittest
from urllib.parse import quote

# Related third party imports
from genicam2.gentl import TimeoutException

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvesterCoreBase
from harvesters.core import _parse_description_file
from harvesters.core import ImageAcquirer
from harvesters.test.helper import get_package_dir


class TestHarvesterCore(TestHarvesterCoreBase):

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
        ia.start_image_acquisition()

        # Fetch a buffer that is filled with image data.
        with ia.fetch_buffer() as buffer:
            # Reshape it.
            self._logger.info('{0}'.format(buffer))

        # Stop image acquisition.
        ia.stop_image_acquisition()

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
                ia.start_image_acquisition()
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
                ia.stop_image_acquisition()
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
        #ia.start_image_acquisition()

        timeout = 3  # sec

        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will immediately raise
            # TimeoutException because it's not started image acquisition:
            _ = ia.fetch_buffer(timeout=timeout)

        # Then we setup the device for software trigger mode:
        ia.device.node_map.TriggerMode.value = 'On'
        ia.device.node_map.TriggerSource.value = 'Software'

        # We're ready to start image acquisition:
        ia.start_image_acquisition()

        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will raise TimeoutException
            # because we've not triggered the device so far:
            _ = ia.fetch_buffer(timeout=timeout)

        # We finally acquire an image triggering the device:
        buffer = None
        self.assertIsNone(buffer)

        ia.device.node_map.TriggerSoftware.execute()
        buffer = ia.fetch_buffer(timeout=timeout)
        self.assertIsNotNone(buffer)
        self._logger.info('{0}'.format(buffer))
        buffer.queue()

        # Now we stop image acquisition:
        ia.stop_image_acquisition()
        ia.destroy()

    def test_stop_start_and_stop(self):
        # Create an image acquirer:
        ia = self.harvester.create_image_acquirer(0)

        # It's not necessary but we stop image acquisition first:
        ia.stop_image_acquisition()

        # Then start it:
        ia.start_image_acquisition()

        # Fetch a buffer to make sure it's working:
        with ia.fetch_buffer() as buffer:
            self._logger.info('{0}'.format(buffer))

        # Then stop image acquisition:
        ia.stop_image_acquisition()

        # And destroy the ImageAcquirer:
        ia.destroy()

    def test_num_holding_filled_buffers(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        #
        num_images_to_acquire_default = 4

        # Setup the camera before starting image acquisition.
        self.setup_camera()

        # Then start image acquisition.
        self.ia.start_image_acquisition()

        # Setup your equipment then trigger the camera.
        self.generate_software_trigger()

        #
        self.ia.num_filled_buffers_to_hold = num_images_to_acquire_default

        #
        num_images_to_acquire = num_images_to_acquire_default

        # Accumulate the number of filled buffers that the ImageAcquirer
        # is holding:
        while num_images_to_acquire > 0:
            # Set up your equipment for the next image acquisition.
            self.generate_software_trigger()
            # We should have another reliable way to wait until the target
            # gets ready.
            time.sleep(0.01)
            num_images_to_acquire -= 1

        #
        num_images_to_acquire = num_images_to_acquire_default

        # Check the num_holding_filled_buffers is decreased every time
        # a filled buffer is fetched:
        while num_images_to_acquire > 0:
            #
            with self.ia.fetch_buffer():
                #
                self.assertEqual(
                    self.ia.num_holding_filled_buffers,
                    num_images_to_acquire - 1
                )

            num_images_to_acquire -= 1

    def setup_camera(self):
        self.ia.device.node_map.AcquisitionMode.value = 'Continuous'
        self.ia.device.node_map.TriggerMode.value = 'On'
        self.ia.device.node_map.TriggerSource.value = 'Software'

    def generate_software_trigger(self):
        # Trigger the camera because you have already setup your
        # equipment for the upcoming image acquisition.
        self.ia.device.node_map.TriggerSoftware.execute()

    def test_issue_59(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        #
        min = self.ia._data_streams[0].buffer_announce_min  # Warning: It's accessing a private member.
        with self.assertRaises(ValueError):
            self.ia.num_buffers = min - 1

        #
        max = self.ia.num_buffers
        with self.assertRaises(ValueError):
            self.ia.num_filled_buffers_to_hold = max + 1

        #
        self.ia.num_filled_buffers_to_hold = min
        self.ia.num_filled_buffers_to_hold = max

        #
        self.ia.num_buffers = min

    def test_issue_60(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        # Check the number of buffers:
        self.assertEqual(16, self.ia.num_buffers)

    def test_issue_61(self):
        if not self.is_running_with_default_target():
            return

        # Connect to the first camera in the list.
        self.ia = self.harvester.create_image_acquirer(0)

        # Register a call back method:
        self.ia.on_new_buffer_arrival = self._callback_on_new_buffer_arrival

        # We turn software tirrger on:
        self.setup_camera()

        # We have not fetched any buffer:
        self.assertEqual(0, len(self._buffers))

        # Start image acquisition:
        self.ia.start_image_acquisition()

        # Trigger the target device:
        num_images = self.ia.num_buffers
        self.assertTrue(num_images > 0)

        # Trigger the target device:
        for _ in range(num_images):
            self.generate_software_trigger()
            # Note that we should have another reliable way to confirm
            # FRAME_TRIGGER_WAIT.
            time.sleep(0.01)

        # If the callback method was called, then we should have the same
        # number of buffers with num_images:
        self.assertEqual(num_images, len(self._buffers))

        # Release the buffers before stopping image acquisition:
        for buffer in self._buffers:
            buffer.queue()

        self._buffers.clear()

        # Then stop image acquisition:
        self.ia.stop_image_acquisition()

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
            self.ia.device.node_map.DeviceModelName.value
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
        url = 'file:///'
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
        file_name, _, _ = _parse_description_file(url=url)

        # Compare file names:
        self.assertEqual(
            file_name, expected_file_name
        )

    @staticmethod
    def _get_xml_dir():
        return os.path.join(get_package_dir('harvesters'), 'test', 'xml')


if __name__ == '__main__':
    unittest.main()
