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
    'Raw', 'Mono', 'R', 'G', 'B',
    'Mono8', 'Mono10', 'Mono12', 'Mono14', 'Mono16',
    'Coord3D_A', 'Coord3D_B', 'Coord3D_C', 'Confidence',
]

lmn_444_location_formats = [
    'RGB', 'BGR',
    'YUV', 'YCbCr', 'YCbCr601', 'YCbCr709',
    'RGB8', 'RGB10', 'RGB12', 'RGB14', 'RGB16',
    'BGR8', 'BGR10', 'BGR12', 'BGR14', 'BGR16',
    'RGB8Packed',
    'Coord3D_ABC',
]

lmn_422_location_formats = [
    'YUV422', 'YCbCr422', 'YCbCr601_422', 'YCbCr709_422',
]

lmn_411_location_formats = [
    'YUV411', 'YCbCr411', 'YCbCr601_411', 'YCbCr709_411',
]

lmno_4444_location_formats = [
    'aRGB', 'YRGB', 'RGBa', 'BGRa',
    'RGBa8', 'RGBa10', 'RGBa12', 'RGBa14', 'RGBa16',
    'BGRa8', 'BGRa10', 'BGRa12', 'BGRa14', 'BGRa16',
]

lm_44_location_formats = [
    'Coord3D_AC',
]

bayer_location_formats = [
    #
    'BayerGR8', 'BayerGB8', 'BayerRG8', 'BayerBG8',
    #
    'BayerGR12', 'BayerGB12', 'BayerRG12', 'BayerBG12',
    #
    'BayerGR10', 'BayerGB10', 'BayerRG10', 'BayerBG10',
    #
    'BayerGR16', 'BayerRG16', 'BayerGB16', 'BayerBG16',
    #
    'BayerGR32', 'BayerRG32', 'BayerGB32', 'BayerBG32',
]

uint8_formats = [
    #
    'Mono8',
    #
    'RGB8', 'RGB8Packed', 'RGBa8',
    #
    'BGR8', 'BGRa8',
    #
    'BayerGR8', 'BayerGB8', 'BayerRG8', 'BayerBG8',
    #
    'Confidence8'
]

uint16_formats = [
    #
    'Mono10', 'Mono12', 'Mono14', 'Mono16',
    #
    'RGB10', 'RGB12', 'RGB14', 'RGB16',
    #
    'BGR10', 'BGR12', 'BGR14', 'BGR16',
    #
    'RGBa10', 'RGBa12', 'RGBa14', 'RGBa16',
    #
    'BGRa10', 'BGRa12', 'BGRa14', 'BGRa16',
    #
    'BayerGR10', 'BayerGB10', 'BayerRG10', 'BayerBG10',
    #
    'BayerGR12', 'BayerGB12', 'BayerRG12', 'BayerBG12',
    #
    'BayerGR16', 'BayerRG16', 'BayerGB16', 'BayerBG16',
    #
    'Coord3D_C16'
]

uint32_formats = [
    'Mono32',
]

float32_formats = [
    'Coord3D_A32f', 'Coord3D_B32f', 'Coord3D_C32f',
]

component_8bit_formats = [
    #
    'Mono8',
    #
    'RGB8', 'RGBa8',
    #
    'BGR8', 'BGRa8',
    #
    'BayerGR8', 'BayerGB8', 'BayerRG8', 'BayerBG8',
    #
    'Confidence8'
]

component_10bit_formats = [
    #
    'Mono10',
    #
    'RGB10', 'RGBa10',
    #
    'BGR10', 'BGRa10',
    #
    'BayerGR10', 'BayerGB10', 'BayerRG10', 'BayerBG10',
]

component_12bit_formats = [
    #
    'Mono12',
    #
    'RGB12', 'RGBa12',
    #
    'BGR12', 'BGRa12',
    #
    'BayerGR12', 'BayerGB12', 'BayerRG12', 'BayerBG12',
]

component_14bit_formats = [
    #
    'Mono14',
    #
    'RGB14', 'RGBa14',
    #
    'BGR14', 'BGRa14',
]

component_16bit_formats = [
    #
    'Mono16',
    #
    'RGB16', 'RGBa16',
    #
    'BayerGR16', 'BayerRG16', 'BayerGB16', 'BayerBG16',
    #
    'Coord3D_C16',
]

component_2d_formats = [
    #
    'Mono8', 'Mono10', 'Mono12', 'Mono14', 'Mono16',
    #
    'RGB8', 'RGB10', 'RGB12', 'RGB14', 'RGB16',
    #
    'BGR8', 'BGR10', 'BGR12', 'BGR14', 'BGR16',
    #
    'RGBa8', 'RGBa10', 'RGBa12', 'RGBa14', 'RGBa16',
    #
    'BGRa8', 'BGRa10', 'BGRa12', 'BGRa14', 'BGRa16',
    #
    'BayerGR8', 'BayerGB8', 'BayerRG8', 'BayerBG8',
    #
    'BayerGR10', 'BayerGB10', 'BayerRG10', 'BayerBG10',
    #
    'BayerGR12', 'BayerGB12', 'BayerRG12', 'BayerBG12',
    #
    'BayerGR16', 'BayerRG16', 'BayerGB16', 'BayerBG16',
    #
    'Coord3D_A32f', 'Coord3D_B32f', 'Coord3D_C32f',
    'Coord3D_C16',
    #
    'Confidence1', 'Confidence1p', 'Confidence8', 'Confidence16',
    'Confidence32f',
]

rgb_formats = [
    #
    'RGB8', 'RGB10', 'RGB12', 'RGB14', 'RGB16',
]

rgba_formats = [
    #
    'RGBa8', 'RGBa10', 'RGBa12', 'RGBa14', 'RGBa16',
]

bgr_formats = [
    #
    'BGR8', 'BGR10', 'BGR12', 'BGR14', 'BGR16',
]

bgra_formats = [
    #
    'BGRa8', 'BGRa10', 'BGRa12', 'BGRa14', 'BGRa16',
]
