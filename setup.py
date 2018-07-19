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
import os
import setuptools
from distutils import log

# Related third party imports

# Local application/library specific imports
import versioneer as versioneer


#
log.set_verbosity(log.DEBUG)
log.info('Entered setup.py')
log.info('$PATH=%s' % os.environ['PATH'])

__doc__ = ''
with open('README.rst', 'r',encoding='utf-8_sig') as fh:
    __doc__ = fh.read()

name = 'harvesters'
description = 'Image acquisition & data visualization library with Python maintained by the official GenICam committee'

setuptools.setup(
    author='The GenICam Committee',
    author_email='genicam@list.stemmer-imaging.com',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
    description=description,
    download_url='https://pypi.org/project/harvesters/',
    install_requires=['numpy'],
    license='Apache Software License V2.0',
    long_description=__doc__,
    long_description_content_type='text/x-rst',
    name=name,
    package_dir={
        'harvesters': 'harvesters'
    },
    package_data={
        'harvesters': [
            '_private/frontend/image/*/*.jpg',
            '_private/frontend/image/*/*.png'
        ]
    },
    packages=setuptools.find_packages(),
    platforms='any',
    provides=['harvesters'],
    url='https://github.com/genicam/harvesters',
    version=versioneer.get_version(),
)
