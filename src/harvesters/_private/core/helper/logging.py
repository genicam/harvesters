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
from logging import getLogger
from logging import StreamHandler, Formatter
from logging import ERROR

# Related third party imports

# Local application/library specific imports


def get_logger(*, logger_given=None, name=None, level=ERROR):
    #
    if logger_given:
        logger = logger_given
    else:
        # Use our logger:
        if not name:
            name = __name__

        logger = getLogger(name)
        logger.setLevel(level)

        #
        logging_handler = StreamHandler()

        # Check if handlers are already present:
        if logger.hasHandlers():
            # Then clear the handlers before adding new handlers:
            logger.handlers.clear()

        # Set up the formatter:
        formatter = Formatter(
            '%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s'
        )
        logging_handler.setFormatter(formatter)
        logging_handler.setLevel(level)

        #
        logger.addHandler(logging_handler)

        #
        logger.propagate = False

    return logger


