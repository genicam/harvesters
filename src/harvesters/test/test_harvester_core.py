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
from genicam.genapi import GenericException as GenApi_GenericException
from genicam.genapi import NodeMap
from genicam.gentl import TimeoutException
import numpy as np

# Local application/library specific imports
from harvesters._private.core.helper.system import is_running_on_windows
from harvesters.test.base_harvester import TestHarvester, \
    TestHarvesterNoCleanUp
from harvesters.test.base_harvester import get_cti_file_path
from harvesters.core import Callback
from harvesters.core import Harvester, Interface
from harvesters.core import ParameterSet, ParameterKey
from harvesters.core import ImageAcquirer
from harvesters.core import _drop_padding_data
from harvesters.core import Module
from harvesters.test.helper import get_package_dir
from harvesters.util.pfnc import Dictionary
from harvesters.core import Component2DImage
from harvesters.util.pfnc import Mono8, Mono10, Mono12, Mono14, Mono16
from harvesters.util.pfnc import Mono10Packed, Mono12Packed
from harvesters.util.pfnc import Mono10p, Mono12p, Mono14p
from harvesters.util.pfnc import RGB10p, BGR10p
from harvesters.util.pfnc import RGB12p, BGR12p


class TestHarvesterCoreNoCleanUp(TestHarvesterNoCleanUp):
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
            0, file_path=os.path.join(xml_dir, file_name))

        # Compare DeviceModelNames:
        self.assertEqual(
            'Altered TLSimu (' + expected_value + ')',
            self.ia.remote_device.node_map.DeviceModelName.value
        )

        #
        self.ia.destroy()


class TestHarvesterCore(TestHarvester):
    sleep_duration = .5  # Time to keep sleeping [s]

    def test_ticket_300(self):
        if not self.is_running_with_default_target():
            return

        info_list = self.harvester.device_info_list
        self.assertTrue(len(info_list) > 0)

        dev_info = info_list[0]
        self.assertEqual(Interface, type(dev_info.parent))

        iface = dev_info.parent
        self.assertIsNotNone(iface.node_map)
        self.assertEqual(NodeMap, type(iface.node_map))
        self.assertEqual("XX::InterfaceA", iface.node_map.InterfaceID.value)

        system = iface.parent
        self.assertIsNotNone(system.node_map)
        self.assertEqual(NodeMap, type(system.node_map))
        self.assertEqual("TLSimu.cti", system.node_map.TLID.value)

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
        ia.start()

        # Fetch a buffer that is filled with image data.
        with ia.fetch() as buffer:
            # Reshape it.
            self._logger.info('{0}'.format(buffer))

        # Stop image acquisition.
        ia.stop()

    def test_multiple_image_acquirers(self):
        if not self.is_running_with_default_target():
            return

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
                ia.start()
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
                            # a client called fetch method even though
                            # he'd forgotten to start image acquisition.
                            with ia.fetch() as buffer:
                                self._logger.info('{0}'.format(buffer))
                        except AttributeError:
                            # Harvester Core has not started image acquisition
                            # so calling fetch() raises AttributeError
                            # because None object is used for the with
                            # statement.
                            pass
                    else:
                        # Option 2: You can manually do the same job but not
                        # recommended because you might forget to queue the
                        # buffer.
                        buffer = ia.fetch()
                        self._logger.info('{0}'.format(buffer))

                #
                k += 1

            #
            self._logger.info('<--- Round {0}: Tear down'.format(i))
            for index, ia in enumerate(ias):
                ia.stop()
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
        #ia.start()

        timeout = 3  # sec

        self._logger.info("you will see timeout but that's intentional.")
        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will immediately raise
            # TimeoutException because it's not started image acquisition:
            _ = ia.fetch(timeout=timeout)

        # Then we setup the device for software trigger mode:
        ia.remote_device.node_map.TriggerMode.value = 'On'
        ia.remote_device.node_map.TriggerSource.value = 'Software'

        # We're ready to start image acquisition:
        ia.start()

        self._logger.info("you will see timeout but that's intentional.")
        with self.assertRaises(TimeoutException):
            # Try to fetch a buffer but the IA will raise TimeoutException
            # because we've not triggered the device so far:
            _ = ia.fetch(timeout=timeout)

        # We finally acquire an image triggering the device:
        buffer = None
        self.assertIsNone(buffer)

        ia.remote_device.node_map.TriggerSoftware.execute()
        buffer = ia.fetch(timeout=timeout)
        self.assertIsNotNone(buffer)
        self._logger.info('{0}'.format(buffer))
        buffer.queue()

        # Now we stop image acquisition:
        ia.stop()
        ia.destroy()

    def test_releasing_resource_on_update_call(self):
        #
        acquires = []
        nr_devices = len(self.harvester.device_info_list)
        for i in range(nr_devices):
            acquires.append(self.harvester.create_image_acquirer(i))
        #
        for acquire in acquires:
            acquire.start()
        #
        self._logger.info("finished allocating resource.")
        self.harvester.update()
        self._logger.info("finished the update method call.")
        #
        for acquire in acquires:
            self.assertFalse(acquire.is_valid())

    def test_deprecation_announced_items_fetch_buffer(self):
        ia = self.harvester.create_image_acquirer(0)
        ia.start()
        # Try to fetch a buffer but None will be returned
        # because we've not triggered the device so far:
        self._logger.info("you will see deprecation announcement.")
        with ia.fetch_buffer(timeout=0.1) as buffer:
            pass
        self._logger.info("did you see deprecation announcement?")
        ia.stop()

    def test_deprecation_announced_items_start_stop_image_acquisition(self):
        ia = self.harvester.create_image_acquirer(0)
        self._logger.info("you will see deprecation announcement.")
        ia.start_acquisition()
        self._logger.info("did you see deprecation announcement?")
        self._logger.info("you will see deprecation announcement.")
        ia.stop_acquisition()
        self._logger.info("did you see deprecation announcement?")

    def test_try_fetch_with_timeout(self):
        if not self.is_running_with_default_target():
            return

        # Create an image acquirer:
        ia = self.harvester.create_image_acquirer(0)

        # We do not start image acquisition:
        #ia.start()

        timeout = 3  # sec

        # Setup the device for software trigger mode:
        ia.remote_device.node_map.TriggerMode.value = 'On'
        ia.remote_device.node_map.TriggerSource.value = 'Software'

        # We're ready to start image acquisition:
        ia.start()

        # Try to fetch a buffer but None will be returned
        # because we've not triggered the device so far:
        self._logger.info("you will see timeout but that's intentional.")
        buffer = ia.try_fetch(timeout=timeout)
        self.assertIsNone(buffer)

        ia.remote_device.node_map.TriggerSoftware.execute()
        buffer = ia.try_fetch(timeout=timeout)
        self.assertIsNotNone(buffer)
        self._logger.info('{0}'.format(buffer))
        buffer.queue()

        # Now we stop image acquisition:
        ia.stop()
        ia.destroy()

    def test_stop_start_and_stop(self):
        # Create an image acquirer:
        ia = self.harvester.create_image_acquirer(0)

        # It's not necessary but we stop image acquisition first;
        #
        ia.stop()

        # Then start it:
        ia.start()

        # Fetch a buffer to make sure it's working:
        with ia.fetch() as buffer:
            self._logger.info('{0}'.format(buffer))

        # Then stop image acquisition:
        ia.stop()

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
            for num_images in [1, 2]:
                #
                self.ia.num_filled_buffers_to_hold = num_images

                # Start image acquisition:
                self._logger.info(
                    "you will see timeout but that's intentional.")
                self.ia.start(run_as_thread=True)

                # Run a test:
                test(num_images)

                # Stop image acquisition:
                self.ia.stop()

    def _test_issue_120_1(self, num_images):
        # Make sure num_holding_filled_buffers is incremented every trigger:
        for i in range(num_images):
            #
            self.assertEqual(
                self.ia.num_holding_filled_buffers, i
            )

            # Trigger it:
            self.generate_software_trigger(sleep_s=self.sleep_duration)
            self._logger.info("triggered.")

            # It must be incremented:
            self.assertEqual(
                self.ia.num_holding_filled_buffers, i + 1
            )

        # Trigger it again, we know it's redundant compared to the
        # maximum capacity:
        self.generate_software_trigger(sleep_s=self.sleep_duration)
        self._logger.info("triggered.")

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
            with self.ia.fetch():
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
        self.assertEqual(5, self.ia.num_buffers)

    def _callback_on_new_buffer_arrival(self):
        # Fetch a buffer and keep it:
        self._buffers.append(self.ia.fetch())

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
        retrieved_file_path = Module._retrieve_file_path(url=url)

        # Compare file names:
        self.assertEqual(
            os.path.basename(retrieved_file_path),
            expected_file_name
        )

    def test_issue_121(self):
        if is_running_on_windows():
            return

        #
        expected_file_path = '/Foo.xml'

        #
        url = 'file://' + expected_file_path
        retrieved_file_path = Module._retrieve_file_path(url=url)

        # Compare file names:
        self.assertEqual(
            retrieved_file_path,
            expected_file_path
        )

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
        self.ia.start(run_as_thread=False)
        #
        with self.ia.fetch() as buffer:
            self.assertIsNotNone(buffer)
        #
        self.ia.stop()

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
            self._logger.info("you will see timeout but that's intentional.")
            test()

            # Then stop image acquisition:
            self.ia.stop()

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
        self._logger.info("going to start acquisition in the background.")
        self.ia.start(run_as_thread=True)

        # Trigger the target device:
        for _ in range(self.num_images):
            self.generate_software_trigger(sleep_s=self.sleep_duration)
            self._logger.info("triggered.")

    def test_issue_150(self):
        if not self.is_running_with_default_target():
            return

        # Create an image acquirer:
        self.ia = self.harvester.create_image_acquirer(0)

        # TLSimu does not support SingleFrame in reality:
        # modes = ["SingleFrame", "Continuous"]

        # Test only "Continuous":
        modes = ["Continuous"]
        for mode in modes:
            self.ia.remote_device.node_map.AcquisitionMode.value = mode

            for i in range(32):
                # Then start it:
                self.ia.start()

                # Fetch a buffer to make sure it's working:
                with self.ia.fetch() as buffer:
                    self._logger.info('{0}'.format(buffer))

            # Then stop image acquisition:
            self.ia.stop()

        # And destroy the ImageAcquirer:
        self.ia.destroy()

    def test_issue_146(self):
        #
        tests = [
            self._test_issue_146_group_packed_10,
            self._test_issue_146_group_packed_12,
            self._test_issue_146_packed_10,
            self._test_issue_146_packed_12,
            self._test_issue_222,
            self._test_issue_146_mono_unpacked_multibytes,
            self._test_issue_146_bayer_rg_12p,
        ]
        #
        for test in tests:
            test()

    def _test_issue_146_bayer_rg_12p(self):
        inputs = [
            bytes([0b11111111, 0b00001111, 0b00000000]),
            bytes([0b00000000, 0b11110000, 0b11111111])
        ]
        outputs = [
            [0xfff, 0],
            [0, 0xfff]
        ]
        self._test_conversion('BayerRG12p', inputs, outputs)

    def _test_issue_146_group_packed_10(self):
        _1st = 0xff
        _3rd = 0xff
        ba = bytes([_1st, 0x33, _3rd])
        packed = np.frombuffer(ba, dtype=np.uint8)
        pf = Dictionary.get_proxy('BayerRG10Packed')
        unpacked = pf.expand(packed)
        self.assertEqual(_1st * 4 + 3, unpacked[0])
        self.assertEqual(_3rd * 4 + 3, unpacked[1])

    def _test_conversion(self, format_name: str, inputs, outputs):
        pf = Dictionary.get_proxy(format_name)
        for input, output in zip(inputs, outputs):
            packed = np.frombuffer(input, dtype=np.uint8)
            unpacked_elements = pf.expand(packed)
            self.assertEqual(len(outputs), unpacked_elements.size)
            for i, element in enumerate(unpacked_elements):
                self.assertEqual(output[i], element)

    def _test_issue_146_group_packed_12(self):
        inputs = [
            bytes([0b11111111, 0b00001111, 0b00000000]),
            bytes([0b00000000, 0b11110000, 0b11111111])
        ]
        outputs = [
            [0xfff, 0],
            [0, 0xfff]
        ]
        self._test_conversion('BayerRG12Packed', inputs, outputs)

    def _test_issue_146_packed_10(self):
        inputs = [
            bytes([0b11111111, 0b00000011, 0b00000000, 0b00000000, 0b00000000]),
            bytes([0b00000000, 0b11111100, 0b00001111, 0b00000000, 0b00000000]),
            bytes([0b00000000, 0b00000000, 0b11110000, 0b00111111, 0b00000000]),
            bytes([0b00000000, 0b00000000, 0b00000000, 0b11000000, 0b11111111])
        ]
        outputs = [
            [0x3ff, 0, 0, 0],
            [0, 0x3ff, 0, 0],
            [0, 0, 0x3ff, 0],
            [0, 0, 0, 0x3ff]
        ]
        self._test_conversion('Mono10p', inputs, outputs)

    def _test_issue_146_packed_12(self):
        inputs = [
            bytes([0b11111111, 0b00001111, 0b00000000]),
            bytes([0b00000000, 0b11110000, 0b11111111])
        ]
        outputs = [
            [0xfff, 0],
            [0, 0xfff]
        ]
        self._test_conversion('Mono12p', inputs, outputs)

    def _test_issue_222(self):
        inputs = [
            bytes([0b11111111, 0b00000011, 0b00000000, 0b00000000]),
            bytes([0b00000000, 0b11111100, 0b00001111, 0b00000000]),
            bytes([0b00000000, 0b00000000, 0b11110000, 0b00111111])
        ]
        outputs = [
            [0x3ff, 0, 0],
            [0, 0x3ff, 0],
            [0, 0, 0x3ff]
        ]
        self._test_conversion('Mono10c3p32', inputs, outputs)

    def _test_issue_146_mono_unpacked_multibytes(self):
        names = ['Mono10', 'Mono12']
        maximums = [0x4, 0x10]
        for index, name in enumerate(names):
            pf = Dictionary.get_proxy(name)
            for i in range(maximums[index]):
                for j in range(0x100):
                    ba = bytes([j, i, j, i])
                    packed = np.frombuffer(ba, dtype=np.uint8)
                    unpacked = pf.expand(packed)
                    # We know it's redundant but check 10 times:
                    for l in range(10):
                        for k in range(2):
                            self.assertEqual((i << 8) + j, unpacked[k])

    def test_issue_215(self):
        if not self.is_running_with_default_target():
            return

        ia = self.harvester.create_image_acquirer(0)

        ports = [
            ia.system.port,
            ia.interface.port,
            ia.device.port,
            ia.remote_device.port
        ]
        file_names = [
            'SITL.xml',
            'SITLI.xml',
            'SIDEVTL.xml',
            'SIDEV.xml'
        ]

        for (port, file_name) in zip(ports, file_names):
            self.assertEqual(port.url_info_list[0].file_name, file_name)

    def test_port_access(self):
        if not self.is_running_with_default_target():
            return

        # instantiate an acquirer:
        ia = self.harvester.create_image_acquirer(0)

        #
        address = 0x104
        access_size = 4

        # read a piece of data through the remote device port:
        data_size, data_returned = ia.remote_device.port.read(
            address, access_size)
        self.assertEqual(data_size, access_size)
        self.assertEqual(data_returned, b'\x00\x02\x00\x00')

        # overwrite the data through the remote device port:
        data_to_write = b'\x00\x01\x00\x00'
        ia.remote_device.port.write(address, data_to_write)

        # then read it back to make sure that it worked:
        data_size, data_returned = ia.remote_device.port.read(
            address, access_size)
        self.assertEqual(data_size, access_size)
        self.assertEqual(data_returned, data_to_write)

    def test_issue_207_that_does_not_match(self):
        if not self.is_running_with_default_target():
            return

        ia = self.harvester.create_image_acquirer(
            0, file_dict={r'\.$': b'\23\34\45'}
        )
        self.assertIsNotNone(ia)

    def test_issue_207_that_does_match(self):
        if not self.is_running_with_default_target():
            return

        with self.assertRaises(GenApi_GenericException):
            _ = self.harvester.create_image_acquirer(
                0, file_dict={r'\.xml$': bytes('<', encoding='utf-8')})

    def test_fix_for_bfd47ca_1(self):
        # Create an image acquirer:
        self.ia = self.harvester.create_image_acquirer(0)

        self.ia.timeout_on_internal_fetch_call = 1
        internal = self.ia.timeout_on_internal_fetch_call

        self._logger.info("larger")
        value = internal + 1
        value /= 1000
        self.ia.timeout_on_client_fetch_call = value

        self._logger.info("equal")
        value = 0.001
        self.ia.timeout_on_client_fetch_call = value

        self._logger.info("smaller")
        value = internal * 1000
        value -= 1
        value /= 1000
        value /= 1000
        self.ia.timeout_on_client_fetch_call = value

    def test_fix_for_bfd47ca_2(self):
        # Create an image acquirer:
        self.ia = self.harvester.create_image_acquirer(0)

        self.ia.timeout_on_client_fetch_call = 2.
        self._logger.info("larger")
        self.ia.timeout_on_internal_fetch_call = 2001
        self._logger.info("equal")
        self.ia.timeout_on_internal_fetch_call = 2000
        self._logger.info("smaller")
        self.ia.timeout_on_internal_fetch_call = 1000

    def test_manual_chunk_update(self):
        # Create an image acquirer:
        self.ia = self.harvester.create_image_acquirer(
            0, auto_chunk_data_update=False)

        # Then start it:
        self.ia.start()

        for i in range(32):
            # Fetch a buffer to make sure it's working:
            with self.ia.fetch() as buffer:
                self._logger.info('going to update chunk data'.format(buffer))
                buffer.update_chunk_data()
                self._logger.info('did it update?')

        # Then stop image acquisition:
        self.ia.stop()

        # And destroy the ImageAcquirer:
        self.ia.destroy()


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
            ia.start()
            ia.stop()
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

        config = ParameterSet({
            ParameterKey.ENABLE_CLEANING_UP_INTERMEDIATE_FILES: False,
        })
        #
        with Harvester(config=config) as h:
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
        buffer = self._ia.fetch()
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


class TestIssue181(unittest.TestCase):
    def test_issue_181_with_nonexistent_file(self):
        h = Harvester()
        with self.assertRaises(FileNotFoundError):
            h.add_file('just a string', check_existence=True)

    def test_issue_181_with_invalid_file(self):
        h = Harvester()
        with self.assertRaises(OSError):
            h.add_file(__file__, check_validity=True)


class TestIssue188(unittest.TestCase):
    _height = 1
    _range = range(0, 3, 1)

    def test_issue_188_unpacked(self):
        proxies = [Mono8, Mono10, Mono12, Mono14, Mono16]
        expected_bytes = [
            [1, 2, 2, 2, 2],  # 1 x 1
            [2, 4, 4, 4, 4],  # 2 x 1
            [3, 6, 6, 6, 6],  # 3 x 1
        ]
        for i in self._range:
            for j, proxy in enumerate(proxies):
                self.assertEqual(
                    expected_bytes[i][j],
                    Component2DImage._get_nr_bytes(
                        pf_proxy=proxy(), width=i + 1, height=self._height
                    )
                )

    def test_issue_188_packed(self):
        proxies = [Mono10Packed, Mono12Packed]
        expected_bytes = [
            [2, 2],  # 1 x 1
            [3, 3],  # 2 x 1
            [4, 5],  # 3 x 1
        ]
        for i in self._range:
            for j, proxy in enumerate(proxies):
                self.assertEqual(
                    expected_bytes[i][j],
                    Component2DImage._get_nr_bytes(
                        pf_proxy=proxy(), width=i + 1, height=self._height
                    )
                )

    def test_issue_188_p(self):
        proxies = [Mono10p, Mono12p, Mono14p]
        expected_bytes = [
            [2, 2, 2],  # 1 x 1
            [3, 3, 4],  # 2 x 1
            [4, 5, 6],  # 3 x 1
        ]
        for i in self._range:
            for j, proxy in enumerate(proxies):
                self.assertEqual(
                    expected_bytes[i][j],
                    Component2DImage._get_nr_bytes(
                        pf_proxy=proxy(), width=i + 1, height=self._height
                    )
                )

    def test_issue_188_neels_case(self):
        proxies = [Mono12]
        width = 2456
        height = 2058
        for proxy in proxies:
            self.assertEqual(
                10108896,  # = 2456 * 2058 * 2
                Component2DImage._get_nr_bytes(
                    pf_proxy=proxy(), width=width, height=height
                )
            )

    def test_issue_238(self):
        proxies = [RGB10p, BGR10p, RGB12p, BGR12p]
        expected_bytes = [
            [4, 4, 5, 5],  # 1 x 1
            [8, 8, 9, 9],  # 2 x 1
            [12, 12, 14, 14],  # 3 x 1
        ]
        for i in self._range:
            for j, proxy in enumerate(proxies):
                self.assertEqual(
                    expected_bytes[i][j],
                    Component2DImage._get_nr_bytes(
                        pf_proxy=proxy(), width=i + 1, height=self._height
                    )
                )


class TestUtility(unittest.TestCase):
    def test_issue_207_and_226(self):
        body = b'\xc2\xb0'  # °
        padding = b'\x00\x00'
        data = body + padding
        data = _drop_padding_data(data)
        self.assertEqual(data, body)
        self.assertEqual('°', str(data, encoding='utf-8'))

    def test_issue_207(self):
        data = b'\xc2\xb0'  # '°'
        padding = b'\x2D\x65\x6E'  # '-en'
        target_file_name = 'GenTL_Stream.xml'
        file_name_pattern = r'GenTL_Stream\.xml'
        result = _drop_padding_data(
            data + padding, file_name=target_file_name,
            file_dict={file_name_pattern: bytes('-en', encoding='utf-8')}
        )
        self.assertEqual(data, result)

    def test_issue_277(self):
        if not is_running_on_windows():
            return

        prefix = 'file:///'
        path = 'C:/ProgramData/GenICam/xml/cache/Optronis_Cyclone_V1_7_8.xml'
        url = prefix + path
        result = ImageAcquirer._retrieve_file_path(url=url)
        self.assertEqual(path, result)


if __name__ == '__main__':
    unittest.main()
