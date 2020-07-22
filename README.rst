.. figure:: https://user-images.githubusercontent.com/8652625/40595190-1e16e90e-626e-11e8-9dc7-207d691c6d6d.jpg
    :align: center
    :alt: The Harvesters

    Pieter Bruegel the Elder, The Harvesters, 1565, (c) The Metropolitan Museum of Art

.. image:: https://readthedocs.org/projects/harvesters/badge/?version=latest
    :target: https://harvesters.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/pypi/v/harvesters.svg
    :target: https://pypi.org/project/harvesters

.. image:: https://zenodo.org/badge/133908095.svg
   :target: https://zenodo.org/badge/latestdoi/133908095

----

############
Introduction
############

Hello everyone. I'm Kazunari, the author of Harvester and a technical contributor to GenICam.

Since I opened the source code of Harvester in May 2018, so many people tried out that and gave me very positive feedback that improves Harvester. The number of feedback and the number of people who I discussed with was much more than I expected what I had in the beginning and it truly was one of the exciting experiences I ever had in my professional career.

The original motivation that drove me to develop Harvester was like this: Until I got the idea of Harvester, I had to learn and adapt to popular proprietary 3rd party image acquisition/processing libraries from scratch every time even though I just wanted to acquire an image. To be honest, I had felt it's a bit annoying. A straightforward solution to the issue was to have a unified image acquisition library. In addition, as a guy who likes to work with Python, I wanted to make it a Python module to boost productivity.

I believe that Harvester can help you to concentrate on image processing that you really have to be responsible for. Of course, you would have to implement the algorithm again using other sophisticated and powerful proprietary libraries to optimize the performance in reality. However, (this is very important so let me stress this) Harvester is just a productive sandbox that encapsulates the image acquisition process and does not intend to take the place of such superior image processing libraries because they were designed for exactly that purpose. Harvester just wants to shorten the time you spend to realize your brilliant ideas as much as possible. With this meaning, Harvester can be considered as a tool that helps you to quickly iterate the prototyping process. Note that it is vital for designers because the prototyping process defines the basic quality of the final product. Fortunately, Harvester has got firm support from the high-quality GenTL Producers on the market. It means you can smoothly start working with any GenICam compliant cameras that you may want to work with.

So, everyone, there's no worry anymore. Keep having fun working. Harvester has got your back.

Greetings, Kazunari Kudo.

**************************
Harvester as Python Module
**************************

Techincally speaking, Harvester consists of two Python modules, Harvester Core and Harvester GUI, and technically speaking, each library is responsible for the following tasks:

- Harvester Core: Image acquisition & remote device manipulation
- Harvester GUI: Image data visualization

Harvester consumes image acquisition libraries, so-called GenTL Producers. Just grabbing a GenTL Producer and GenICam compliant machine vision cameras, then Harvester will supply you the acquired image data as `numpy <http://www.numpy.org>`_ array to make your image processing task productive.

You can freely use, modify, distribute Harvester under `Apache License-2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_ without worrying about the use of your software: personal, internal or commercial.

Currently, Harvester is being developed by the motivated contributors from all over the world.

***********************
Where Is The Name From?
***********************

Harvester's name is from the great Flemish painter, Pieter Bruegel the Elder's painting so-called "The Harvesters". You can see the painting in the top of this page. Harvesters harvest a crop every season that has been fully grown and the harvested crop is passed to the consumers. On the other hand, image acquisition libraries acquire images as their crop and the images are passed to the following processes. We found the similarity between them and decided to name our library Harvester.

Apart from anything else, we love its peaceful and friendly name.

----

.. contents:: Table of Contents
    :depth: 2

**Disclaimer**: All external pictures should have associated credits. If there are missing credits, please tell us, we will correct it. Similarly, all excerpts should be sourced. If not, this is an error and we will correct it as soon as you tell us.

----

******************
Development Status
******************

The Harvester project has started since April 2018 and it's still under development as of October 2018 but many developers and researchers over the world have already confirmed that it is actually usable with the popular GenTL Producers and GenICam compliant cameras from the following companies. We have realized the progress had been brought by all interested people's positive expectation in the machine vision market and we strongly believe it will sustain to the following years. Of course, we will never forget the importance of volunteer companies which provided us their products to test Harvester. Thank you very much!

Note that we as the committee have not prepared any formal certification procedure for Harvester. The following results were presented by Harvester users who confirmed Harvester worked for their use cases. It is true that the following information does not cover whole domain but as a fact it is helpful sometimes at least.

.. list-table::
    :header-rows: 1
    :align: center

    - - Company Name
      - GenTL Producer for CoaXPress
      - GenTL Producer for GigE Vision
      - GenTL Producer for USB3 Vision
      - GenICam compliant cameras
    - - `Active Silicon <https://www.activesilicon.com/>`_
      - Worked
      - Not applicable
      - Not applicable
      - Not applicable
    - - `Adimec <https://www.adimec.com/>`_
      - Not applicable
      - Not applicable
      - Not applicable
      - Worked
    - - `Allied Vision <https://www.alliedvision.com/en/digital-industrial-camera-solutions.html>`_
      - Not tested
      - Not tested
      - Not tested
      - Worked
    - - `Automation Technology <https://www.automationtechnology.de/cms/en/>`_
      - Not applicable
      - Not applicable
      - Not applicable
      - Worked
    - - `Basler <https://www.baslerweb.com/>`_
      - Not applicable
      - Not applicable
      - Worked
      - Worked
    - - `Baumer Optronic <https://www.baumer.com/se/en/>`_
      - Not applicable
      - Worked
      - Worked
      - Worked
    - - `CREVIS <http://www.crevis.co.kr/eng/main/main.php>`_
      - Not applicable
      - Not tested
      - Not applicable
      - Worked
    - - `CRITICAL LINK <https://www.criticallink.com>`_
      - Not applicable
      - Not applicable
      - Worked
      - Worked
    - - `DAHENG VISION <http://en.daheng-image.com/main.html>`_
      - Not applicable
      - Worked
      - Worked
      - Worked
    - - `Euresys <https://www.euresys.com/Homepage>`_
      - Worked
      - Not tested
      - Not tested
      - Not applicable
    - - `FLIR <https://www.flir.com>`_
      - Not applicable
      - Not applicable
      - Not applicable
      - Worked
    - - `Gardasoft <http://www.gardasoft.com>`_
      - Not applicable
      - Not applicable
      - Not applicable
      - Worked
    - - `JAI <https://www.jai.com>`_
      - Not tested
      - Worked
      - Worked
      - Worked
    - - `The IMAGING SOURCE <https://www.theimagingsource.com/>`_
      - Not tested
      - Not tested
      - Not tested
      - Worked
    - - `Lucid Vision Labs <https://thinklucid.com>`_
      - Not applicable
      - Worked
      - Not applicable
      - Worked
    - - `MACNICA Inc. <https://www.macnica.co.jp/en/top>`_
      - Not tested
      - Not tested
      - Worked
      - Worked
    - - `MATRIX VISION GmbH <https://www.matrix-vision.com/home-en.html>`_
      - Not applicable
      - Worked
      - Worked
      - Worked
    - - `Matrox Imaging <https://matrox.com/en/>`_
      - Worked
      - Not applicable
      - Not applicable
      - Not applicable
    - - `OMRON SENTECH <https://sentech.co.jp/en/>`_
      - Not tested
      - Not tested
      - Worked
      - Worked
    - - `PCO <https://www.pco-imaging.com/>`_
      - Not applicable
      - Not applicable
      - Not applicable
      - Not tested
    - - `Roboception <https://roboception.com/en/>`_
      - Not applicable
      - Not applicable
      - Not applicable
      - Worked
    - - `SICK <https://www.sick.com/ag/en/>`_
      - Not applicable
      - Worked
      - Not applicable
      - Worked
    - - `Silicon Software <https://silicon.software/>`_
      - Not tested
      - Not tested
      - Not tested
      - Not applicable
    - - `STEMMER IMAGING <https://www.stemmer-imaging.com/en/>`_
      - Not tested
      - Worked
      - Worked
      - Not applicable
    - - `Teledyne DALSA <http://www.teledynedalsa.com/en/products/imaging/cameras/>`_
      - Not tested
      - Not applicable
      - Not applicable
      - Worked
    - - `Vieworks <http://www.vieworks.com/eng/main.html>`_
      - Not tested
      - Not applicable
      - Not applicable
      - Not tested
    - - `XIMEA <https://www.ximea.com/>`_
      - Not tested
      - Not tested
      - Not tested
      - Not tested

Please don't hesitate to tell us if you have tested Harvester with your GenTL Producer or GenICam compliant device. We will add your company/organization name to the list.

***********
Need a GUI?
***********

Would you like to have a GUI? Harvester has a sister project that is called **Harvester GUI**. Oops, there's no punch line on its name! Please take a look its source repository if you are interested in it:

https://github.com/genicam/harvesters_gui

.. image:: https://user-images.githubusercontent.com/8652625/43035346-c84fe404-8d28-11e8-815f-2df66cbbc6d0.png
    :align: center
    :alt: Image data visualizer

*************
Announcements
*************

- **Version 1.2.8**: Resolves issue `#191 <https://github.com/genicam/harvesters/issues/191>`_.
- **Version 1.2.7**: Resolves issues `#167 <https://github.com/genicam/harvesters/issues/167>`_, `#181 <https://github.com/genicam/harvesters/issues/181>`_, `#183 <https://github.com/genicam/harvesters/issues/183>`_, `#184 <https://github.com/genicam/harvesters/issues/184>`_, `#185 <https://github.com/genicam/harvesters/issues/185>`_, and `#188 <https://github.com/genicam/harvesters/issues/188>`_.
- **Version 1.2.6**: Reverted the change made for version 1.2.5.
- **Version 1.2.5**: Resolves issue `#180 <https://github.com/genicam/harvesters/issues/180>`_.
- **Version 1.2.4**: Resolves issues `#125 <https://github.com/genicam/harvesters/issues/125>`_, `#169 <https://github.com/genicam/harvesters/issues/169>`_, `#172 <https://github.com/genicam/harvesters/issues/172>`_, `#175 <https://github.com/genicam/harvesters/issues/175>`_, and `#178 <https://github.com/genicam/harvesters/issues/178>`_.
- **Version 1.2.3**: Resolves issue `#165 <https://github.com/genicam/harvesters/issues/165>`_.
- **Version 1.2.2**: Resolves issue `#146 <https://github.com/genicam/harvesters/issues/146>`_; please let me know if it breaks something on your side. I will revert the change as soon as possible.
- **Version 1.2.1**: Resolves issues `#145 <https://github.com/genicam/harvesters/issues/145>`_, `#155 <https://github.com/genicam/harvesters/issues/155>`_, `#157 <https://github.com/genicam/harvesters/issues/157>`_, and `#159 <https://github.com/genicam/harvesters/issues/159>`_.
- **Version 1.2.0**: Resolves issues `#127 <https://github.com/genicam/harvesters/issues/127>`_, `#131 <https://github.com/genicam/harvesters/issues/131>`_, `#141 <https://github.com/genicam/harvesters/issues/141>`_, and `#142 <https://github.com/genicam/harvesters/issues/142>`_. The fix for ticket #131 improves the performance of both stability and capable acquisition rate of the image acquisition.
- **Version 1.1.1**: Resolves issue `#126 <https://github.com/genicam/harvesters/issues/126>`_.
- **Version 1.1.0**: Resolves issue `#120 <https://github.com/genicam/harvesters/issues/120>`_.
- **Version 1.0.5**: Resolves issue `#124 <https://github.com/genicam/harvesters/issues/124>`_.
- **Version 1.0.4**: Partly resolves issue `#121 <https://github.com/genicam/harvesters/issues/121>`_.

Other older releases should be found at `Milestones page <https://github.com/genicam/harvesters/milestones>`_ on GitHub.

################
Online Resources
################

****************
Asking Questions
****************

We have prepared an FAQ page. Perhaps your issue could be resolved just reading through it:

https://github.com/genicam/harvesters/wiki/FAQ

If any article was not mentioning about the issue you are facing, please try to visit the following page and check if there's a ticket that is relevant to the issue. If nothing has been mentioned yet, feel free to create an issue ticket so that we can support you:

https://github.com/genicam/harvesters/issues

***************
Important Links
***************

.. list-table::

    - - Documentation
      - https://harvesters.readthedocs.io/en/latest/
    - - Digital Object Identifier
      - https://zenodo.org/record/3554804#.Xd4HSi2B01I
    - - EMVA website
      - https://www.emva.org/standards-technology/genicam/genicam-downloads/
    - - Harvester GUI
      - https://github.com/genicam/harvesters_gui
    - - Issue tracker
      - https://github.com/genicam/harvesters/issues
    - - PyPI
      - https://pypi.org/project/harvesters/
    - - Source repository
      - https://github.com/genicam/harvesters

***************
GenTL Producers
***************

As of today, we have tested Harvester with the following GenTL Producers and it definitely is the shortest way to get one from the following list to get Harvester working with tangible machine vision cameras:

.. list-table::
    :header-rows: 1
    :align: center

    - - Company Name
      - SDK Name
      - Camera Manufacturer Free
    - - Basler AG
      - `Pylon <https://www.baslerweb.com/en/products/software/basler-pylon-camera-software-suite/>`_
      - No
    - - Baumer Optronic
      - `Baumer GAPI SDK <https://www.baumer.com/ae/en/product-overview/image-processing-identification/software/baumer-gapi-sdk/c/14174>`_
      - Yes for GEV and No for U3V
    - - DAHENG VISION
      - `MER Galaxy View <http://en.daheng-image.com/products_list/&pmcId=a1dda1e7-5d40-4538-9572-f4234be49c9c.html>`_
      - No
    - - JAI
      - `JAI SDK <https://www.jai.com/support-software/jai-software>`_
      - Yes
    - - MATRIX VISION GmbH
      - `mvIMPACT Acquire <http://static.matrix-vision.com/mvIMPACT_Acquire/>`_
      - Yes
    - - OMRON SENTECH
      - `SentechSDK <https://sentech.co.jp/en/data/>`_
      - No
    - - STEMMER IMAGING
      - `Common Vision Blox <https://www.commonvisionblox.com/en/cvb-download/>`_
      - Yes

You might be able to directly download one at their website but please note that perhaps some of them could require you to register your information to get one. In addition, some GenTL Producers might block you to connect other competitors' cameras.

###########
Terminology
###########

Before start talking about the detail, let's take a look at some important terminologies that frequently appear in this document. These terminologies are listed as follows:

* **The GenApi-Python Binding**: A Python module that communicates with the GenICam reference implementation.

* **A GenTL Producer**: A library that has C interface and offers consumers a way to communicate with cameras over physical transport layer dependent technology hiding the detail from the consumer.

* **The GenTL-Python Binding**: A Python module that communicates with GenTL Producers.

* **Harvester**: A Python module that consists of Harvester Core and Harvester GUI.

* **Harvester Core**: A part of Harvester that works as an image acquisition engine.

* **Harvester GUI**: A part of Harvester that works as a graphical user interface of Harvester Core.

* **A GenICam compliant device**: It's typically a camera. Just involving the GenICam reference implementation, it offers consumers a way to dynamically configure/control the target remote devices.

The following diagram shows the hierarchy and relationship of the relevant modules:

.. figure:: https://user-images.githubusercontent.com/8652625/48105146-a3b0e700-e279-11e8-8a3f-f94372aeff37.png
    :align: center
    :alt: Module hierarchy

###############
Getting Started
###############

In this section, we will learn how to instruct procedures to get Harvester work.

*******************
System Requirements
*******************

The following software modules are required to get Harvester working:

* Either of Python 3.4, 3.5, 3.6, or 3.7 (**Only 64bit versions** are supported as of October 2018.)

In addition, please note that we don't supported Cygwin on Windows. This restriction is coming from a fact that the GenICam reference implementation has not supported it.

In addition, you will need the following items to let Harvester make something meaningful:

* GenTL Producers
* GenICam compliant machine vision cameras

Harvester has been confirmed it works with the following 64-bit operating systems:

* Fedora 27
* macOS 10.13
* Red Hat Enterprise Linux Workstation 7.4
* Ubuntu 14.04
* Windows 7
* Windows 10

Note that it's just a snapshot at a moment. If you are curious to know the reality, just make a try because Harvester is for free!

*****************
Installing Python
*****************

First, let's install Python. There are several options for you but I would like to introduce you Anaconda here. You can download Anaconda from the following URL:

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
=======================

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

Finally, to deactivate the environment, type the following command:

.. code-block:: shell

    $ conda deactivate

It's so easy.

***************************
Installing a GenTL Producer
***************************

Now we install a GenTL Producer that works with Harvester. Harvester can't acquire images without it.

Today, many camera manufacturers and software vendors all over the world provide GenTL Producers to support image acquisition using GenICam compliant cameras. However, you should note that some GenTL Producers may block cameras from other competitors. Though it's perfectly legal but we recommend you here to use a GenTL Producer from MATRIX VISION as a one of reliable GenTL Producer for this tutorial because it doesn't block cameras from other competitors. However, please respect their license and give them feedback immediately if you find something to be reported or something that you appreciate. As an open source activity, we would like to pay our best respect to their attitude and their products.

You can get their SDK from the following URL; please download ``mvIMPACT_Acquire`` and install it.

http://static.matrix-vision.com/mvIMPACT_Acquire/2.29.0/

Once you installed their SDK, you can find the appropriate GenTL Producer just grepping ``*.cti``. Note that Harvester supports only 64-bit version of GenTL Producers as of November 2018.

This is just for your information but you can find the list of other reliable GenTL Producers `here <https://github.com/genicam/harvesters#gentl-producers>`_.

*************************
Installing Harvester Core
*************************

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

These commands will automatically install the required modules such as ``numpy`` or ``genicam2`` (the Python Binding for the GenICam GenApi & the GenTL Producers) if the module has not yet installed on your environment.

Getting back to the original topic, you could install the latest development version it using ``setup.py`` cloning Harvester from GitHub:

.. code-block:: shell

    $ git clone https://github.com/genicam/harvesters.git && cd harvesters && python setup.py install

#######################
Working with Harveseter
#######################

Harvester Core is an image acquisition engine. No GUI. You can use it as an image acquisition library which acquires images from GenTL Producers through the GenTL-Python Binding and controls the target remote device (it's typically a camera) through the GenApi-Python Binding.

Harvester Core works as a minimalistic front-end for image acquisition. Just importing it from your Python script, you should immediately be able to set images on your table.

You'll be able to download the these language binding runtime libraries from the `EMVA website <https://www.emva.org/standards-technology/genicam/genicam-downloads/>`_, however, it's not available as of May 2018, because they have not officially released yet. Fortunately they are in the final reviewing process so hopefully they'll be released by the end of 2018.

If you don't have to care about the display rate for visualizing acquired images, the combination of Harvester Core and `Matplotlib <https://matplotlib.org>`_ might be a realistic option for that purpose.

*********************************
Tasks Harvester Core Does for You
*********************************

The main features of Harvester Core are listed as follows:

* Image acquisition through GenTL Producers
* Multiple loading of GenTL Producers in a single Python script
* GenICam feature node manipulation of the target remote device

Note that the second item implies you can involve multiple types of transport layers in your Python script. Each transport layer has own advantages and disadvantages and you should choose appropriate transport layers following your application's requirement. You just need to acquire images for some purposes and the GenTL Producers deliver the images somehow. It truly is the great benefit of the GenTL Standard! And of course, not only GenTL Producers but Harvester Core offer you a way to manipulate multiple remote devices in a single Python script with an intuitive manner.

On the other hand, Harvester Core could be considered as a simplified version of the GenTL-Python Binding; actually, Harvester Core hides it in its back and shows only intuitive interfaces to its clients. Harvester Core just offers you a relationship between you and a remote device. Nothing more. We say it again, just you and a remote device. If you need to manipulate more relevant GenTL modules or have to achieve something over a hardcore way, then you should directly work with the GenTL-Python Binding.

*************************
Harvester Core on IPython
*************************

The following code block shows Harvester Core is running on IPython. An acquired image is delivered as the payload of a buffer and the buffer can be fetched by calling the ``fetch_buffer`` method of the ``ImageAcquirer`` class. Once you get an image you should be able to immediately start image processing. If you're running on the Jupyter notebook, you should be able to visualize the image data using Matplotlib. This step should be helpful to check what's going on your trial in the image processing flow.

.. code-block:: python

    (genicam) kznr@Kazunaris-MacBook:~% ipython
    Python 3.6.6 |Anaconda, Inc.| (default, Jun 28 2018, 11:07:29)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 6.5.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: from harvesters.core import Harvester

    In [2]: import numpy as np  # This is just for a demonstration.

    In [3]: h = Harvester()

    In [4]: h.add_file('/Users/kznr/dev/genicam/bin/Maci64_x64/TLSimu.cti')

    In [5]: h.update()

    In [6]: len(h.device_info_list)
    Out[6]: 4

    In [7]: h.device_info_list[0]
    Out[7]: (id_='TLSimuMono', vendor='EMVA_D', model='TLSimuMono', tl_type='Custom', user_defined_name='Center', serial_number='SN_InterfaceA_0', version='1.2.3')

    In [8]: ia = h.create_image_acquirer(0)

    In [9]: ia.remote_device.node_map.Width.value = 8

    In [10]: ia.remote_device.node_map.Height.value = 8

    In [11]: ia.remote_device.node_map.PixelFormat.value = 'Mono8'

    In [12]: ia.start_acquisition()

    In [13]: with ia.fetch_buffer() as buffer:
        ...:     # Let's create an alias of the 2D image component:
        ...:     component = buffer.payload.components[0]
        ...:
        ...:     # Note that the number of components can be vary. If your
        ...:     # target remote device transmits a multi-part information, then
        ...:     # you'd get two or more components in the payload. However, now
        ...:     # we're working with a remote device that transmits only a 2D image.
        ...:     # So we manipulate only index 0 of the list object, components.
        ...:
        ...:     # Let's see the acquired data in 1D:
        ...:     _1d = component.data
        ...:     print('1D: {0}'.format(_1d))
        ...:
        ...:     # Reshape the NumPy array into a 2D array:
        ...:     _2d = component.data.reshape(
        ...:         component.height, component.width
        ...:     )
        ...:     print('2D: {0}'.format(_2d))
        ...:
        ...:     # Here are some trivial calculations:
        ...:     print(
        ...:         'AVE: {0}, MIN: {1}, MAX: {2}'.format(
        ...:             np.average(_2d), _2d.min(), _2d.max()
        ...:         )
        ...:     )
        ...:
    1D: [123 124 125 126 127 128 129 130 124 125 126 127 128 129 130 131 125 126
     127 128 129 130 131 132 126 127 128 129 130 131 132 133 127 128 129 130
     131 132 133 134 128 129 130 131 132 133 134 135 129 130 131 132 133 134
     135 136 130 131 132 133 134 135 136 137]
    2D: [[123 124 125 126 127 128 129 130]
     [124 125 126 127 128 129 130 131]
     [125 126 127 128 129 130 131 132]
     [126 127 128 129 130 131 132 133]
     [127 128 129 130 131 132 133 134]
     [128 129 130 131 132 133 134 135]
     [129 130 131 132 133 134 135 136]
     [130 131 132 133 134 135 136 137]]
    AVE: 130.0, MIN: 123, MAX: 137

    In [14]: ia.stop_acquisition()

    In [15]: ia.destroy()

    In [16]: h.reset()

    In [17]: quit
    (genicam) kznr@Kazunaris-MacBook:~%

######################
The Harvester Workflow
######################

****************
Acquiring Images
****************

First, let's import Harvester:

.. code-block:: python

    from harvesters.core import Harvester

Then instantiate a Harvester object; we're going to use ``h`` that stands for
Harvester as its identifier.

.. code-block:: python

    h = Harvester()

And load a CTI file; loading a CTI file, you can communicate with the GenTL
Producer:

.. code-block:: python

    # ATTENTION! Please use the CTI file in the original location!

    # Why? Visit https://github.com/genicam/harvesters/wiki/FAQ and
    # read "I pointed out a CTI file but Harvester says the image doesn't
    # exist (Part 2)."

    h.add_file('path/to/gentl_producer.cti')

Note that you can add **one or more CTI files** on a single Harvester Core object. To add another CTI file, just repeat calling ``add_file`` method passing another target CTI file:

.. code-block:: python

    h.add_file('path/to/another_gentl_producer.cti')

And the following code will let you know the CTI files that have been loaded
on the Harvester object:

.. code-block:: python

    h.files

In a contrary sense, you can remove a specific CTI file that you have added with the following code:

.. code-block:: python

    h.remove_file('path/to/gentl_producer.cti')

And now you have to update the list of remote devices; it fills up your device
information list and you'll select a remote device to control from the list:

.. code-block:: python

    h.update()

The following code will let you know the remote devices that you can control:

.. code-block:: python

    h.device_info_list

Our friendly GenTL Producer, so called TLSimu, gives you the following information:

.. code-block:: python

    [(unique_id='TLSimuMono', vendor='EMVA_D', model='TLSimuMono', tl_type='Custom', user_defined_name='Center', serial_number='SN_InterfaceA_0', version='1.2.3'),
     (unique_id='TLSimuColor', vendor='EMVA_D', model='TLSimuColor', tl_type='Custom', user_defined_name='Center', serial_number='SN_InterfaceA_1', version='1.2.3'),
     (unique_id='TLSimuMono', vendor='EMVA_D', model='TLSimuMono', tl_type='Custom', user_defined_name='Center', serial_number='SN_InterfaceB_0', version='1.2.3'),
     (unique_id='TLSimuColor', vendor='EMVA_D', model='TLSimuColor', tl_type='Custom', user_defined_name='Center', serial_number='SN_InterfaceB_1', version='1.2.3')]

And you create an image acquirer object specifying a target remote device. The image acquirer does the image acquisition task for you. In the following example it's trying to create an acquirer object of the first candidate remote device in the device information list:

.. code-block:: python

    ia = h.create_image_acquirer(0)

Or equivalently:

.. code-block:: python

    ia = h.create_image_acquirer(list_index=0)

You can connect the same remote device passing more unique information to the method. In the following case, we specify a serial number of the target remote device:

.. code-block:: python

    ia = h.create_image_acquirer(serial_number='SN_InterfaceA_0')

You can specify a target remote device using properties that are provided through the ``device_info_list`` property of the ``Harvester`` class object. Note that it is invalid if the specifiers gives you two ore more remote devices. Please specify sufficient information so that the combination gives you a unique target remote device.

We named the image acquirer object ``ia`` in the above example but in a practical occasion, you may give it a purpose oriented name like ``ia_face_detection``. Note that a camera itself does NOT acquirer/receive images but it just transmits them. In a machine vision application, there should be two roles at least: One transmits images and the other acquires them. The ``ImageAcquirer`` class objects play the latter role and it holds a camera as the ``remote_device`` object, the source of images.

Anyway, then now we start image acquisition:

.. code-block:: python

    ia.start_acquisition()

Once you started image acquisition, you should definitely want to get an image. Images are delivered to the acquirer allocated buffers. To fetch a buffer that has been filled up with an image, you can have 2 options; the first option is to use the ``with`` statement:

.. code-block:: python

    with ia.fetch_buffer() as buffer:
        # Work with the Buffer object. It consists of everything you need.
        print(buffer)
        # The buffer will automatically be queued.

Having that code, the fetched buffer is automatically queued once the code step out from the scope of the ``with`` statement. It's prevents you to forget queueing it by accident. The other option is to manually queue the fetched buffer by yourself:

.. code-block:: python

    buffer = ia.fetch_buffer()
    print(buffer)
    # Don't forget to queue the buffer.
    buffer.queue()

In this option, again, please do not forget that you have to queue the buffer by yourself. If you forget queueing it, then you'll lose a buffer that could be used for image acquisition. Everything is up to your design, so please choose an appropriate way for you. In addition, once you queued the buffer, the Buffer object will be obsolete. There's nothing to do with it.

Okay, then you would stop image acquisition with the following code:

.. code-block:: python

    ia.stop_acquisition()

And the following code disconnects the connecting remote device from the image acquirer; you'll have to create an image acquirer object again when you have to work with a remote device:

.. code-block:: python

    ia.destroy()

If you finished working with the ``Harvester`` object, then release the acquired resources calling the ``reset`` method:

.. code-block:: python

    h.reset()

Now you can quit the program! Please not that ``Harvester`` and ``ImageAcquirer`` also support the ``with`` statement. So you may write program as follows:

.. code-block:: python

    with Harvester() as h:
        with h.create_image_acquirer(0) as ia:
            # Work, work, and work with the ia object.
            # The ia object will automatically call the destroy method
            # once it goes out of the block.

        # The h object will automatically call the reset method
        # once it goes out of the block.

This way prevents you forget to release the acquired external resources. If this notation doesn't block your use case then you should rely on the ``with`` statement.

***********************************
Reshaping a NumPy Array as an Image
***********************************

We have learned how to acquire images from a target remote device through an ``ImageAcquirer`` class object. In this section, we will learn how to reshape the acquired image into another that can be used by your application.

First, you should know that Harvester Core returns you an image as a 1D NumPy array.

.. code-block:: python

    buffer = ia.fetch_buffer()
    _1d = buffer.payload.components[0].data

Perhaps you may expect to have it as a 2D array but Harvester Core doesn't in reality because if Harvester Core provides an image as a specific shape, then it could limit your algorithm that you can apply to get the image that fits to your expected shape. Instead, Harvester Core provides you an image as a 1D array and also provides you required information that you would need while you're reshaping the original array to another.

The following code is an except from Harvester GUI that reshapes the source 1D array to another to draw it on the VisPy canvas. VisPy canvas takes ``content`` as an image to draw:

.. code-block:: python

    from harvesters.util.pfnc import mono_location_formats, \
        rgb_formats, bgr_formats, \
        rgba_formats, bgra_formats

    payload = buffer.payload
    component = payload.components[0]
    width = component.width
    height = component.height
    data_format = component.data_format

    # Reshape the image so that it can be drawn on the VisPy canvas:
    if data_format in mono_location_formats:
        content = component.data.reshape(height, width)
    else:
        # The image requires you to reshape it to draw it on the
        # canvas:
        if data_format in rgb_formats or \
                data_format in rgba_formats or \
                data_format in bgr_formats or \
                data_format in bgra_formats:
            #
            content = component.data.reshape(
                height, width,
                int(component.num_components_per_pixel)  # Set of R, G, B, and Alpha
            )
            #
            if data_format in bgr_formats:
                # Swap every R and B:
                content = content[:, :, ::-1]
        else:
            return

Note that ``component.num_components_per_pixel`` returns a ``float`` so please don't forget to cast it when you pass it to the ``reshape`` method of NumPy array. If you try to set a ``float`` then the method will refuse it.

It's not always but sometimes you may have to handle image formats that require you to newly create another image calculating each pixel component value referring to the pixel location. To help such calculation, ``Component2DImage`` class provides the ``represent_pixel_location`` method to tell you the 2D pixel location that corresponds to the pixel format. The pixel location is defined by Pixel Format Naming Convention, PFNC in short. The array that is returned by the method is a 2D NumPy array and it corresponds to the model that is defined by PFNC.

.. code-block:: python

    pixel_location = component.represent_pixel_location()

The 2D array you get from the method is equivalent to the definition that is given by PFNC. The following screenshot is an excerpt from the PFNC 2.1:

.. image:: https://user-images.githubusercontent.com/8652625/47624017-dad91700-db5a-11e8-9f87-6f383c0c6627.png
    :align: center
    :alt: The definition of the pixel location of LMN422 formats

For example, if you acquired a YCbCr422_8 format image, then the first and the second rows of ``pixel_location`` would look as follows; ``L`` is used to denote the 1st component, ``M`` is for the 2nd, and ``N`` is for the 3rd, and they correspond to ``Y``, ``Cb``, and ``Cr`` respectively; in the following description, for a given pixel, the first index represents the row number and the second index represents the column number and note that the following index notation is based on one but not zero though you will use the zero based notation in your Python script:

.. code-block:: python

    [Y11, Cb11, Y12, Cr11, Y13, Cb13, Y14, Cr13, ...]
    [Y21, Cb21, Y22, Cr21, Y23, Cb23, Y24, Cr23, ...]

Having that pixel location, you should be able to convert the color space of each row from YCbCr to RGB.

.. code-block:: python

    import numpy as np
    # Create the output array that has been filled up with zeros.
    rgb_2d = np.zeros(shape=(height, width, 3), dtype='uint8')
    # Calculate each pixel component using pixel_location.
    # Calculation block follows:
    #     ...

For example, if you have an 8 bits YCbCr709 image, then you can get the RGB values of the first pixel calculating the following formula:

.. image:: https://user-images.githubusercontent.com/8652625/47624981-298bae80-db65-11e8-8f78-53b188f22f53.png
    :align: center
    :alt: \begin{align*} R_{11} &= 1.16438 (Y_{11} - 16) &                           & + 1.79274 (Cr_{11} - 128) \\G_{11} &= 1.16438 (Y_{11} - 16) & - 0.21325 (Cb_{11} - 128) & - 0.53291 (Cr_{11} - 128) \\B_{11} &= 1.16438 (Y_{11} - 16) & - 0.21240 (Cb_{11} - 128) \\\end{align*}

Similarly, you can get the RGB values of the second pixel calculating the following formula:

.. image:: https://user-images.githubusercontent.com/8652625/47625009-6657a580-db65-11e8-900d-f84f70e055a5.png
    :align: center
    :alt: \begin{align*} R_{12} &= 1.16438 (Y_{12} - 16) &                           & + 1.79274 (Cr_{11} - 128) \\G_{12} &= 1.16438 (Y_{12} - 16) & - 0.21325 (Cb_{11} - 128) & - 0.53291 (Cr_{11} - 128) \\B_{11} &= 1.16438 (Y_{11} - 16) & - 0.21240 (Cb_{11} - 128) \\\end{align*}

Once you finished filling up each pixel with a set of RGB values, then you'll be able to handle it as a RGB image but not a YCbCr image.

You can download the standard document of PFNC at the `EMVA website <https://www.emva.org/standards-technology/genicam/genicam-downloads/>`_.

**********************************
Manipulating GenICam Feature Nodes
**********************************

Probably almost of the Harvester users would be interested in manipulating GenIcam feature nodes through Harvester. Let's assume that we are going to control a GenICam feature node called ``Foo``.

To get the value of ``Foo``, we code as follows:

.. code-block:: python

    a = ia.remote_device.node_map.Foo.value

On the other hand, if ``Foo`` is an Integer node then we code as follows to set a value:

.. code-block:: python

    ia.remote_device.node_map.Foo.value = 42

If ``Foo`` is a Boolean node, then you code as follows:

.. code-block:: python

    ia.remote_device.node_map.Foo.value = True

Or if ``Foo`` is an Enumeration node, then you code as follows; it also works for a case where Foo is a String node:

.. code-block:: python

    ia.remote_device.node_map.Foo.value = 'Bar'

If ``Foo`` is a Command node, then you can execute the command with the following

.. code-block:: python

    ia.remote_device.node_map.Foo.execute()

There you can dive much more deeper in the GenICam GenApi but the description above would be sufficient for a general use.

Ah, one more thing. You may want to know the available GenICam feature nodes in the target remote physical device. In such a case, you can probe them calling the ``dir`` function as follows:

.. code-block:: python

    dir(ia.remote_device.node_map)

You should be able to find (probably) familiar feature names in the output.

########
Appendix
########

*********************
Open Source Resources
*********************

Harvester Core uses the following open source libraries/resources:

* Pympler

  | License: `Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0.html>`_
  | Copyright (c) Jean Brouwers, Ludwig Haehne, Robert Schuppenies

  | https://pythonhosted.org/Pympler/
  | https://github.com/pympler/pympler
  | https://pypi.org/project/Pympler/

* Versioneer

  | License: `The Creative Commons "Public Domain Dedication" license  (CC0-1.0) <https://creativecommons.org/publicdomain/zero/1.0/>`_
  | Copyright (c) 2018 Brian Warner

  | https://github.com/warner/python-versioneer

***************
Acknowledgement
***************

The initial idea about Harvester suddenly came up to a software engineer, Kazunari Kudo's head in the early April of year 2018 and he immediately decided to bring the first prototype to the International Vision Standards Meeting, IVSM in short, that was going to be held in Frankfurt am Main in the following early May. During the Frankfurt IVSM, interested engineers tried out Harvester and confirmed it really worked using commercial machine vision cameras provided by well-known machine vision camera manufacturers in the world. Having that fact, the attendees of the IVSM warmly welcomed Harvester.

The following individuals have directly or indirectly contributed to the development activity of Harvester or encouraged the developers by their thoughtful warm words; they are our respectable wonderful colleagues:

Rod Barman, Stefan Battmer, David Beek, Jan Becvar, David Bernecker, Chris Beynon, Eric Bourbonnais, Benedikt Busch, George Chamberlain, Thomas Detjen, Friedrich Dierks, Dana Diezemann, Emile Dodin, Reynold Dodson, Sascha Dorenbeck, Jozsa Elod, Erik Eloff, Katie Ensign, Andreas Ertl, James Falconer, Werner Feith, Maciej Gara, Andreas Gau, Sebastien Gendreau, Francois Gobeil, Werner Goeman, Jean-Paul Goglio, Markus Grebing, Eric Gross, Ioannis Hadjicharalambous, Uwe Hagmaier, Tim Handschack, Christopher Hartmann, Reinhard Heister, Gerhard Helfrich, Jochem Herrmann, Heiko Hirschmueller, Tom Hopfner, David Hoese, Karsten Ingeman Christensen, Severi Jaaskelainen, Mattias Johannesson, Mark Jones, Mattias Josefsson, Martin Kersting, Stephan Kieneke, Tom Kirchner, Lutz Koschorreck, Frank Krehl, Maarten Kuijk, Max Larin, Ralf Lay, Min Liu, Sergey Loginonvskikh, Thomas Lueck, Alain Marchand, Rocco Matano, Masahide Matsubara, Stephane Maurice, Robert McCurrach, Mike Miethig, Thies Moeller, Roman Moie, Katsura Muramatsu, Marcel Naggatz, Hartmut Nebelung, Damian Nesbitt, Quang Nhan Nguyen, Klaus-Henning Noffz, Neerav Patel, Jan Pech, Merlin Plock, Joerg Preckwinkel, Benjamin Pussacq, Dave Reaves, Thomas Reuter, Gordon Rice, Andreas Rittinger, Ryan Robe, Nicolas P. Rougier, Felix Ruess, Matthias Schaffland, Michael Schmidt, Jan Scholze, Martin Schwarzbauer, Rupert Stelz, Madhura Suresh, Chendra Hadi Suryanto, Andrew Wei Chuen Tan, Timo Teifel, Albert Theuwissen, Laval Tremblay, Tim Vlaar, Silvio Voitzsch, Stefan Von Weihe, Frederik Voncken, Roman Wagner, Ansger Waschki, Anne Wendel, Michael Williamson, Jean-Michel Wintgens, Manfred Wuetschner, Jang Xu, Christoph Zierl, Sebastian Yap, and Juraj Zopp

******************************
Column: Seeing and Recognition
******************************

The following is a short column that was written by one of my favorite photographers/philosophers, Katsura Muramatsu. Even though the column was exclusively dedicated to her exhibition called "Natura naturans", she generously allowed me to excerpt the column for this Harvester project. It would give us an opportunity to thinking about seeing and recognition we regularly do. To me, at least, they sound like a habit on which we unconsciously premise when we do machine vision: We tend to see everything in a way that we want to interpret. Of course, I would like to take the fact in a positive way though.

*"When we talk to someone, we implicitly or explicitly try to find a piece of evidence in his/her eyes that he/she is alive. The same situation happens in a case where we face a stuffed animal and the face, or especially the eyes play a much more important role rather than its fur or other parts. When people visit this place, the museum where I took photos of these stuffed animals, they would feel that they are seen by the animals rather than they see the animals even though the animals are not alive anymore. In fact, the eyes of the stuffed animals are made of glass or other materials such as plastic. I frequently ask myself why we felt that we were seen through their eyes made of those materials." - Katsura Muramatsu*

.. figure:: https://user-images.githubusercontent.com/8652625/65650928-c261cd00-e047-11e9-9ce3-972461c3e15d.jpg
    :align: center
    :alt: Ordo: Eastern Wolf

    Title: "Ordo: Eastern Wolf" (2018)
    
    © Katsura Muramatsu All Rights Reserved

    http://hellerraum.nobody.jp
