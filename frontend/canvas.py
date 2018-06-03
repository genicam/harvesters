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
from PyQt5.QtCore import QMutexLocker

import numpy as np
from vispy import gloo
from vispy import app
from vispy.gloo import Program
from vispy.util.transforms import ortho

# Local application/library specific imports
from core.system import is_running_on_windows


class Canvas(app.Canvas):
    def __init__(self, harvester_core, width=640, height=480, mutex=None, fps=50., background_color='gray'):
        """
        NOTE: fps should be smaller than or equal to 50 fps. If it's exceed
        VisPy drags down the acquisition performance. This is the issue we
        have to investigate.
        """

        #
        app.Canvas.__init__(
            self, size=(width, height), vsync=True, autoswap=False
        )

        #
        self._background_color = background_color

        #
        self._magnification = 1.
        self._has_filled_texture = False

        #
        vertex = """
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

        fragment = """
            varying vec2 v_texcoord;
            uniform sampler2D texture;
            void main()
            {
                gl_FragColor = texture2D(texture, v_texcoord);
            }
        """

        #
        self._harvester_core = harvester_core
        self._mutex = mutex
        self._program = Program(vertex, fragment, count=4)
        self._width = width
        self._height = height

        self._data = np.zeros(
            4, dtype=[
                ('a_position', np.float32, 2),
                ('a_texcoord', np.float32, 2)
            ]
        )
        self._data['a_texcoord'] = np.array(
            [[0., 1.], [1., 1.], [0., 0.], [1., 0.]]
        )

        #
        self._program['u_model'] = np.eye(4, dtype=np.float32)
        self._program['u_view'] = np.eye(4, dtype=np.float32)

        #
        self._timer = app.Timer(1./fps, connect=self.update, start=True)

        #
        self._translate = 1.
        self._latest_translate = self._translate

        #
        self._is_dragging = False
        self._coordinate = [0, 0]
        self._origin = [0, 0]

        #
        self.set_rect(width, height)

        # If it's True , the canvas keeps image acquisition but do not
        # draw images on the canvas.
        self._pause_drawing = False

    def set_rect(self, width, height):
        #
        self._has_filled_texture = False

        #
        self._width = width
        self._height = height

        #
        self.apply_magnification()

    def on_draw(self, event):
        #
        with QMutexLocker(self._mutex):
            # Clear the canvas in gray.
            gloo.clear(color=self._background_color)

            if self._harvester_core.is_acquiring_images and not self._pause_drawing:
                if self._harvester_core.get_image(False) is not None:
                    # Draw the latest image on the canvas.
                    self._program['texture'] = self._harvester_core.get_image(False)
                else:
                    if self._has_filled_texture:
                        # Keep drawing the image recently drew on the canvas.
                        self._program['texture'] = self._program['texture']
                if not self._has_filled_texture:
                    self._has_filled_texture = True
            else:
                # Keep drawing the image recently drew on the canvas.
                if self._has_filled_texture:
                    self._program['texture'] = self._program['texture']

            # Actually draw the new image on the texture.
            self._program.draw('triangle_strip')

            # Then swap the texture. You'll see the canvas updates the
            # texture we see.
            self.swap_buffers()

    def on_resize(self, event):
        self.apply_magnification()

    def apply_magnification(self, swap_buffers=True):
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

        if swap_buffers:
            # Clear the canvas.
            gloo.clear(color=self._background_color)

            # Then swap the texture.
            self.swap_buffers()

    def on_mouse_wheel(self, event):
        self._translate += event.delta[1]
        power = 5. if is_running_on_windows() else 7.  # 2 ** power
        stride = 4.
        translate = self._translate
        translate = min(power * stride, translate)
        translate = max(-power * stride, translate)
        self._translate = translate
        self._magnification = 2 ** (self._translate / stride)
        if self._latest_translate != self._translate:
            self.apply_magnification(False)
            self._latest_translate = self._translate

    def on_mouse_press(self, event):
        self._is_dragging = True
        self._origin = event.pos

    def on_mouse_release(self, event):
        self._is_dragging = False

    def on_mouse_move(self, event):
        if self._is_dragging:
            ratio = self._magnification
            delta = event.pos - self._origin
            self._origin = event.pos
            self._coordinate[0] -= (delta[0] * ratio)
            self._coordinate[1] += (delta[1] * ratio)
            self.apply_magnification(False)

    def stop_drawing(self):
        self._timer.stop()

    def start_drawing(self):
        self._timer.start()

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

