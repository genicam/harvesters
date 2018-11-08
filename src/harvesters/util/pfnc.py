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

# Related third party imports

# Local application/library specific imports
from harvesters.util._pfnc import symbolics as _symbolics

#
symbolics = _symbolics


# 32-bit value layout
# |31            24|23            16|15            08|07            00|
# | C| Comp. Layout| Effective Size |            Pixel ID             |

# Custom flag
pfnc_custom = 0x80000000

# Component layout
pfnc_single_component = 0x01000000
pfnc_multiple_component = 0x02000000
pfnc_component_mask = 0x02000000

# Effective size
pfnc_pixel_size_mask = 0x00ff0000
pfnc_pixel_size_shift = 16


def get_effective_pixel_size(pixel_format_value):
    """
    Returns the effective pixel size (number of bits a pixel occupies in memory).
    This includes padding in many cases and the actually used bits are less.
    """
    return (pixel_format_value & pfnc_pixel_size_mask) >> \
           pfnc_pixel_size_shift


def is_custom(pixel_format_value):
    return (pixel_format_value & pfnc_custom) == pfnc_custom


def is_single_component(pixel_format_value):
    return (pixel_format_value & pfnc_component_mask) == pfnc_single_component


def is_multiple_component(pixel_format_value):
    return (pixel_format_value & pfnc_component_mask) == pfnc_multiple_component


def get_bits_per_pixel(data_format):
    """
    Returns the number of (used) bits per pixel.
    So without padding.
    Returns None if format is not known.
    """
    if data_format in component_8bit_formats:
        return 8
    elif data_format in component_10bit_formats:
        return 10
    elif data_format in component_12bit_formats:
        return 12
    elif data_format in component_14bit_formats:
        return 14
    elif data_format in component_16bit_formats:
        return 16
    # format not known
    return None


mono_location_formats = [
    #
    'Mono8',
    'Mono8s',
    'Mono10',
    'Mono12',
    'Mono14',
    'Mono16',
    #
    'R8',
    'R10',
    'R12',
    'R16',
    'G8',
    'G10',
    'G12',
    'G16',
    'B8',
    'B10',
    'B12',
    'B16',
    #
    'Coord3D_A8',
    'Coord3D_B8',
    'Coord3D_C8',
    'Coord3D_A16',
    'Coord3D_B16',
    'Coord3D_C16',
    'Coord3D_A32f',
    'Coord3D_B32f',
    'Coord3D_C32f',
    #
    'Confidence1',
    'Confidence8',
    'Confidence16',
    'Confidence32f',
]

mono_packed_location_formats = [
    'Mono1p',
    'Mono2p',
    'Mono4p',
    'Mono10Packed',
    'Mono10p',
    'Mono12Packed',
    'Mono12p',
    'Coord3D_A10p',
    'Coord3D_B10p',
    'Coord3D_C10p',
    'Coord3D_A12p',
    'Coord3D_B12p',
    'Coord3D_C12p',
]

lmn_444_location_formats = [
    #
    'RGB8',
    'RGB10',
    'RGB12',
    'RGB14',
    'RGB16',
    #
    'BGR8',
    'BGR10',
    'BGR12',
    'BGR14',
    'BGR16',
    #
    'Coord3D_ABC8',
    'Coord3D_ABC8_Planar',
    'Coord3D_ABC16',
    'Coord3D_ABC16_Planar',
    'Coord3D_ABC32f',
    'Coord3D_ABC32f_Planar',
]

lmn_444_packed_location_formats = [
    #
    'RGB8Packed',
    #
    'Coord3D_ABC10p',
    'Coord3D_ABC10p_Planar',
    'Coord3D_ABC12p',
    'Coord3D_ABC12p_Planar',
]

lmn_422_location_formats = [
    'YUV422_8_UYVY',
    'YUV422_8',
    'YCbCr422_8',
    'YCbCr601_422_8',
    'YCbCr709_422_8',
    'YCbCr422_8_CbYCrY',
    'YCbCr601_422_8_CbYCrY',
    'YCbCr709_422_8_CbYCrY',
    'YCbCr422_10',
    'YCbCr422_12',
    'YCbCr601_422_10',
    'YCbCr601_422_12',
    'YCbCr709_422_10',
    'YCbCr709_422_12',
    'YCbCr422_10_CbYCrY',
    'YCbCr422_12_CbYCrY',
    'YCbCr601_422_10_CbYCrY',
    'YCbCr601_422_12_CbYCrY',
    'YCbCr709_422_10_CbYCrY',
    'YCbCr709_422_12_CbYCrY',
    'YCbCr2020_422_8',
    'YCbCr2020_422_8_CbYCrY',
    'YCbCr2020_422_10',
    'YCbCr2020_422_10_CbYCrY',
    'YCbCr2020_422_12',
    'YCbCr2020_422_12_CbYCrY',
]

lmn_422_packed_location_formats = [
    'YCbCr422_10p',
    'YCbCr422_12p',
    'YCbCr601_422_10p',
    'YCbCr601_422_12p',
    'YCbCr709_422_10p',
    'YCbCr709_422_12p',
    'YCbCr422_10p_CbYCrY',
    'YCbCr422_12p_CbYCrY',
    'YCbCr601_422_10p_CbYCrY',
    'YCbCr601_422_12p_CbYCrY',
    'YCbCr709_422_10p_CbYCrY',
    'YCbCr709_422_12p_CbYCrY',
    'YCbCr2020_422_10p',
    'YCbCr2020_422_10p_CbYCrY',
    'YCbCr2020_422_12p',
    'YCbCr2020_422_12p_CbYCrY',
]

lmn_411_location_formats = [
    'YUV411_8_UYYVYY',
    'YCbCr411_8_CbYYCrYY',
    'YCbCr601_411_8_CbYYCrYY',
    'YCbCr709_411_8_CbYYCrYY',
    'YCbCr411_8',
    'YCbCr2020_411_8_CbYYCrYY',
]

lmno_4444_location_formats = [
    'RGBa8',
    'RGBa10',
    'RGBa12',
    'RGBa14',
    'RGBa16',
    'BGRa8',
    'BGRa10',
    'BGRa12',
    'BGRa14',
    'BGRa16',
]

lmno_4444_packed_location_formats = [
    'RGBa10p',
    'RGBa12p',
    'BGRa10p',
    'BGRa12p',
]

lm_44_location_formats = [
    'Coord3D_AC8',
    'Coord3D_AC8_Planar',
    'Coord3D_AC16',
    'Coord3D_AC16_Planar',
    'Coord3D_AC32f',
    'Coord3D_AC32f_Planar',
]

lm_44_packed_location_formats = [
    'Coord3D_AC10p',
    'Coord3D_AC10p_Planar',
    'Coord3D_AC12p',
    'Coord3D_AC12p_Planar',
]

bayer_location_formats = [
    'BayerGR8',
    'BayerRG8',
    'BayerGB8',
    'BayerBG8',
    'BayerGR10',
    'BayerRG10',
    'BayerGB10',
    'BayerBG10',
    'BayerGR12',
    'BayerRG12',
    'BayerGB12',
    'BayerBG12',
    'BayerGR16',
    'BayerRG16',
    'BayerGB16',
    'BayerBG16',
]

bayer_packed_location_formats = [
    'BayerGR10Packed',
    'BayerRG10Packed',
    'BayerGB10Packed',
    'BayerBG10Packed',
    'BayerGR12Packed',
    'BayerRG12Packed',
    'BayerGB12Packed',
    'BayerBG12Packed',
    'BayerBG10p',
    'BayerBG12p',
    'BayerGB10p',
    'BayerGB12p',
    'BayerGR10p',
    'BayerGR12p',
    'BayerRG10p',
    'BayerRG12p',
]

uint8_formats = [
    #
    'Mono8',
    #
    'RGB8',
    'RGB8Packed',
    'RGBa8',
    #
    'BGR8',
    'BGRa8',
    #
    'BayerGR8',
    'BayerGB8',
    'BayerRG8',
    'BayerBG8',
    #
    'Coord3D_A8',
    'Coord3D_B8',
    'Coord3D_C8',
    'Coord3D_ABC8',
    'Coord3D_ABC8_Planar',
    'Coord3D_AC8',
    'Coord3D_AC8_Planar',
    #
    'Confidence1',
    'Confidence8',
]

uint16_formats = [
    #
    'Mono10',
    'Mono12',
    'Mono14',
    'Mono16',
    #
    'RGB10',
    'RGB12',
    'RGB14',
    'RGB16',
    #
    'BGR10',
    'BGR12',
    'BGR14',
    'BGR16',
    #
    'RGBa10',
    'RGBa12',
    'RGBa14',
    'RGBa16',
    #
    'BGRa10',
    'BGRa12',
    'BGRa14',
    'BGRa16',
    #
    'BayerGR10',
    'BayerGB10',
    'BayerRG10',
    'BayerBG10',
    #
    'BayerGR12',
    'BayerGB12',
    'BayerRG12',
    'BayerBG12',
    #
    'BayerGR16',
    'BayerRG16',
    'BayerGB16',
    'BayerBG16',
    #
    'Coord3D_A16',
    'Coord3D_B16',
    'Coord3D_C16',
    #
    'Coord3D_ABC16',
    'Coord3D_ABC16_Planar',
    #
    'Coord3D_AC16',
    'Coord3D_AC16_Planar',
    #
    'Coord3D_A10p',
    'Coord3D_B10p',
    'Coord3D_C10p',
    #
    'Coord3D_A12p',
    'Coord3D_B12p',
    'Coord3D_C12p',
    #
    'Coord3D_ABC10p',
    'Coord3D_ABC10p_Planar',
    #
    'Coord3D_ABC12p',
    'Coord3D_ABC12p_Planar',
    #
    'Coord3D_AC10p',
    'Coord3D_AC10p_Planar',
    #
    'Coord3D_AC12p',
    'Coord3D_AC12p_Planar',
    #
    'Confidence16',
]

uint32_formats = [
    'Mono32',
]

float32_formats = [
    #
    'Coord3D_A32f',
    'Coord3D_B32f',
    'Coord3D_C32f',
    #
    'Coord3D_ABC32f',
    'Coord3D_ABC32f_Planar',
    #
    'Coord3D_AC32f',
    'Coord3D_AC32f_Planar',
    #
    'Confidence32f',
]

component_8bit_formats = [
    #
    'Mono8',
    #
    'RGB8',
    'RGBa8',
    #
    'BGR8',
    'BGRa8',
    #
    'BayerGR8',
    'BayerGB8',
    'BayerRG8',
    'BayerBG8',
    #
    'Confidence8',
]

component_10bit_formats = [
    #
    'Mono10',
    #
    'RGB10',
    'RGBa10',
    #
    'BGR10',
    'BGRa10',
    #
    'BayerGR10',
    'BayerGB10',
    'BayerRG10',
    'BayerBG10',
]

component_12bit_formats = [
    #
    'Mono12',
    #
    'RGB12',
    'RGBa12',
    #
    'BGR12',
    'BGRa12',
    #
    'BayerGR12',
    'BayerGB12',
    'BayerRG12',
    'BayerBG12',
]

component_14bit_formats = [
    #
    'Mono14',
    #
    'RGB14',
    'RGBa14',
    #
    'BGR14',
    'BGRa14',
]

component_16bit_formats = [
    #
    'Mono16',
    #
    'RGB16',
    'RGBa16',
    #
    'BayerGR16',
    'BayerRG16',
    'BayerGB16',
    'BayerBG16',
    #
    'Coord3D_A16',
    'Coord3D_B16',
    'Coord3D_C16',
    #
    'Coord3D_ABC16',
    'Coord3D_ABC16_Planar',
    #
    'Coord3D_AC16',
    'Coord3D_AC16_Planar',
    #
    'Confidence16',
]

component_32bit_formats = [
    'Confidence32f',
]

component_2d_formats = [
    #
    'Mono8',
    'Mono10',
    'Mono12',
    'Mono14',
    'Mono16',
    #
    'RGB8',
    'RGB10',
    'RGB12',
    'RGB14',
    'RGB16',
    #
    'BGR8',
    'BGR10',
    'BGR12',
    'BGR14',
    'BGR16',
    #
    'RGBa8',
    'RGBa10',
    'RGBa12',
    'RGBa14',
    'RGBa16',
    #
    'BGRa8',
    'BGRa10',
    'BGRa12',
    'BGRa14',
    'BGRa16',
    #
    'BayerGR8',
    'BayerGB8',
    'BayerRG8',
    'BayerBG8',
    #
    'BayerGR10',
    'BayerGB10',
    'BayerRG10',
    'BayerBG10',
    #
    'BayerGR12',
    'BayerGB12',
    'BayerRG12',
    'BayerBG12',
    #
    'BayerGR16',
    'BayerRG16',
    'BayerGB16',
    'BayerBG16',
    #
    'Coord3D_A8',
    'Coord3D_B8',
    'Coord3D_C8',
    'Coord3D_ABC8',
    'Coord3D_ABC8_Planar',
    'Coord3D_AC8',
    'Coord3D_AC8_Planar',
    'Coord3D_A16',
    'Coord3D_B16',
    'Coord3D_C16',
    'Coord3D_ABC16',
    'Coord3D_ABC16_Planar',
    'Coord3D_AC16',
    'Coord3D_AC16_Planar',
    'Coord3D_A32f',
    'Coord3D_B32f',
    'Coord3D_C32f',
    'Coord3D_ABC32f',
    'Coord3D_ABC32f_Planar',
    'Coord3D_AC32f',
    'Coord3D_AC32f_Planar',
    'Coord3D_A10p',
    'Coord3D_B10p',
    'Coord3D_C10p',
    'Coord3D_A12p',
    'Coord3D_B12p',
    'Coord3D_C12p',
    'Coord3D_ABC10p',
    'Coord3D_ABC10p_Planar',
    'Coord3D_ABC12p',
    'Coord3D_ABC12p_Planar',
    'Coord3D_AC10p',
    'Coord3D_AC10p_Planar',
    'Coord3D_AC12p',
    'Coord3D_AC12p_Planar',
    #
    'Confidence1',
    'Confidence1p',
    'Confidence8',
    'Confidence16',
    'Confidence32f',
]

rgb_formats = [
    #
    'RGB8',
    'RGB10',
    'RGB12',
    'RGB14',
    'RGB16',
]

rgba_formats = [
    #
    'RGBa8',
    'RGBa10',
    'RGBa12',
    'RGBa14',
    'RGBa16',
]

bgr_formats = [
    #
    'BGR8',
    'BGR10',
    'BGR12',
    'BGR14',
    'BGR16',
]

bgra_formats = [
    #
    'BGRa8',
    'BGRa10',
    'BGRa12',
    'BGRa14',
    'BGRa16',
]
