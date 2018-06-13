#!/usr/bin/env python3
# ----------------------------------------------------------------------------
#
# Copyright 2018 EMVA
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ----------------------------------------------------------------------------


# Standard library imports
import setuptools

# Related third party imports

# Local application/library specific imports
import versioneer


with open('README.rst', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='genicam.harvester',
    version=versioneer.get_version(),
    author='Kazunari Kudo',
    author_email='who.is.kazunari@gmail.com',
    description='Image acquisition & data visualization with Python',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/genicam/harvester',
    packages=setuptools.find_packages(),
    classifiers=(
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
    ),
 )
