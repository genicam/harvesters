##########
Installing
##########

In this section, we will learn how to instruct procedures to get Harvester work.

.. contents:: Table of Contents

********
Overview
********

In short, you may think which tools are required to get Harvester work. The answer is listed as follows:

    * The GenApi-Python Binding
    * The GenTL-Python Binding
    * The GenICam reference implementation.
    * A certified GenTL Producer
    * A GenICam compliant machine vision camera

The first three items will be able to downloaded from the EMVA website in the future. Regarding the 4th item, you should be able to get proprietary product from software vendors who sell image acquisition library. Regarding the 5th item, you should be able to purchase from machine vision camera manufactures all over the world.

******************************
Installing an official release
******************************

**NOTE: This way is not available as of May 2018. Thank you for your patience!**

The Harvester project is planning to support distribution via PyPI but it's not done yet. If once we supported it, you should be able to install Harvester invoking the following command:

.. code-block:: shell

    $ pip install genicam.harvester

**********************
Installing from source
**********************

In the meantime, the only way to use Harvester is cloning the Harvester package from the GitHub invoking the following command:

.. code-block:: shell

    $ git clone https://github.com/genicam/harvester.git

Harvester requires some Python modules. To install the required modules, please invoke the following command:

.. code-block:: shell

    $ pip install numpy PyQt5 vispy

If you're running Anaconda Python, then you can do the same with the following command:

.. code-block:: shell

    $ conda install numpy pyqt vispy

After that, you'll have to build the Python bindings by yourself; once they're officially released everything should be okay just downloading a distribution package.

The source code can be downloaded from the following URL using Subversion:

    https://genicam.mvtec.com/svn/genicam/branches/_dev_teli_kazunari_1881_20180121/

To build the library, please read the README file which is located at the following directory in the source package:

    source/Bindings/README.rst


