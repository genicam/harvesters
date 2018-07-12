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


class ThreadBase:
    def __init__(self, mutex=None):
        #
        super().__init__()

        #
        self._is_running = False
        self._mutex = mutex

    def start(self):
        self._is_running = True
        self._start()

    def _start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def acquire(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    @property
    def is_running(self):
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value

    @property
    def worker(self):
        raise NotImplementedError

    @worker.setter
    def worker(self, obj):
        raise NotImplementedError

    @property
    def mutex(self):
        raise NotImplementedError


class MutexLocker:
    def __init__(self, thread: ThreadBase=None):
        #
        super().__init__()

        #
        self._thread = thread
        self._locked_mutex = None

    def __enter__(self):
        #
        if self._thread is None:
            return None

        #
        self._locked_mutex = self._thread.acquire()
        return self._locked_mutex

    def __exit__(self, exc_type, exc_val, exc_tb):
        #
        if self._thread is None:
            return

        #
        self._thread.release()


