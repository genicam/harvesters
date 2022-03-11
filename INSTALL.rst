###############
Getting Started
###############

In this section, we will learn how to instruct procedures to get Harvester working.

***********
Terminology
***********

Before start talking about the detail, let's take a look at some important terminologies that frequently appear in this document. These terminologies are listed as follows:

* *The GenApi-Python Binding*: A Python module that communicates with the GenICam GenApi reference implementation.

* *A GenTL Producer*: A library that has C interface and offers consumers a way to communicate with cameras over physical transport layer dependent technology hiding the detail from the consumer.

* *The GenTL-Python Binding*: A Python module that communicates with GenTL Producers.

* *Harvester*: An image acquisition engine.

* *Harvester GUI*: A Harvester-based graphical user interface.

* *A GenICam compliant device*: It's typically a camera. Just involving the GenICam reference implementation, it offers consumers a way to dynamically configure/control the target remote devices.

The following diagram shows the hierarchy and relationship of the relevant modules:

.. figure:: https://user-images.githubusercontent.com/8652625/155761972-c131d638-a0cc-4c51-aa3b-752d8f3d1284.svg
    :align: center
    :alt: Module hierarchy

*******************
System Requirements
*******************

The supported CPython versions are defined by the ``genicam`` package. If the target CPython is not supported by the ``genicam`` package then Harvester will not be available.

Concerning the compiler compatibility, please note that we don't supported Cygwin GCC on Windows. This restriction is coming from a fact that the GenICam reference implementation has not supported it.

In addition, you will need the following items:

* GenTL Producers
* GenICam compliant machine vision cameras/devices

*****************
Installing Python
*****************

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

***********************
Creating an Environment
***********************

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

It's so easy.

***************************
Installing a GenTL Producer
***************************

Now we install a GenTL Producer that works with Harvester. Harvester can't acquire images without it.

Today, many camera manufacturers and software vendors all over the world provide GenTL Producers to support image acquisition using GenICam compliant cameras. However, you should note that some GenTL Producers may block cameras from other competitors. Though it's perfectly legal but we recommend you here to use a GenTL Producer from MATRIX VISION as a one of reliable GenTL Producer for this tutorial because it doesn't block cameras from other competitors. However, please respect their license and give them feedback immediately if you find something to be reported or something that you appreciate. As an open source activity, we would like to pay our best respect to their attitude and their products.

You can get their SDK from the following URL; please download the latest version of ``mvIMPACT_Acquire`` and install it; note that it has been renamed to ``mvGenTL_Acquire`` since 2.30:

http://static.matrix-vision.com/mvIMPACT_Acquire/

Once you installed their SDK, you can find the appropriate GenTL Producer just grepping ``*.cti``. Note that Harvester supports only 64-bit version of GenTL Producers as of November 2018.

This is just for your information but you can find the list of other reliable GenTL Producers `here <https://github.com/genicam/harvesters/wiki#gentl-producers>`_.

********************
Installing Harvester
********************

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

######################
Working with Harvester
######################

Harvester is an image acquisition engine. No GUI. You can use it as an image acquisition library which acquires images from GenTL Producers through the GenTL-Python Binding and controls the target remote device (it's typically a camera) through the GenApi-Python Binding.

Harvester works as a minimalistic front-end for image acquisition. Just importing it from your Python script, you should immediately be able to set images on your table.

You'll be able to download the these language binding runtime libraries from the `EMVA website <https://www.emva.org/standards-technology/genicam/genicam-downloads/>`_, however, it's not available as of May 2018, because they have not officially released yet. Fortunately they are in the final reviewing process so hopefully they'll be released by the end of 2018.

If you don't have to care about the display rate for visualizing acquired images, the combination of Harvester and `Matplotlib <https://matplotlib.org>`_ might be a realistic option for that purpose.

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

Note that you can add **one or more CTI files** on a single Harvester object. To add another CTI file, just repeat calling ``add_file`` method passing another target CTI file:

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

First, you should know that Harvester returns you an image as a 1D NumPy array.

.. code-block:: python

    buffer = ia.fetch_buffer()
    _1d = buffer.payload.components[0].data

Perhaps you may expect to have it as a 2D array but Harvester doesn't in reality because if Harvester provides an image as a specific shape, then it could limit your algorithm that you can apply to get the image that fits to your expected shape. Instead, Harvester provides you an image as a 1D array and also provides you required information that you would need while you're reshaping the original array to another.

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
