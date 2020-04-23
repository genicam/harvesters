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
from typing import Optional

# Related third party imports
import numpy

# Local application/library specific imports
from harvesters.util._pfnc import symbolics as _symbolics

#
symbolics = _symbolics
dict_by_ints = symbolics
dict_by_names = {n: i for i, n in symbolics.items()}

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


class DataBoundary:
    INT8 = 'int8'
    UINT8 = 'uint8'
    UINT16 = 'uint16'
    UINT32 = 'uint32'
    FLOAT32 = 'float32'

    def __init__(self, unpacked: str, packed: Optional[str] = None):
        #
        super().__init__()
        #
        self._unpacked = unpacked
        self._packed = packed if packed else unpacked
        #
        for target in (self._packed, self._unpacked):
            size = self._get_size(target)
            assert size > 0
            assert (size % 4) == 0
        assert self._get_size(self._unpacked) >= self._get_size(self._packed)

    def __repr__(self):
        repr = ''
        repr += 'Unpacked: {}, '.format(self.unpacked)
        repr += 'Unpacked size: {}, '.format(self.unpacked_size)
        repr += 'Packed: {}, '.format(self.packed)
        repr += 'Is packed: {}'.format(self.is_packed())
        return repr

    @property
    def unpacked(self):
        return self._unpacked

    @property
    def unpacked_size(self):
        return self._get_size(self.unpacked) / 8

    @property
    def packed(self):
        return self._packed

    def is_packed(self):
        return self._unpacked != self._packed

    def _get_size(self, dtype: str):
        if dtype in (self.INT8, self.UINT8):
            return 8
        elif dtype in (self.UINT16):
            return 16
        elif dtype in (self.UINT32, self.FLOAT32):
            return 32


class _Base:
    def __init__(self):
        #
        super().__init__()

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        raise NotImplementedError

    def _check_validity(self):
        raise NotImplementedError


class _PixelFormat(_Base):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = None
        self._symbolic = None
        self._nr_components = None
        self._unit_depth_in_bit = None

    @property
    def data_boundary(self):
        return self._data_boundary

    @property
    def symbolic(self) -> str:
        return self._symbolic

    @property
    def nr_components(self):
        return self._nr_components

    @property
    def depth_in_bit(self):
        return self._nr_components * self._unit_depth_in_bit

    @property
    def depth_in_byte(self):
        return self.depth_in_bit / 8

    def _finalize(self, symbolic: str):
        self._symbolic = symbolic
        self._check_validity()  # Make sure if the class has valid values.

    def _check_validity(self):
        assert self._data_boundary
        assert self._symbolic
        assert self._nr_components
        assert self._unit_depth_in_bit

    def __repr__(self):
        repr = ''
        repr += 'Symbolic: {}, '.format(self.symbolic)
        repr += 'Nr. components: {}, '.format(self.nr_components)
        repr += 'Depth[b]: {}, '.format(self.depth_in_bit)
        repr += 'Depth[B]: {}, '.format(self.depth_in_byte)
        repr += 'Data boundary: {}'.format(self.data_boundary)
        return repr


# ----


class _Unpacked(_PixelFormat):
    def __init__(self):
        #
        super().__init__()


# ----


class _Unpacked_Uint8(_Unpacked):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array


class _Unpacked_Int8(_Unpacked):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.INT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.int8)


class _Unpacked_Uint16(_Unpacked):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.uint16)


class _Unpacked_Float32(_Unpacked):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.FLOAT32)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.float32)


# ----

class _Mono_Unpacked_Uint8(_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


class _Mono_Unpacked_Int8(_Unpacked_Int8):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


class _Mono_Unpacked_Uint16(_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


class _Mono_Unpacked_Float32(_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.
        self._unit_depth_in_bit = 32


# ----


class Mono8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('Mono8')


class Mono8s(_Mono_Unpacked_Int8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('Mono8s')


class Mono10(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10
        #
        self._finalize('Mono10')


class Mono12(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12
        #
        self._finalize('Mono12')


class Mono14(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 14
        #
        self._finalize('Mono14')


class Mono16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('Mono16')


class R8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('R8')


class R10(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10
        #
        self._finalize('R10')


class R12(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12
        #
        self._finalize('R12')


class R16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('R16')


class G8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('G8')


class G10(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10
        #
        self._finalize('G10')


class G12(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12
        #
        self._finalize('G12')


class G16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('G16')


class B8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('B8')


class B10(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10
        #
        self._finalize('B10')


class B12(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12
        #
        self._finalize('B12')


class B16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('B16')


class Coord3D_A8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('Coord3D_A8')


class Coord3D_B8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('Coord3D_B8')


class Coord3D_C8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('Coord3D_C8')


class Coord3D_A16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('Coord3D_A8')


class Coord3D_B16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('Coord3D_B8')


class Coord3D_C16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('Coord3D_C8')


# ----


class Coord3D_A32f(_Mono_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_A32f')


class Coord3D_B32f(_Mono_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_B32f')


class Coord3D_C32f(_Mono_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_C32f')

# ----


class Confidence1(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 1
        #
        self._finalize('Confidence1')


class Confidence8(_Mono_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8
        #
        self._finalize('Confidence8')


class Confidence16(_Mono_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16
        #
        self._finalize('Confidence16')


class Confidence32f(_Mono_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 32
        #
        self._finalize('Confidence32f')


# ----


class _Packed(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16, packed=DataBoundary.UINT8)


# ----


class _GroupPacked(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16, packed=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        nr_packed = 3
        nr_unpacked = 2
        #
        p1st, p2nd, p3rd = numpy.reshape(
            array, (array.shape[0] // nr_packed, nr_packed)
        ).astype(numpy.uint16).T
        #
        up1st = p1st + p2nd << 8
        up2nd = p2nd >> 4 + p3rd << 4
        #
        return numpy.reshape(
            numpy.concatenate(
                (up1st[:, None], up2nd[:, None]), axis=1
            ),
            nr_unpacked * up1st.shape[0]
        )


# ----


class _GroupPacked_10(_GroupPacked):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10


class _GroupPacked_12(_GroupPacked):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12


# ----


class _10p(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16, packed=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        nr_packed = 4
        nr_unpacked = 3
        #
        p1st, p2nd, p3rd, p4th = numpy.reshape(
            array, (array.shape[0] // nr_packed, nr_packed)
        ).astype(numpy.uint16).T
        #
        up1st = p1st + p2nd << 8
        up2nd = p2nd >> 2 + p3rd << 6
        up3rd = p3rd >> 5 + p4th << 3
        #
        return numpy.reshape(
            numpy.concatenate(
                (up1st[:, None], up2nd[:, None], up3rd[:, None]), axis=1
            ),
            nr_unpacked * up1st.shape[0]
        )


class _12p(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16, packed=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        nr_packed = 3
        nr_unpacked = 2
        #
        p1st, p2nd, p3rd = numpy.reshape(
            array, (array.shape[0] // nr_packed, nr_packed)
        ).astype(numpy.uint16).T
        #
        up1st = p1st + p2nd << 8
        up2nd = p2nd >> 4 + p3rd << 4
        #
        return numpy.reshape(
            numpy.concatenate(
                (up1st[:, None], up2nd[:, None]), axis=1
            ),
            nr_unpacked * up1st.shape[0]
        )


# ----


class _Mono_10p(_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


class _Mono_12p(_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


# ----


class _Mono_GroupPacked_10(_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


class _Mono_GroupPacked_12(_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


# ----


class Mono10p(_Mono_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Mono10p')


class Mono10Packed(_Mono_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Mono10Packed')


class Mono12Packed(_Mono_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Mono12Packed')


class Mono12p(_Mono_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Mono12p')


class Coord3D_A10p(_Mono_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_A10p')


class Coord3D_B10p(_Mono_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_B10p')


class Coord3D_C10p(_Mono_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_C10p')


class _Coord3D_A12p(_Mono_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_A12p')


class Coord3D_A12p(_Mono_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_A12p')


class Coord3D_B12p(_Mono_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_B12p')


class Coord3D_C12p(_Mono_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_C12p')


# 'Mono1p',
# 'Mono2p',
# 'Mono4p',


# ----


class _LMN444_Unpacked_Uint8(_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3.


class _LMN444_Unpacked_Uint16(_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3.


class _LMN444_Unpacked_Float32(_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3.


# ----


class _LMN444_Unpacked_Uint8_8(_LMN444_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8


class _LMN444_Unpacked_Uint16_10(_LMN444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10


class _LMN444_Unpacked_Uint16_12(_LMN444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12


class _LMN444_Unpacked_Uint16_14(_LMN444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 14


class _LMN444_Unpacked_Uint16_16(_LMN444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16


class _LMN444_Unpacked_Float32_32(_LMN444_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 32


# ----


class RGB8(_LMN444_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGB8')


class RGB10(_LMN444_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGB10')


class RGB12(_LMN444_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGB12')


class RGB14(_LMN444_Unpacked_Uint16_14):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGB14')


class RGB16(_LMN444_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGB16')


# ----


class BGR8(_LMN444_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGR8')


class BGR10(_LMN444_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGR10')


class BGR12(_LMN444_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGR12')


class BGR14(_LMN444_Unpacked_Uint16_14):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGR14')


class BGR16(_LMN444_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGR16')


# ----


class Coord3D_ABC8(_LMN444_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC8')


class Coord3D_ABC8_Planar(_LMN444_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC8_Planar')


# ----


class Coord3D_ABC16(_LMN444_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC16')


class Coord3D_ABC16_Planar(_LMN444_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC16_Planar')


# ----


class Coord3D_ABC32f(_LMN444_Unpacked_Float32_32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC32f')


class Coord3D_ABC32f_Planar(_LMN444_Unpacked_Float32_32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC32f_Planar')


# 'RGB8Packed',


# ----


class _LMN444_10p(_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3.


class _LMN444_12p(_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3.


# ----


class Coord3D_ABC10p(_LMN444_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC10p')


class Coord3D_ABC10p_Planar(_LMN444_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC10p_Planar')


class Coord3D_ABC12p(_LMN444_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC12p')


class Coord3D_ABC12p_Planar(_LMN444_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_ABC12p_Planar')


# ----


class _LMN422(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2.


class _LMN411(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.5


class _LMNO4444(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 4.


# ----


class _LMN422_Unpacked_Uint8(_LMN422):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array


class _LMN422_Unpacked_Uint16(_LMN422):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.uint16)


class _LMN411_Unpacked_Uint8(_LMN411):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array


class _LMNO4444_Unpacked_Uint8(_LMNO4444):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array


# ----


class _LMN422_GroupPacked_10(_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3


class _LMN422_GroupPacked_12(_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 3


class _LMN422_10p(_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2


class _LMN422_12p(_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2


# ----


class _LMN422_Unpacked_Uint8_8(_LMN422_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8


class _LMN422_Unpacked_Uint16_10(_LMN422_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10


class _LMN422_Unpacked_Uint16_12(_LMN422_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12


class _LMN411_Unpacked_Uint8_8(_LMN411_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8


class _LMNO4444_Unpacked_Uint8_8(_LMNO4444_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        self._unit_depth_in_bit = 8


# ----


class YUV422_8_UYVY(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YUV422_8_UYVY')


class YUV422_8(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YUV422_8')


class YCbCr422_8(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_8')


class YCbCr601_422_8(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_8')


class YCbCr709_422_8(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_8')


class YCbCr422_8_CbYCrY(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_8_CbYCrY')


class YCbCr601_422_8_CbYCrY(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_8_CbYCrY')


class YCbCr709_422_8_CbYCrY(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_8_CbYCrY')


class YCbCr2020_422_8(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_8')


class YCbCr2020_422_8_CbYCrY(_LMN422_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_8_CbYCrY')


class YCbCr422_10(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_10')


class YCbCr601_422_10(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_10')


class YCbCr709_422_10(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_10')


class YCbCr422_10_CbYCrY(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_10_CbYCrY')


class YCbCr601_422_10_CbYCrY(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_10_CbYCrY')


class YCbCr709_422_10_CbYCrY(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_10_CbYCrY')


class YCbCr2020_422_10(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_10')


class YCbCr2020_422_10_CbYCrY(_LMN422_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_10_CbYCrY')


class YCbCr422_12(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_12')


class YCbCr601_422_12(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_12')


class YCbCr709_422_12(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_12')


class YCbCr422_12_CbYCrY(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_12_CbYCrY')


class YCbCr601_422_12_CbYCrY(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_12_CbYCrY')


class YCbCr709_422_12_CbYCrY(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_12_CbYCrY')


class YCbCr2020_422_12(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_12')


class YCbCr2020_422_12_CbYCrY(_LMN422_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_12_CbYCrY')


# ----


class YCbCr422_10p(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_10p')


class YCbCr601_422_10p(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_10p')


class YCbCr601_422_12p(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_12p')


class YCbCr709_422_10p(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_10p')


class YCbCr422_10p_CbYCrY(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_10p_CbYCrY')


class YCbCr601_422_10p_CbYCrY(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_10p_CbYCrY')


class YCbCr709_422_10p_CbYCrY(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_10p_CbYCrY')


class YCbCr2020_422_10p(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_10p')


class YCbCr2020_422_10p_CbYCrY(_LMN422_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_10p_CbYCrY')


class YCbCr422_12p(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_12p')


class YCbCr709_422_12p(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_12p')


class YCbCr422_12p_CbYCrY(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr422_12p_CbYCrY')


class YCbCr601_422_12p_CbYCrY(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_422_12p_CbYCrY')


class YCbCr709_422_12p_CbYCrY(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_422_12p_CbYCrY')


class YCbCr2020_422_12p(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_12p')


class YCbCr2020_422_12p_CbYCrY(_LMN422_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_422_12p_CbYCrY')


class YUV411_8_UYYVYY(_LMN411_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YUV411_8_UYYVYY')


class YCbCr411_8_CbYYCrYY(_LMN411_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr411_8_CbYYCrYY')


class YCbCr601_411_8_CbYYCrYY(_LMN411_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr601_411_8_CbYYCrYY')


class YCbCr709_411_8_CbYYCrYY(_LMN411_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr709_411_8_CbYYCrYY')


class YCbCr411_8(_LMN411_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr411_8')


class YCbCr2020_411_8_CbYYCrYY(_LMN411_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('YCbCr2020_411_8_CbYYCrYY')


class RGBa8(_LMNO4444_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa8')


class BGRa8(_LMNO4444_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa8')


# ----


class _LMNO4444_Unpacked_Uint16(_LMNO4444):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.uint16)


class _LMNO4444_10p(_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 4.


class _LMNO4444_12p(_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 4.


# ----


class _LMNO4444_Unpacked_Uint16_10(_LMNO4444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10


class _LMNO4444_Unpacked_Uint16_12(_LMNO4444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12


class _LMNO4444_Unpacked_Uint16_14(_LMNO4444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 14


class _LMNO4444_Unpacked_Uint16_16(_LMNO4444_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16


# ----


class RGBa10(_LMNO4444_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa10')


class BGRa10(_LMNO4444_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa10')


class RGBa12(_LMNO4444_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa12')


class BGRa12(_LMNO4444_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa12')


class RGBa14(_LMNO4444_Unpacked_Uint16_14):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa14')


class BGRa14(_LMNO4444_Unpacked_Uint16_14):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa14')


class RGBa16(_LMNO4444_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa16')


class BGRa16(_LMNO4444_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa16')


class RGBa10p(_LMNO4444_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa10p')


class BGRa10p(_LMNO4444_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa10p')


class RGBa12p(_LMNO4444_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('RGBa12p')


class BGRa12p(_LMNO4444_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BGRa12p')


# ----


class _LM44(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2.


class _LM44_Unpacked_Float32(_LM44):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.FLOAT32)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.float32)


class _LM44_GroupPacked_10(_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2


class _LM44_GroupPacked_12(_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2



class _LM44_10p(_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        raise NotImplementedError


class _LM44_12p(_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 2

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        raise NotImplementedError


class _LM44_Unpacked_Uint8(_LM44):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT8)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array


class _LM44_Unpacked_Uint16(_LM44):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.uint16)


# ----


class _LM44_Unpacked_Uint8_8(_LM44_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 8


class _LM44_Unpacked_Uint16_16(_LM44_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16


# ----


class _LM44_Unpacked_Float32_32(_LM44_Unpacked_Float32):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 32


class Coord3D_AC32f(_LM44_Unpacked_Float32_32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC32f')


class Coord3D_AC32f_Planar(_LM44_Unpacked_Float32_32):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC32f_Planar')


class Coord3D_AC8(_LM44_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC8')


class Coord3D_AC8_Planar(_LM44_Unpacked_Uint8_8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC8_Planar')


class Coord3D_AC10p(_LM44_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC10p')


class Coord3D_AC10p_Planar(_LM44_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC10p_Planar')


class Coord3D_AC12p(_LM44_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC12p')


class Coord3D_AC12p_Planar(_LM44_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC12p_Planar')


class Coord3D_AC16(_LM44_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC16')


class Coord3D_AC16_Planar(_LM44_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('Coord3D_AC16_Planar')


# ----


class _Bayer(_PixelFormat):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1.


# ----


class _Bayer_Unpacked_Uint8(_Bayer):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT8)
        self._unit_depth_in_bit = 8

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array


class _Bayer_Unpacked_Uint16(_Bayer):
    def __init__(self):
        #
        super().__init__()
        #
        self._data_boundary = DataBoundary(unpacked=DataBoundary.UINT16)

    def expand(self, array: numpy.ndarray) -> numpy.ndarray:
        return array.view(numpy.uint16)


# ----


class _Bayer_Unpacked_Uint16_10(_Bayer_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 10


class _Bayer_Unpacked_Uint16_12(_Bayer_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 12


class _Bayer_Unpacked_Uint16_16(_Bayer_Unpacked_Uint16):
    def __init__(self):
        #
        super().__init__()
        #
        self._unit_depth_in_bit = 16


# ----


class BayerGR8(_Bayer_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR8')


class BayerRG8(_Bayer_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG8')


class BayerGB8(_Bayer_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB8')


class BayerBG8(_Bayer_Unpacked_Uint8):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG8')


class BayerGR10(_Bayer_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR10')


class BayerRG10(_Bayer_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG10')


class BayerGB10(_Bayer_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB10')


class BayerBG10(_Bayer_Unpacked_Uint16_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG10')


class BayerGR12(_Bayer_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR12')


class BayerRG12(_Bayer_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG12')


class BayerGB12(_Bayer_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB12')


class BayerBG12(_Bayer_Unpacked_Uint16_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG12')


class BayerGR16(_Bayer_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR16')


class BayerRG16(_Bayer_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG16')


class BayerGB16(_Bayer_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB16')


class BayerBG16(_Bayer_Unpacked_Uint16_16):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG16')


# ----


class _Bayer_GroupPacked_10(_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1


class _Bayer_GroupPacked_12(_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1


class _Bayer_10p(_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1


class _Bayer_12p(_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._nr_components = 1


# ----


class BayerGR10Packed(_Bayer_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR10Packed')


class BayerRG10Packed(_Bayer_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG10Packed')


class BayerGB10Packed(_Bayer_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB10Packed')


class BayerBG10Packed(_Bayer_GroupPacked_10):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG10Packed')


class BayerBG10p(_Bayer_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG10p')


class BayerGB10p(_Bayer_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB10p')


class BayerGR10p(_Bayer_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR10p')


class BayerRG10p(_Bayer_10p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG10p')


class BayerGR12Packed(_Bayer_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR12Packed')


class BayerRG12Packed(_Bayer_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG12Packed')


class BayerGB12Packed(_Bayer_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB12Packed')


class BayerBG12Packed(_Bayer_GroupPacked_12):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG12Packed')


class BayerBG12p(_Bayer_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerBG12p')


class BayerGB12p(_Bayer_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGB12p')


class BayerGR12p(_Bayer_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerGR12p')


class BayerRG12p(_Bayer_12p):
    def __init__(self):
        #
        super().__init__()
        #
        self._finalize('BayerRG12p')


class NpArrayFactory:
    _pixel_formats = [
        Mono8(),
        Mono8s(),
        Mono10(),
        Mono12(),
        Mono14(),
        Mono16(),
        R8(),
        R10(),
        R12(),
        R16(),
        G8(),
        G10(),
        G12(),
        G16(),
        B8(),
        B10(),
        B12(),
        B16(),
        Coord3D_A8(),
        Coord3D_B8(),
        Coord3D_C8(),
        Coord3D_A16(),
        Coord3D_B16(),
        Coord3D_C16(),
        Coord3D_A32f(),
        Coord3D_B32f(),
        Coord3D_C32f(),
        Confidence1(),
        Confidence8(),
        Confidence16(),
        Confidence32f(),
        # Mono1p(),
        # Mono2p(),
        # Mono4p(),
        Mono10Packed(),
        Mono10p(),
        Mono12Packed(),
        Mono12p(),
        Coord3D_A10p(),
        Coord3D_B10p(),
        Coord3D_C10p(),
        Coord3D_A12p(),
        Coord3D_B12p(),
        Coord3D_C12p(),
        RGB8(),
        RGB10(),
        RGB12(),
        RGB14(),
        RGB16(),
        BGR8(),
        BGR10(),
        BGR12(),
        BGR14(),
        BGR16(),
        Coord3D_ABC8(),
        Coord3D_ABC8_Planar(),
        Coord3D_ABC16(),
        Coord3D_ABC16_Planar(),
        Coord3D_ABC32f(),
        Coord3D_ABC32f_Planar(),
        # RGB8Packed(),
        Coord3D_ABC10p(),
        Coord3D_ABC10p_Planar(),
        Coord3D_ABC12p(),
        Coord3D_ABC12p_Planar(),
        YUV422_8_UYVY(),
        YUV422_8(),
        YCbCr422_8(),
        YCbCr601_422_8(),
        YCbCr709_422_8(),
        YCbCr422_8_CbYCrY(),
        YCbCr601_422_8_CbYCrY(),
        YCbCr709_422_8_CbYCrY(),
        YCbCr422_10(),
        YCbCr422_12(),
        YCbCr601_422_10(),
        YCbCr601_422_12(),
        YCbCr709_422_10(),
        YCbCr709_422_12(),
        YCbCr422_10_CbYCrY(),
        YCbCr422_12_CbYCrY(),
        YCbCr601_422_10_CbYCrY(),
        YCbCr601_422_12_CbYCrY(),
        YCbCr709_422_10_CbYCrY(),
        YCbCr709_422_12_CbYCrY(),
        YCbCr2020_422_8(),
        YCbCr2020_422_8_CbYCrY(),
        YCbCr2020_422_10(),
        YCbCr2020_422_10_CbYCrY(),
        YCbCr2020_422_12(),
        YCbCr2020_422_12_CbYCrY(),
        YCbCr422_10p(),
        YCbCr422_12p(),
        YCbCr601_422_10p(),
        YCbCr601_422_12p(),
        YCbCr709_422_10p(),
        YCbCr709_422_12p(),
        YCbCr422_10p_CbYCrY(),
        YCbCr422_12p_CbYCrY(),
        YCbCr601_422_10p_CbYCrY(),
        YCbCr601_422_12p_CbYCrY(),
        YCbCr709_422_10p_CbYCrY(),
        YCbCr709_422_12p_CbYCrY(),
        YCbCr2020_422_10p(),
        YCbCr2020_422_10p_CbYCrY(),
        YCbCr2020_422_12p(),
        YCbCr2020_422_12p_CbYCrY(),
        YUV411_8_UYYVYY(),
        YCbCr411_8_CbYYCrYY(),
        YCbCr601_411_8_CbYYCrYY(),
        YCbCr709_411_8_CbYYCrYY(),
        YCbCr411_8(),
        YCbCr2020_411_8_CbYYCrYY(),
        RGBa8(),
        RGBa10(),
        RGBa12(),
        RGBa14(),
        RGBa16(),
        BGRa8(),
        BGRa10(),
        BGRa12(),
        BGRa14(),
        BGRa16(),
        RGBa10p(),
        RGBa12p(),
        BGRa10p(),
        BGRa12p(),
        Coord3D_AC8(),
        Coord3D_AC8_Planar(),
        Coord3D_AC16(),
        Coord3D_AC16_Planar(),
        Coord3D_AC32f(),
        Coord3D_AC32f_Planar(),
        Coord3D_AC10p(),
        Coord3D_AC10p_Planar(),
        Coord3D_AC12p(),
        Coord3D_AC12p_Planar(),
        BayerGR8(),
        BayerRG8(),
        BayerGB8(),
        BayerBG8(),
        BayerGR10(),
        BayerRG10(),
        BayerGB10(),
        BayerBG10(),
        BayerGR12(),
        BayerRG12(),
        BayerGB12(),
        BayerBG12(),
        BayerGR16(),
        BayerRG16(),
        BayerGB16(),
        BayerBG16(),
        BayerGR10Packed(),
        BayerRG10Packed(),
        BayerGB10Packed(),
        BayerBG10Packed(),
        BayerGR12Packed(),
        BayerRG12Packed(),
        BayerGB12Packed(),
        BayerBG12Packed(),
        BayerBG10p(),
        BayerBG12p(),
        BayerGB10p(),
        BayerGB12p(),
        BayerGR10p(),
        BayerGR12p(),
        BayerRG10p(),
        BayerRG12p(),
    ]

    def __init__(self):
        #
        super().__init__()
        #
        for p in self._pixel_formats:
            print(p)
        pass

    @classmethod
    def get_proxy(cls, symbolic: str):
        #
        _pf = None
        for pf in cls._pixel_formats:
            if symbolic == pf.symbolic:
                _pf = pf
                break
        #
        return _pf


"""
_pixel_formats = [
    Mono8(),
    Mono8s(),
    Mono10(),
    Mono12(),
    Mono14(),
    Mono16(),
    R8(),
    R10(),
    R12(),
    R16(),
    G8(),
    G10(),
    G12(),
    G16(),
    B8(),
    B10(),
    B12(),
    B16(),
    Coord3D_A8(),
    Coord3D_B8(),
    Coord3D_C8(),
    Coord3D_A16(),
    Coord3D_B16(),
    Coord3D_C16(),
    Coord3D_A32f(),
    Coord3D_B32f(),
    Coord3D_C32f(),
    Confidence1(),
    Confidence8(),
    Confidence16(),
    Confidence32f(),
    # Mono1p(),
    # Mono2p(),
    # Mono4p(),
    Mono10Packed(),
    Mono10p(),
    Mono12Packed(),
    Mono12p(),
    Coord3D_A10p(),
    Coord3D_B10p(),
    Coord3D_C10p(),
    Coord3D_A12p(),
    Coord3D_B12p(),
    Coord3D_C12p(),
    RGB8(),
    RGB10(),
    RGB12(),
    RGB14(),
    RGB16(),
    BGR8(),
    BGR10(),
    BGR12(),
    BGR14(),
    BGR16(),
    Coord3D_ABC8(),
    Coord3D_ABC8_Planar(),
    Coord3D_ABC16(),
    Coord3D_ABC16_Planar(),
    Coord3D_ABC32f(),
    Coord3D_ABC32f_Planar(),
    # RGB8Packed(),
    Coord3D_ABC10p(),
    Coord3D_ABC10p_Planar(),
    Coord3D_ABC12p(),
    Coord3D_ABC12p_Planar(),
    YUV422_8_UYVY(),
    YUV422_8(),
    YCbCr422_8(),
    YCbCr601_422_8(),
    YCbCr709_422_8(),
    YCbCr422_8_CbYCrY(),
    YCbCr601_422_8_CbYCrY(),
    YCbCr709_422_8_CbYCrY(),
    YCbCr422_10(),
    YCbCr422_12(),
    YCbCr601_422_10(),
    YCbCr601_422_12(),
    YCbCr709_422_10(),
    YCbCr709_422_12(),
    YCbCr422_10_CbYCrY(),
    YCbCr422_12_CbYCrY(),
    YCbCr601_422_10_CbYCrY(),
    YCbCr601_422_12_CbYCrY(),
    YCbCr709_422_10_CbYCrY(),
    YCbCr709_422_12_CbYCrY(),
    YCbCr2020_422_8(),
    YCbCr2020_422_8_CbYCrY(),
    YCbCr2020_422_10(),
    YCbCr2020_422_10_CbYCrY(),
    YCbCr2020_422_12(),
    YCbCr2020_422_12_CbYCrY(),
    YCbCr422_10p(),
    YCbCr422_12p(),
    YCbCr601_422_10p(),
    YCbCr601_422_12p(),
    YCbCr709_422_10p(),
    YCbCr709_422_12p(),
    YCbCr422_10p_CbYCrY(),
    YCbCr422_12p_CbYCrY(),
    YCbCr601_422_10p_CbYCrY(),
    YCbCr601_422_12p_CbYCrY(),
    YCbCr709_422_10p_CbYCrY(),
    YCbCr709_422_12p_CbYCrY(),
    YCbCr2020_422_10p(),
    YCbCr2020_422_10p_CbYCrY(),
    YCbCr2020_422_12p(),
    YCbCr2020_422_12p_CbYCrY(),
    YUV411_8_UYYVYY(),
    YCbCr411_8_CbYYCrYY(),
    YCbCr601_411_8_CbYYCrYY(),
    YCbCr709_411_8_CbYYCrYY(),
    YCbCr411_8(),
    YCbCr2020_411_8_CbYYCrYY(),
    RGBa8(),
    RGBa10(),
    RGBa12(),
    RGBa14(),
    RGBa16(),
    BGRa8(),
    BGRa10(),
    BGRa12(),
    BGRa14(),
    BGRa16(),
    RGBa10p(),
    RGBa12p(),
    BGRa10p(),
    BGRa12p(),
    Coord3D_AC8(),
    Coord3D_AC8_Planar(),
    Coord3D_AC16(),
    Coord3D_AC16_Planar(),
    Coord3D_AC32f(),
    Coord3D_AC32f_Planar(),
    Coord3D_AC10p(),
    Coord3D_AC10p_Planar(),
    Coord3D_AC12p(),
    Coord3D_AC12p_Planar(),
    BayerGR8(),
    BayerRG8(),
    BayerGB8(),
    BayerBG8(),
    BayerGR10(),
    BayerRG10(),
    BayerGB10(),
    BayerBG10(),
    BayerGR12(),
    BayerRG12(),
    BayerGB12(),
    BayerBG12(),
    BayerGR16(),
    BayerRG16(),
    BayerGB16(),
    BayerBG16(),
    BayerGR10Packed(),
    BayerRG10Packed(),
    BayerGB10Packed(),
    BayerBG10Packed(),
    BayerGR12Packed(),
    BayerRG12Packed(),
    BayerGB12Packed(),
    BayerBG12Packed(),
    BayerBG10p(),
    BayerBG12p(),
    BayerGB10p(),
    BayerGB12p(),
    BayerGR10p(),
    BayerGR12p(),
    BayerRG10p(),
    BayerRG12p(),
]
"""

