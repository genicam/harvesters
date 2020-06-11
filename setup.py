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
import sys

# Related third party imports

# Local application/library specific imports
import versioneer as versioneer

#
log.set_verbosity(log.DEBUG)
log.info('Entered setup.py')
log.info('$PATH=%s' % os.environ['PATH'])


# Check the Python version:
supported_versions = [(3, 4), (3, 5), (3, 6)]
if sys.version_info in supported_versions:
    raise RuntimeError(
        'See https://github.com/genicam/harvesters#requirements'
    )


with open('README.rst', 'r',encoding='utf-8_sig') as fh:
    __doc__ = fh.read()

description = '🌈 Friendly Image Acquisition Library for Computer Vision People'

# Determine the base directory:
base_dir = os.path.dirname(__file__)
src_dir = os.path.join(base_dir, 'src')

# Make our package importable when executing setup.py;
# the package is located in src_dir:
sys.path.insert(0, src_dir)


# genicam package does not support 3.8 so 1.0.1 is the only way where
# people can install harvesters package:
dep_ver_genicam = '1.0.1' if sys.version_info.major == 3 and \
        sys.version_info.minor == 8 else '1.0.0'


setuptools.setup(
    # The author of the package:
    author='The GenICam Committee',
    author_email='genicam@list.stemmer-imaging.com',
    # Tells the index and pip some additional metadata about our package:
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ),
    # A short, on-sentence summary of the package:
    description=description,
    # Location where the package may be downloaded:
    download_url='https://pypi.org/project/harvesters/',
    # A list of required Python modules:
    install_requires=[
        'genicam==' + dep_ver_genicam,
        'numpy'
    ],
    #
    license='Apache Software License V2.0',
    # A detailed description of the package:
    long_description=__doc__,
    # The index to tell what type of markup is used for the long description:
    long_description_content_type='text/x-rst',
    # The name of the package:
    name='harvesters',
    # A list of all Python import packages that should be included in the
    # distribution package:
    packages=setuptools.find_packages(where='src'),
    # Keys: Package names; an empty name stands for the root package.
    # Values: Directory names relative to the setup.py.
    package_dir={
        '': 'src'
    },
    # Keys: Package names.
    # Values: A list of globs.
    # All the files that match package_data will be added to the MANIFEST
    # file if no template is provided:
    package_data={
        'harvesters': [
            os.path.join(
                'logging', '*.ini'
            ),
            os.path.join(
                'test', 'xml', '*.xml'
            ),
            os.path.join(
                'test', 'xml', '*.zip'
            ),
        ]
    },
    # A list of supported platforms:
    platforms='any',
    #
    provides=['harvesters'],
    # The URL for the website of the project:
    url='https://github.com/genicam/harvesters',
    # The package version:
    version=versioneer.get_version(),
)
