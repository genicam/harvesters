#!/bin/bash
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

# Prepare options.
build=
test=
upload=

while getopts btu opt ; do
  case $opt in
  b)
    build=true ;;
  t)
    test=true ;;
  u)
    upload=true ;;
  \?)
    echo "Invalid option!"
    exit 1 ;;
  esac
done

# Delete intermediate directories.
for dir in build dist genicam.harvester.egg-info
do
  if [ -e "$dir" ]
  then
    echo "Removing \"$dir\""
    rm -rf "$dir"
  fi
done

# BUild a distribution package.
if [ "x$build" = "xtrue" ]
then
  python3 setup.py sdist bdist_wheel
fi

url="https://upload.pypi.org/legacy/"
if [ "x$test" = "xtrue" ]
then
  url="https://test.pypi.org/legacy/"
fi

# Upload the distribution package.
if [ "x$upload" = "xtrue" ]
then
  twine upload --repository-url $url dist/*
fi

exit $?

