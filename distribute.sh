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
check=
test=
upload=

while getopts btu opt ; do
  case $opt in
  b)
    build=true ;;
  c)
    check=true ;;
  t)
    test=true ;;
  u)
    upload=true ;;
  \?)
    echo "Invalid option!"
    exit 1 ;;
  esac
done


# Build a distribution package.
if [ "x$build" = "xtrue" ]
then
  # Delete intermediate directories.
  for dir in build dist genicam.harvester.egg-info
  do
    if [ -e "$dir" ]
    then
      echo "Removing \"$dir\""
      rm -rf "$dir"
    fi
  done
  python3 setup.py sdist bdist_wheel
fi


# Check the distribution package:
if [ "x$check" = "xtrue" ]
then
  twine check dist/*
  # Return; do not execute upload:
  exit $?
else
fi


# Upload the distribution package.
if [ "x$upload" = "xtrue" ]
then
  url="https://upload.pypi.org/legacy/"
  if [ "x$test" = "xtrue" ]
  then
    url="https://test.pypi.org/legacy/"
  fi
  twine upload --repository-url $url dist/*
fi


exit $?

