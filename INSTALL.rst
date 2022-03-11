.. figure:: https://user-images.githubusercontent.com/8652625/157880841-adf8a717-b2b0-47af-a5cc-171a7df31fcc.jpg
    :align: center
    :alt: The Battle between Carnival and Lent

    Pieter Bruegel the Elder, The Battle between Carnival and Lent, 1559

----

Installation
############

In this section, we will learn how to install Harvester and prerequiresites.

.. contents:: Table of Contents
    :depth: 2

----

System Requirements
-------------------

The supported CPython versions are defined by the ``genicam`` package. If the target CPython is not supported by the ``genicam`` package then Harvester will not be available.

Concerning the compiler compatibility, please note that we don't supported Cygwin GCC on Windows. This restriction is coming from a fact that the GenICam reference implementation has not supported it.

In addition, you will need the following items:

* GenTL Producers
* GenICam compliant machine vision cameras/devices

Installing Python
-----------------

First, let's install Python. There are several options for you but I would like to introduce you Anaconda here; I say this again, Anaconda is just an option and we bring it up here just for our convenience!

You can download Anaconda from the following URL:

https://www.anaconda.com/download/

For Windows, please find a 64-Bit graphical installer that fits your machine and download it. The installation process is straightforward but it could be a bad idea to add the Anaconda Python executable directory to the ``PATH`` environment variable because it means your system begins to use your Anaconda Python instead of the system Python that had been already installed before you installed Anaconda Python.

To not letting Anaconda Python interfere in your system Python, not adding Anaconda Python to the ``PATH`` and you should always launch ``Anaconda Prompt`` in the ``Anaconda3 (64-bit)`` folder from the Windows's start menu. It will automatically kick up the Anaconda Python so that you can immediately use the functionality that Anaconda provides you.

On Linux machines, you can make it with the following steps. First, please type the following command. Invoking that command, you will be able to use the ``conda`` command which allows you to activate an environment; note that the following code has been modified for my setup on a macOS machine:

.. code-block:: shell

    $ echo ". /Users/kznr/anaconda3/etc/profile.d/conda.sh" >> ~/.bash_profile

Then activate the root environment:

.. code-block:: shell

    $ conda activate

Now you can start working for installing Harvester.

Creating an Environment
-----------------------

After installing a Python, let's create an isolated environment where does not interfere in your system. An environment is very helpful for developers because everything will be okay just deleting the environment if you completely corrupted it by accident. Please imagine a case where you corrupt the system-wide Python. It's obviously a nightmare and it will enforce you to spend some days to recover it so it is very recommended to work in an isolated environment when you need to develop something.

Assume we have added the Anaconda Python executable directory to the ``PATH`` environment variable. To create an environment on a UNIX system, please type the following command; we name the environment ``genicam``:

.. code-block:: shell

    $ conda create -n genicam python=3.6

We have created an environment ``genicam`` with Python ``3.6``. If you prefer to install another version, just change the version number above.

After that, we activate the environment to work with Harvester. To activate the environment, type the following command:

.. code-block:: shell

    $ conda activate genicam

If it works well then you will be able to find ``genicam`` in the shell prompt as follows:

.. code-block:: shell

    (genicam) kznr@Kazunaris-MacBook:~%

Then let's check the version number of Python. To check the version number of Python, type the following command:

.. code-block:: shell

    $ python --version

You should be able to see the expected version number in its return as follows:

.. code-block:: shell

    Python 3.6.5 :: Anaconda, Inc.

Next, it is not necessary but install IPython; it is a convenient place
anytime when you want to give it a try; note that we executed ``conda
install`` instead of ``python -m pip install`` because we want to avoid using
the IPython in the system Python by mistake:

.. code-block:: shell

    $ conda install ipython

And then, install Harvester, too:

.. code-block:: shell

    $ python -m install harvesters

Finally, to deactivate the environment, type the following command:

.. code-block:: shell

    $ conda deactivate

Installing a GenTL Producer
---------------------------

Now we install a GenTL Producer that works with Harvester. Harvester can't acquire images without it.

Today, many camera manufacturers and software vendors all over the world provide GenTL Producers to support image acquisition using GenICam compliant cameras. However, you should note that some GenTL Producers may block cameras from other competitors. Though it's perfectly legal but we recommend you here to use a GenTL Producer from MATRIX VISION as a one of reliable GenTL Producer for this tutorial because it doesn't block cameras from other competitors. However, please respect their license and give them feedback immediately if you find something to be reported or something that you appreciate. As an open source activity, we would like to pay our best respect to their attitude and their products.

You can get their SDK from the following URL; please download the latest version of ``mvIMPACT_Acquire`` and install it; note that it has been renamed to ``mvGenTL_Acquire`` since 2.30:

http://static.matrix-vision.com/mvIMPACT_Acquire/

Once you installed their SDK, you can find the appropriate GenTL Producer just grepping ``*.cti``. Note that Harvester supports only 64-bit version of GenTL Producers as of November 2018.

This is just for your information but you can find the list of other reliable GenTL Producers `here <https://github.com/genicam/harvesters/wiki#gentl-producers>`_.

Installing Harvester
--------------------

Before installing Harvester, let's make sure that you are working in the environment that you created in `the previous chapter <https://github.com/genicam/harvesters#id18>`_.

After that, you can install Harvester via PyPI invoking the following command; note that the package name is ``harvesters`` but not ``harvester``; unfortunately, the latter word had been reserved by another project:

.. code-block:: shell

    $ pip install harvesters

For people who those have already installed it:

.. code-block:: shell

    $ pip install --upgrade harvesters

Or more simply:

.. code-block:: shell

    $ pip install -U harvesters

Perhaps ``pip`` could install cached package. If you want to install the newly dowloaded package, you should invoke the following command:

.. code-block:: shell

    $ pip install -U --no-cache-dir harvesters

These commands will automatically install the required modules such as ``numpy`` or ``genicam`` (the Python Binding for the GenICam GenApi & the GenTL Producers) if the module has not yet installed on your environment.

Getting back to the original topic, you could install the latest development version it using ``setup.py`` cloning Harvester from GitHub:

.. code-block:: shell

    $ git clone https://github.com/genicam/harvesters.git && cd harvesters && python setup.py install

