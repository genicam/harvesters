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
import unittest

# Related third party imports
from genicam2.gentl import TimeoutException

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvesterCoreBase
from harvesters.core import ImageAcquirer


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
        # Create an image acquirer:
        ia = self.harvester.create_image_acquirer(0)

        # We do not start image acquisition:
        #ia.start_image_acquisition()

        timeout = 3  # sec

        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will immediately raise
            # TimeoutException because it's not started image acquisition:
            _ = ia.fetch_buffer(timeout_s=timeout)

        # Then we setup the device for software trigger mode:
        ia.device.node_map.TriggerMode.value = 'On'
        ia.device.node_map.TriggerSource.value = 'Software'

        # We're ready to start image acquisition:
        ia.start_image_acquisition()

        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will raise TimeoutException
            # because we've not triggered the device so far:
            _ = ia.fetch_buffer(timeout_s=timeout)

        # We finally acquire an image triggering the device:
        buffer = None
        self.assertIsNone(buffer)

        ia.device.node_map.TriggerSoftware.execute()
        buffer = ia.fetch_buffer(timeout_s=timeout)
        self.assertIsNotNone(buffer)
        self._logger.info('{0}'.format(buffer))
        buffer.queue()

        # Now we stop image acquisition:
        ia.stop_image_acquisition()
        ia.destroy()


if __name__ == '__main__':
    unittest.main()
