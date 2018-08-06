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

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvesterCoreBase


class TestHarvesterCore(TestHarvesterCoreBase):
    @staticmethod
    def print_buffer(buffer):
        print('W: {0} x H: {1}, {2}, {3} elements\n{4}'.format(
            buffer.image.width,
            buffer.image.height,
            buffer.image.pixel_format,
            len(buffer.image.payload),
            buffer.image.payload
        ))

    def test_basic_usage(self):
        # Prepare an image acquisition agent for device #0.
        iaa = self._harvester.get_agent(0)

        # Set up the device.
        iaa.device.node_map.Width.value = 12
        iaa.device.node_map.Height.value = 8
        iaa.device.node_map.PixelFormat.value = 'Mono8'

        # Start image acquisition.
        iaa.start_image_acquisition()

        # Fetch a buffer that is filled with image data.
        with iaa.fetch_buffer() as buffer:
            self.print_buffer(buffer)
            # Reshape it.
            _1d = buffer.image.payload
            _2d = _1d.reshape(
                buffer.gentl_buffer.height, buffer.gentl_buffer.width
            )
            print(_2d)

        # Stop image acquisition.
        iaa.stop_image_acquisition()

        # Discard the image acquisition agent.
        iaa.close()

    def test_multiple_iaas(self):
        num_devices = len(self._harvester.device_info_list)
        self._test_image_acquisition_agents(num_iaas=num_devices)

    def _test_image_acquisition_agents(self, num_iaas=1):
        #
        print('Number of devices: {0}'.format(num_iaas))

        #
        iaas = []  # Image Acquisition Agents

        #
        for list_index in range(num_iaas):
            iaas.append(
                self._harvester.get_agent(
                    list_index=list_index
                )
                # Or you could simply do the same thing as follows:
                # self._harvester.get_agent(list_index)
            )

        #
        for i in range(10):
            #
            print('---> Round {0}: Set up'.format(i))
            for index, iaa in enumerate(iaas):
                iaa.start_image_acquisition()
                print(
                    'Device #{0} has started image acquisition.'.format(index)
                )

            k = 0

            # Run it as fast as possible.
            frames = 10

            while k < frames:
                for iaa in iaas:
                    if k % 2 == 0:
                        # Option 1: This way is secure and preferred.
                        try:
                            # We know we've started image acquisition but this
                            # try-except block is demonstrating a case where
                            # a client called fetch_buffer method even though
                            # he'd forgotten to start image acquisition.
                            with iaa.fetch_buffer() as buffer:
                                self.print_buffer(buffer)
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
                        buffer = iaa.fetch_buffer()
                        self.print_buffer(buffer)
                        iaa.queue_buffer(buffer)

                #
                k += 1

            #
            print('<--- Round {0}: Tear down'.format(i))
            for index, iaa in enumerate(iaas):
                iaa.stop_image_acquisition()
                print(
                    'Device #{0} has stopped image acquisition.'.format(index)
                )

        for iaa in iaas:
            iaa.close()

    def test_controlling_a_specific_camera(self):
        # The basic usage.
        iaa = self._harvester.get_agent(0)
        iaa.close()

        # The basic usage but it explicitly uses the parameter name.
        iaa = self._harvester.get_agent(
            list_index=0
        )
        iaa.close()

        # The key can't specify a unique device so it raises an exception.
        with self.assertRaises(ValueError):
            self._harvester.get_agent(
                vendor='EMVA_D'
            )

        # The key specifies a unique device.
        print(self._harvester.device_info_list)
        iaa = self._harvester.get_agent(
            serial_number='SN_InterfaceA_0'
        )
        iaa.close()


if __name__ == '__main__':
    unittest.main()
