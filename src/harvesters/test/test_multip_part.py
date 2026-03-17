#!/usr/bin/env python3

##
# \file        test_multi_part.py
# \author      Silvan Murer
# \copyright   EMVA, 2026
# \license     Apache License, Version 2.0 (see LICENSE.txt)
# \version     1.0.0
#
# \brief       Test for acquiring multi-part images.

import unittest
from harvesters.test.base_harvester import TestHarvester

import genicam.gentl


class TestMultiPart(TestHarvester):
    def test_multipart(self):
        self._test_logger.info("start 'test_multipart'.")
        self.ia = self.harvester.create(0)

        # enable multi-part (Intensity component is always enabled, just enable Range component):
        self.ia.remote_device.node_map.ComponentSelector.value = "Range"
        self.ia.remote_device.node_map.ComponentEnable.value = True

        self.ia.start()

        buffer = self.ia.fetch(timeout=10.0)
        self.assertEqual(
            buffer.payload.payload_type,
            genicam.gentl.PAYLOADTYPE_INFO_IDS.PAYLOAD_TYPE_MULTI_PART,
        )
        # 1 Intensity Component (RGBa8) + 3 Range Components (Coord3D_A32f, Coord3D_B32f,Coord3D_C32f)
        self.assertEqual(len(buffer.payload.components), 4)

        self.assertEqual(buffer.payload.components[0].data_format, "RGBa8")
        height_rgba = buffer.payload.components[0].height
        width_rgba = buffer.payload.components[0].width
        # Intensity component is RGBa8
        image_rgba = buffer.payload.components[0].data.reshape(
            height_rgba, width_rgba, 4
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

        self.assertEqual(buffer.payload.components[1].data_format, "Coord3D_A32f")
        height_a32f = buffer.payload.components[1].height
        height_a32f = buffer.payload.components[1].width
        image_a32f = buffer.payload.components[1].data.reshape(height_a32f, height_a32f)
        self.assertEqual(
            image_a32f[:, :].min(), 0, "Wrong minimum value of component 1"
        )
        self.assertEqual(
            image_a32f[:, :].max(), 399.0, "Wrong maximum value of component 1"
        )

        self.assertEqual(buffer.payload.components[2].data_format, "Coord3D_B32f")
        height_b32f = buffer.payload.components[2].height
        height_b32f = buffer.payload.components[2].width
        image_b32f = buffer.payload.components[2].data.reshape(height_b32f, height_b32f)
        self.assertEqual(
            image_b32f[:, :].min(), 0, "Wrong minimum value of component 2"
        )
        self.assertEqual(
            image_b32f[:, :].max(), 399.0, "Wrong maximum value of component 2"
        )

        self.assertEqual(buffer.payload.components[3].data_format, "Coord3D_C32f")
        height_c32f = buffer.payload.components[3].height
        height_c32f = buffer.payload.components[3].width
        image_c32f = buffer.payload.components[3].data.reshape(height_c32f, height_c32f)
        self.assertEqual(
            image_c32f[:, :].min(), 0, "Wrong minimum value of component 3"
        )
        self.assertAlmostEqual(
            image_c32f[:, :].max(), 41.04875, msg="Wrong maximum value of component 3"
        )

        buffer.queue()

        self.ia.stop()
        self.ia.destroy()


if __name__ == "__main__":
    unittest.main()
