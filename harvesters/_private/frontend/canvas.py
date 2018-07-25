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

import numpy as np
from vispy import gloo
from vispy import app
from vispy.gloo import Program
from vispy.util.transforms import ortho

# Local application/library specific imports
from harvesters._private.core.helper.system import is_running_on_macos


class Canvas(app.Canvas):
    def __init__(
            self,
            harvester_core=None,
            width=640, height=480,
            fps=50.,
            background_color='gray',
            vertex_shader=None,
            fragment_shader=None
    ):
        """
        NOTE: fps should be smaller than or equal to 50 fps. If it's exceed
        VisPy drags down the acquisition performance. This is the issue we
        have to investigate.
        """

        self._vertex_shader = vertex_shader if vertex_shader else """
            // Uniforms
            uniform mat4 u_model;
            uniform mat4 u_view;
            uniform mat4 u_projection;

            // Attributes
            attribute vec2 a_position;
            attribute vec2 a_texcoord;

            // Varyings
            varying vec2 v_texcoord;

            // Main
            void main (void)
            {
                v_texcoord = a_texcoord;
                gl_Position = u_projection * u_view * u_model * vec4(a_position, 0.0, 1.0);
            }
        """

        self._fragment_shader = fragment_shader if fragment_shader else """
            varying vec2 v_texcoord;
            uniform sampler2D texture;
            void main()
            {
                gl_FragColor = texture2D(texture, v_texcoord);
            }
        """

        #
        self._harvester_core = harvester_core

        #
        app.Canvas.__init__(
            self, size=(width, height), vsync=True, autoswap=True
        )

        #
        self._program = None
        self._data = None
        self._coordinate = None
        self._origin = None
        self._translate = 0.
        self._latest_translate = self._translate
        self._magnification = 1.

        #
        self._background_color = background_color
        self._has_filled_texture = False
        self._width, self._height = width, height

        #
        self._is_dragging = False

        # If it's True , the canvas keeps image acquisition but do not
        # draw images on the canvas.
        self._pause_drawing = False

        # Apply shaders.
        self.set_shaders(
            vertex_shader=self._vertex_shader,
            fragment_shader=self._fragment_shader
        )

        #
        self._timer = app.Timer(1./fps, connect=self.update, start=True)

    def set_shaders(self, vertex_shader=None, fragment_shader=None):
        #
        vs = vertex_shader if vertex_shader else self._vertex_shader
        fs = fragment_shader if fragment_shader else self._fragment_shader
        self._program = Program(vs, fs, count=4)

        #
        self._data = np.zeros(
            4, dtype=[
                ('a_position', np.float32, 2),
                ('a_texcoord', np.float32, 2)
            ]
        )

        #
        self._data['a_texcoord'] = np.array(
            [[0., 1.], [1., 1.], [0., 0.], [1., 0.]]
        )

        #
        self._program['u_model'] = np.eye(4, dtype=np.float32)
        self._program['u_view'] = np.eye(4, dtype=np.float32)

        #
        self._coordinate = [0, 0]
        self._origin = [0, 0]

        #
        self._program['texture'] = np.zeros(
            (self._height, self._width), dtype='uint8'
        )

        #
        self.apply_magnification()

    def set_rect(self, width, height):
        #
        self._has_filled_texture = False

        #
        updated = False

        #
        if self._width != width or self._height != height:
            self._width = width
            self._height = height
            updated = True

        #
        if updated:
            self.apply_magnification()

    def on_draw(self, event):
        # Clear the canvas in gray.
        gloo.clear(color=self._background_color)
        self._update_texture()

    def _update_texture(self):
        # Fetch a buffer.
        try:
            with self._harvester_core.fetch_buffer(timeout_ms=0.1) as buffer:
                # Set the image as the texture of our canvas.
                if not self._pause_drawing and buffer:
                    # Update the canvas size if needed.
                    self.set_rect(buffer.image.width, buffer.image.height)
                    self._program['texture'] = buffer.image.ndarray

                # Draw the texture.
                self._draw()

        except AttributeError:
            # Harvester Core has not started image acquisition so
            # calling fetch_buffer() raises AttributeError because
            # None object is used for the with statement.

            # Update on June 15th, 2018:
            # According to a VisPy developer, they have not finished
            # porting VisPy to PyQt5. Once they finished the development
            # we should try it out if it gives us the maximum refresh rate.
            # See the following URL to check the latest information:
            #
            #     https://github.com/vispy/vispy/issues/1394

            # Draw the texture.
            self._draw()

    def _draw(self):
        self._program.draw('triangle_strip')

    def on_resize(self, event):
        self.apply_magnification()

    def apply_magnification(self):
        #
        canvas_w, canvas_h = self.physical_size
        gloo.set_viewport(0, 0, canvas_w, canvas_h)

        #
        ratio = self._magnification
        w, h = self._width, self._height

        self._program['u_projection'] = ortho(
            self._coordinate[0],
            canvas_w * ratio + self._coordinate[0],
            self._coordinate[1],
            canvas_h * ratio + self._coordinate[1],
            -1, 1
        )

        x, y = int((canvas_w * ratio - w) / 2), int((canvas_h * ratio - h) / 2)  # centering x & y

        #
        self._data['a_position'] = np.array(
            [[x, y], [x + w, y], [x, y + h], [x + w, y + h]]
        )

        #
        self._program.bind(gloo.VertexBuffer(self._data))

    def on_mouse_wheel(self, event):
        self._translate += event.delta[1]
        power = 7. if is_running_on_macos() else 5.  # 2 ** power
        stride = 4. if is_running_on_macos() else 7.
        translate = self._translate
        translate = min(power * stride, translate)
        translate = max(-power * stride, translate)
        self._translate = translate
        self._magnification = 2 ** -(self._translate / stride)
        if self._latest_translate != self._translate:
            self.apply_magnification()
            self._latest_translate = self._translate

    def on_mouse_press(self, event):
        self._is_dragging = True
        self._origin = event.pos

    def on_mouse_release(self, event):
        self._is_dragging = False

    def on_mouse_move(self, event):
        if self._is_dragging:
            adjustment = 2. if is_running_on_macos() else 1.
            ratio = self._magnification * adjustment
            delta = event.pos - self._origin
            self._origin = event.pos
            self._coordinate[0] -= (delta[0] * ratio)
            self._coordinate[1] += (delta[1] * ratio)
            self.apply_magnification()

    def pause_drawing(self, pause=True):
        self._pause_drawing = pause

    def toggle_drawing(self):
        self._pause_drawing = False if self._pause_drawing else True

    @property
    def is_pausing(self):
        return True if self._pause_drawing else False

    def resume_drawing(self):
        self._pause_drawing = False

    @property
    def background_color(self):
        return self._background_color

    @background_color.setter
    def background_color(self, color):
        self._background_color = color

