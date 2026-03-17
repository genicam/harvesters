#!/usr/bin/env python3

##
# \file        test_gendc.py
# \author      Silvan Murer
# \copyright   EMVA, 2026
# \license     Apache License, Version 2.0 (see LICENSE.txt)
# \version     1.0.0
#
# \brief       Test for acquiring GenDC images.

import unittest
from harvesters.test.base_harvester import TestHarvester

import genicam.gentl


class TestMultiPart(TestHarvester):
    ##
    # single GenDC component without chunk data.
    # => 1 Component containing 1 Part
    def test_gendc_1_parts(self):
        self._test_logger.info("start 'test_gendc_1_parts'.")
        self.ia = self.harvester.create(0)

        # disable chunk data
        self.ia.remote_device.node_map.ChunkModeActive.value = False
        # enable GenDC
        self.ia.remote_device.node_map.GenDCStreamingMode.value = "On"

        self.ia.start()

        buffer = self.ia.fetch(timeout=10.0)
        self.assertEqual(
            buffer.payload.payload_type,
            genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_GENDC,
        )
        # 1 Intensity Component (RGBa8)
        self.assertEqual(len(buffer.payload.components), 1)
        self.assertEqual(len(buffer.payload.components[0].parts), 1)
        self.assertEqual(buffer.payload.components[0].data_format, "RGBa8")

        height_rgba = buffer.payload.components[0].parts[0].height
        width_rgba = buffer.payload.components[0].parts[0].width
        # Intensity component is RGBa8
        image_rgba = (
            buffer.payload.components[0]
            .parts[0]
            .data.reshape(height_rgba, width_rgba, 4)
        )
        self.assertEqual(
            image_rgba[:, :, 0].min(), 255, "Wrong minimum value of component 0.0"
        )
        self.assertEqual(
            image_rgba[:, :, 0].max(), 255, "Wrong maximum value of component 0.0"
        )
        self.assertEqual(
            image_rgba[:, :, 1].min(), 0, "Wrong minimum value of component 0.1"
        )
        self.assertEqual(
            image_rgba[:, :, 1].max(), 255, "Wrong maximum value of component 0.1"
        )
        self.assertEqual(
            image_rgba[:, :, 2].min(), 0, "Wrong minimum value of component 0.2"
        )
        self.assertEqual(
            image_rgba[:, :, 2].max(), 255, "Wrong maximum value of component 0.2"
        )
        self.assertEqual(
            image_rgba[:, :, 3].min(), 0, "Wrong minimum value of component 0.3"
        )
        self.assertEqual(
            image_rgba[:, :, 3].max(), 255, "Wrong maximum value of component 0.3"
        )

        buffer.queue()

        self.ia.stop()
        self.ia.destroy()

    ##
    # single GenDC component with chunk data.
    # => 2 Components: 1 part, 1 part
    def test_gendc_2_parts(self):
        self._test_logger.info("start 'test_gendc_2_parts'.")
        self.ia = self.harvester.create(0)

        # enable chunk data
        self.ia.remote_device.node_map.ChunkModeActive.value = True
        self.ia.remote_device.node_map.ChunkSelector.value = "NrBounces"
        self.ia.remote_device.node_map.ChunkEnable.value = True
        # enable GenDC
        self.ia.remote_device.node_map.GenDCStreamingMode.value = "On"

        self.ia.start()

        buffer = self.ia.fetch(timeout=10.0)
        self.assertEqual(
            buffer.payload.payload_type,
            genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_GENDC,
        )
        # Intensity (RGBa8), Chunk (Data8)
        self.assertEqual(len(buffer.payload.components), 2)

        self.assertEqual(buffer.payload.components[0].data_format, "RGBa8")
        self.assertEqual(buffer.payload.components[1].data_format, "Data8")

        # Intensity (RGBa8)
        self.assertEqual(len(buffer.payload.components[0].parts), 1)
        self.assertEqual(buffer.payload.components[0].parts[0].data_format, "RGBa8")

        height_rgba = buffer.payload.components[0].parts[0].height
        width_rgba = buffer.payload.components[0].parts[0].width
        image_rgba = (
            buffer.payload.components[0]
            .parts[0]
            .data.reshape(height_rgba, width_rgba, 4)
        )
        self.assertEqual(
            image_rgba[:, :, 0].min(), 255, "Wrong minimum value of component 0.0"
        )
        self.assertEqual(
            image_rgba[:, :, 0].max(), 255, "Wrong maximum value of component 0.0"
        )
        self.assertEqual(
            image_rgba[:, :, 1].min(), 0, "Wrong minimum value of component 0.1"
        )
        self.assertEqual(
            image_rgba[:, :, 1].max(), 255, "Wrong maximum value of component 0.1"
        )
        self.assertEqual(
            image_rgba[:, :, 2].min(), 0, "Wrong minimum value of component 0.2"
        )
        self.assertEqual(
            image_rgba[:, :, 2].max(), 255, "Wrong maximum value of component 0.2"
        )
        self.assertEqual(
            image_rgba[:, :, 3].min(), 0, "Wrong minimum value of component 0.3"
        )
        self.assertEqual(
            image_rgba[:, :, 3].max(), 255, "Wrong maximum value of component 0.3"
        )

        # Chunk (Data8)
        self.assertEqual(len(buffer.payload.components[1].parts), 1)
        # Data8 type and access is not yet implemented in 'genicam'

        # Check Chunk data mapping to the node_map
        self.assertTrue(self.ia.remote_device.node_map.ChunkNrBounces.value >= 0)

        buffer.queue()

        self.ia.stop()
        self.ia.destroy()

    ##
    # three GenDC components: Intensity, Range, Chunk (Data)
    # => 3 Components: 1 part, 3 parts, 1 part
    def test_gendc_5_parts(self):
        self._test_logger.info("start 'test_gendc_5_parts'.")
        self.ia = self.harvester.create(0)

        # enable chunk data
        self.ia.remote_device.node_map.ChunkModeActive.value = True

        # enable multiple components (Intensity component is always enabled, just enable Range component):
        self.ia.remote_device.node_map.ComponentSelector.value = "Range"
        self.ia.remote_device.node_map.ComponentEnable.value = True

        # enable GenDC
        self.ia.remote_device.node_map.GenDCStreamingMode.value = "On"

        self.ia.start()

        buffer = self.ia.fetch(timeout=10.0)
        self.assertEqual(
            buffer.payload.payload_type,
            genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_GENDC,
        )
        # Intensity (RGBa8), Range (Coord3D_ABC32f_Planar), Chunk (Data8)
        self.assertEqual(len(buffer.payload.components), 3)

        self.assertEqual(buffer.payload.components[0].data_format, "RGBa8")
        self.assertEqual(
            buffer.payload.components[1].data_format, "Coord3D_ABC32f_Planar"
        )
        self.assertEqual(buffer.payload.components[2].data_format, "Data8")

        # Intensity (RGBa8)
        self.assertEqual(len(buffer.payload.components[0].parts), 1)
        self.assertEqual(buffer.payload.components[0].parts[0].data_format, "RGBa8")

        height_rgba = buffer.payload.components[0].parts[0].height
        width_rgba = buffer.payload.components[0].parts[0].width
        image_rgba = (
            buffer.payload.components[0]
            .parts[0]
            .data.reshape(height_rgba, width_rgba, 4)
        )
        self.assertEqual(
            image_rgba[:, :, 0].min(), 255, "Wrong minimum value of component 0.0"
        )
        self.assertEqual(
            image_rgba[:, :, 0].max(), 255, "Wrong maximum value of component 0.0"
        )
        self.assertEqual(
            image_rgba[:, :, 1].min(), 0, "Wrong minimum value of component 0.1"
        )
        self.assertEqual(
            image_rgba[:, :, 1].max(), 255, "Wrong maximum value of component 0.1"
        )
        self.assertEqual(
            image_rgba[:, :, 2].min(), 0, "Wrong minimum value of component 0.2"
        )
        self.assertEqual(
            image_rgba[:, :, 2].max(), 255, "Wrong maximum value of component 0.2"
        )
        self.assertEqual(
            image_rgba[:, :, 3].min(), 0, "Wrong minimum value of component 0.3"
        )
        self.assertEqual(
            image_rgba[:, :, 3].max(), 255, "Wrong maximum value of component 0.3"
        )

        # Range (Coord3D_A32f, Coord3D_B32f,Coord3D_C32f)
        self.assertEqual(len(buffer.payload.components[1].parts), 3)
        self.assertEqual(
            buffer.payload.components[1].parts[0].data_format, "Coord3D_A32f"
        )
        self.assertEqual(
            buffer.payload.components[1].parts[1].data_format, "Coord3D_B32f"
        )
        self.assertEqual(
            buffer.payload.components[1].parts[2].data_format, "Coord3D_C32f"
        )

        height_a32f = buffer.payload.components[1].parts[0].height
        height_a32f = buffer.payload.components[1].parts[0].width
        image_a32f = (
            buffer.payload.components[1].parts[0].data.reshape(height_a32f, height_a32f)
        )
        self.assertEqual(
            image_a32f[:, :].min(), 0, "Wrong minimum value of component 1"
        )
        self.assertEqual(
            image_a32f[:, :].max(), 399.0, "Wrong maximum value of component 1"
        )

        self.assertEqual(
            buffer.payload.components[1].parts[1].data_format, "Coord3D_B32f"
        )
        height_b32f = buffer.payload.components[1].parts[1].height
        height_b32f = buffer.payload.components[1].parts[1].width
        image_b32f = (
            buffer.payload.components[1].parts[1].data.reshape(height_b32f, height_b32f)
        )
        self.assertEqual(
            image_b32f[:, :].min(), 0, "Wrong minimum value of component 2"
        )
        self.assertEqual(
            image_b32f[:, :].max(), 399.0, "Wrong maximum value of component 2"
        )

        self.assertEqual(
            buffer.payload.components[1].parts[2].data_format, "Coord3D_C32f"
        )
        height_c32f = buffer.payload.components[1].parts[2].height
        height_c32f = buffer.payload.components[1].parts[2].width
        image_c32f = (
            buffer.payload.components[1].parts[2].data.reshape(height_c32f, height_c32f)
        )
        self.assertEqual(
            image_c32f[:, :].min(), 0, "Wrong minimum value of component 3"
        )
        self.assertAlmostEqual(
            image_c32f[:, :].max(), 41.04875, msg="Wrong maximum value of component 3"
        )

        # Cunck (Data8)
        self.assertEqual(len(buffer.payload.components[2].parts), 1)
        # Data8 type and access is not yet implemented in 'genicam'

        # Check Chunk data mapping to the node_map
        self.assertTrue(self.ia.remote_device.node_map.ChunkNrBounces.value >= 0)

        buffer.queue()

        self.ia.stop()
        self.ia.destroy()


if __name__ == "__main__":
    unittest.main()
