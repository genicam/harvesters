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
from logging import Logger
from threading import Thread
import time
import unittest

# Related third party imports
from harvesters.core import ImageAcquirer

# Local application/library specific imports
from harvesters.test.base_harvester import TestHarvester


class LoggerIndexPair:
    def __init__(self, *, logger: Logger, index: int = 0):
        self._logger = logger
        self._index = index

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def index(self) -> int:
        return self._index


class CallbackWorker:
    @staticmethod
    def callback(node, context: LoggerIndexPair):
        context.logger.info(
            "source: {}; event: {}".format(context.index, node.value))


class NodeCallbackDemoThread(Thread):
    def __init__(self, acquire, index, logger):
        super().__init__()
        self._acquire = acquire
        self._logger = logger
        self._index = index

    def run(self):
        self._logger.info("{}; AND GIVEN: an equipped node map".format(self._index))
        self._acquire.remote_device.node_map.Width.value = 100 * (self._index + 1)
        self._acquire.remote_device.node_map.Height.value = 100 * (self._index + 1)
        self._acquire.remote_device.node_map.AcquisitionFrameRate.value = 200

        self._logger.info("{}; WHEN: enabling a node callback".format(self._index))
        context = LoggerIndexPair(logger=self._logger, index=self._index)
        worker = CallbackWorker()
        token = self._acquire.remote_device.register_node_callback(
            node_name='EventGameProgressMessage',
            callback=worker.callback, context=context)

        self._logger.info("{}; THEN: game progress appear".format(self._index))
        self._acquire.start()
        time.sleep(5)
        self._acquire.stop()

        self._logger.info("{}; AND WHEN: disabling a node callback".format(self._index))
        self._acquire.remote_device.deregister_node_callback(token)

        self._logger.info("{}; THEN: game progress does not appear anymore".format(self._index))
        self._acquire.start()
        time.sleep(3)
        self._acquire.stop()

        self._logger.info("{}; WHEN: destroying the acquirer".format(self._index))
        self._acquire.destroy()
        self._logger.info("{}; THEN: destroyed".format(self._index))


class TestTutorials(TestHarvester):

    def test_module_events_on_multi_threaded_application(self):
        if not self.is_running_with('viky'):
            self.skipTest("the given target is not appropriate")

        self._logger.info("GIVEN: one or more devices")
        threads = []
        nr_devices = len(self.harvester.device_info_list)

        self._logger.info("WHEN: letting events happen")
        for i in range(nr_devices):
            threads.append(
                NodeCallbackDemoThread(
                    self.harvester.create(i), i, self._logger))

        for t in threads:
            t.start()

        self._logger.info("THEN: events are observed on the console")

        for t in threads:
            t.join()

        self._logger.info("completed")

    def test_module_events_on_single_threaded_application(self):
        if not self.is_running_with('viky'):
            self.skipTest("the given target is not appropriate")

        self._logger.info("SCENARIO: enabling/disabling node callback")

        self._logger.info("GIVEN: an image acquirer")
        ia = self.harvester.create()  # type: ImageAcquirer

        self._logger.info("AND GIVEN: an equipped node map")
        ia.remote_device.node_map.Width.value = 100
        ia.remote_device.node_map.AcquisitionFrameRate.value = 200

        self._logger.info("WHEN: enabling a node callback")
        context = LoggerIndexPair(logger=self._logger)
        worker = CallbackWorker()
        token = ia.remote_device.register_node_callback(
            node_name='EventGameProgressMessage',
            callback=worker.callback, context=context)

        self._logger.info("THEN: game progress appear")
        ia.start()
        time.sleep(5)

        self._logger.info("AND WHEN: disabling a node callback")
        ia.remote_device.deregister_node_callback(token)

        self._logger.info("THEN: game progress does not appear anymore")
        time.sleep(3)
        ia.stop()

        self._logger.info("AND WHEN: destroying the acquirer")
        ia.destroy()
        self._logger.info("THEN: destroyed")


if __name__ == '__main__':
    unittest.main()
