#########
Harvester
#########

Harvester is a friendly companion for people who those want to learn computer vision.

The Harvester project develops an open source Python library that consumes the GenTL Standard based image acquisition libraries, so-called GenTL Producers. If you have an officially certified GenTL Producer and GenICam compliant machine vision cameras, Harvester offers you high-performance image acquisition from the cameras and visualization of the acquired images on all major platforms. In addition, it offers you interface for numpy to make image processing easier and productive.

Currently, Harvester is Apache-2.0 licensed and it has been developed and maintained by the volunteer contributors all over the world.

.. figure:: https://user-images.githubusercontent.com/8652625/40595190-1e16e90e-626e-11e8-9dc7-207d691c6d6d.jpg
    :align: center
    :alt: The Harvesters
    :scale: 55 %

    Pieter Bruegel the Elder, The Harvesters, 1565, oil on wood, © 2000–2018 The Metropolitan Museum of Art

.. contents:: Table of Contents


################
Asking questions
################

We have prepared a chat room in Gitter. Please don't hesitate to drop your message when you get a question regarding Harvester!

https://gitter.im/genicam-harvester/Lobby

###########
Terminology
###########

Before start talking about the detail, let's take a look at some important terminologies that frequently appear in this document. These terminologies are listed as follows:

* **The GenApi-Python Binding**: A Python module. It communicates with the GenICam reference implementation.
* **A GenTL Producer**: A C/C++ library. It offers consumers a way to communicate with cameras over physical transport layer dependent technology hiding the detail from the consumer.
* **The GenTL-Python Binding**: A Python module. It communicates with GenTL Producers.
* **Harvester**: A Python module that consists of Harvester Core and Harvester GUI.
* **Harvester Core**: A part of Harvester. It works as an image acquisition engine.
* **Harvester GUI**: A part of Harvester. It works as a graphical user interface of Harvester Core.
* **A GenICam compliant device**: It's typically a camera. Just involving the GenICam reference implementation, it offers consumers a way to dynamically configure/control the target devices.

################################
What would Harvester do for you?
################################

Harvester mainly consists of the following two Python modules:

* *Harvester Core*: An image acquisition engine, and
* *Harvester GUI*: Graphical user interface between users & Harvester Core.

In this section, we will learn what Harvester offers us through these components.

****************************************
Harvester Core (``harvester.Harvester``)
****************************************

Harvester Core is an image acquisition engine. No GUI. You can use it as an image acquisition library which acquires images from GenTL Producers through the GenTL-Python Binding and control the target device (it's typically a camera) through the GenApi-Python Binding.

Harvester Core works as a minimalistic front-end for image acquisition. Just importing it from your Python script, you should immediately be able to set images on your table.

You'll be able to download the these language binding runtime libraries from the `EMVA website <https://www.emva.org/standards-technology/genicam/genicam-downloads/>`_, however, it's not available as of May 2018, because they have not officially released yet. Fortunately they are in the final reviewing process so hopefully they'll be release by the end of 2018.

If you don't have to visualize acquired images at high frame rate, the combination of Harvester Core and `Matplotlib <https://matplotlib.org>`_ might be ideal for that purpose.

The main features of Harvester Core are listed as follows:

* Image acquisition over GenTL Producers
* Multiple loading of GenTL Producers in a single Python script
* GenICam node manipulation of the target device

Note that the second item implies you can involve multiple types of transport layers in your Python script. Each transport layer has own advantages and disadvantages and you should choose appropriate transport layers following your application's requirement. You just need to acquire images for some purposes and the GenTL Producers deliver the images somehow. It truly is the great benefit of encapsulation by the GenTL Standard!

On the other hand, Harvester Core could be considered as a simplified version of the GenTL-Python Binding; actually Harvester Core hides it in its back and shows only intuitive interfaces to its clients. Harvester Core just offers you a relationship between you and a device. Nothing more. We say it again, just you and a device. If you need to manipulate more relevant GenTL modules or have to achieve something over a hardcore way, then you should directly work with the GenTL-Python Binding.

******************************************
Harvester GUI (``harvester.HarvesterGUI``)
******************************************

Harvester GUI works on the top of Harvester Core and offers you high-performance data visualization on the fly. It involves VisPy for controlling OpenGL functionality and PyQt for providing GUI.

The main features of Harvester GUI are listed as follows:

* Data visualization of the acquired images
* Image magnification using a mouse wheel or a trackpad
* Image dragging using a mouse or a trackpad
* An arbitrary selection of image displaying point in the data path (Not implemented yet)

Unlike Harvester Core, Harvester GUI limits the number of GenTL Producers to load just one. This is just a limitation to not make the GUI complicated. In general, the user should know which GenTL Producer should be loaded to control his target device. It's not necessary to load multiple GenTL Producers for this use case. However, this is just an idea in an early stage. We might support multiple loading on even Harvester GUI in the future.

=======================
Supported pixel formats
=======================

Currently Harvester GUI supports the following pixel formats that are defined by the Pixel Format Naming Convention:

* ``Mono8``
* ``RGB8``
* ``BayerRG8``, ``BayerGR8``, ``BayerBG8``, and ``BayerGB8`` (No demosaicing supported)

***********
Screenshots
***********

In this section, we see some useful widgets which Harvester offers you.

The image visualizer widget (below) offers you a visualization of the acquired images. In this screenshot, Harvester is acquiring a 4000 x 3000 pixel of RGB8 Packed image at 30 fps; it means it's acquiring images at 8.6 Gbps. It's quite fast isn't it?

.. image:: https://user-images.githubusercontent.com/8652625/40595832-f16e21d4-6271-11e8-9a5c-1b8f18875239.png
    :align: center
    :alt: Image visualizer
    :scale: 40 %

The attribute controller widget (below) offers you to manipulate GenICam feature nodes of the target device. Changing exposure time, triggering the target device for image acquisition, storing a set of camera configuration so-called User Set, etc, you can manually control the target device anytime when you want to. It supports visibility filter feature and regular expression feature. These features are useful in a case where you need to display only the features you are interested.

.. image:: https://user-images.githubusercontent.com/8652625/40595924-94f16794-6272-11e8-9104-9cc57a92dad4.png
    :align: center
    :alt: Attribute Controller
    :scale: 40 %

The following screenshot shows Harvester Core is running on IPython. Harvester Core returns the latest image data at the moment as a Numpy array every time its user call the ``get_latest_image()`` method. Once you get an image you should be able to immediately start image processing. If you're running on Jupyter notebook, you should be able to visualize the data using Matplotlib. This step should be helpful to check what's going on your trial in the image processing flow.

.. image:: https://user-images.githubusercontent.com/8652625/40595908-7d9f17b2-6272-11e8-877f-6893cd88a828.png
    :align: center
    :alt: Harvester on IPython
    :scale: 40 %

############
Requirements
############

*******************
System requirements
*******************

* Python 3.4 or higher
* Officially certifiled GenTL Producers
* GenICam compliant machine vision cameras

***************************
Supported operating systems
***************************

* macOS
* Ubuntu
* Windows

##########
Installing
##########

In this section, we will learn how to instruct procedures to get Harvester work.

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

***********************************************************************************
THIS IS A TEMPORAL INSTRUCTION BUT PLEASE FOLLOW THIS WAY TO GET HARVESTER WORKING!
***********************************************************************************

We are still working in the development stage so people who those are want to get Harvester working have to prepare everything by themselves (sorry about that!). In this section, we will learn how to prepare required tools/libraries.

First, invoking the following command clone the Harvester from the GitHub :

.. code-block:: shell

    $ git clone https://github.com/genicam/harvester.git

Harvester requires some Python modules. To install the required modules, please invoke the following command; we're planning to isolate these modules from Harvester Core because these modules are relevant to visualization task but please install them anyway for now:

.. code-block:: shell

    $ pip install numpy PyQt5 vispy

If you're running Anaconda Python, then you can do the same with the following command:

.. code-block:: shell

    $ conda install numpy pyqt vispy

After that, you'll have to build the Python bindings by yourself. The source code can be downloaded from the following URL using Subversion:

.. code-block:: shell

    $ svn co --username your_account_name https://genicam.mvtec.com/svn/genicam/branches/_dev_teli_kazunari_1881_20180121/

To build the library, please read the ``README`` file which is located at the following directory in the source package:

``genicam/source/Bindings/README.rst``

Reading that file, you should be able to learn everything you need to build the Python Bindings by yourself.

Before closing this section, please remind that you need to be careful when you choose a Python version (especially Anaconda Python, maybe?) because some distributions have different directory structure or linking symbols. It simply breaks the Python Bindings. We have started collecting some results from our experiences and have listed them in the "System Configuration Matrix" section in the ``README`` file. We hope it helps you to save your time.

********************************************************************************************
Installing an official release (Under construction; please do not follow this way for now)
********************************************************************************************

**NOTE: This way is not available as of May 2018. Thank you for your patience!**

The Harvester project is planning to support distribution via PyPI but it's not done yet. If once we supported it, you should be able to install Harvester invoking the following command:

.. code-block:: shell

    $ pip install genicam.harvester

#########
Tutorials
#########

In this section, we will learn how to use Harvester GUI and Harvester Core.

*************
Harvester GUI
*************

When you finished building the Python bindings, then you can launch Harvester. To launch Harvester Core or Harvester GUI, we would recommend you to do it on an IDE called PyCharm. You can download the community version of PyCharm for free at the following URL:

https://www.jetbrains.com/pycharm/download

After installing PyCharm, open the Harvester package, that you have downloaded from GitHub, from PyCharm.

[IMPORTANT] By default, PyCharm doesn't know where the Python Bings are located. You can tell PyCharm the location in the Preference dialog. You should be able to find the right place just searching from the top-left corner. Then clicking ``Add Content Root`` button in the top-right corner and specify the directory.

.. image:: https://user-images.githubusercontent.com/8652625/40595910-7df63826-6272-11e8-807a-96c0fb4229d7.png
    :align: center
    :alt: Project Structure
    :scale: 40 %

In the Project Structure page, please add content root where the Python Bindings are located. In general, you should point at the following directory:

``genicam_root/bin/[target dependent]``

Having that information, PyCharm can find out those modules which Harvester asks Python to import.

After that, you're ready to launch Harvester GUI (not only Harvester Core). To launch Harvester GUI, selecting ``harvester.py`` in the project pane, then right click it. There you should be able to find ``Run harvester`` in the popped up menu. Just click it. Harvester GUI should pop up.

.. image:: https://user-images.githubusercontent.com/8652625/40595912-7e4e5178-6272-11e8-9033-1b9ee58e1fdb.png
    :align: center
    :alt: Loaded TLSimu
    :scale: 40 %

Now it is the time to select a GenTL Producer to load. In the toolbar, clicking the left most button, select a CTI file to load. Then a file selection dialog should pop up. In the following example, we chose a GenTL Producer simulator so-called TLSimu.

.. image:: https://user-images.githubusercontent.com/8652625/40595909-7dca3564-6272-11e8-8ace-1ac571562474.png
    :align: center
    :alt: Loaded TLSimu
    :scale: 40 %

=======
Toolbar
=======

Most of Harvester GUI's features can be used through its toolbox. In this section, we describe each button's functionality and how to use it. Regarding shortcut keys, replace ``Ctrl`` with ``Command`` on macOS.

--------------------
Selecting a CTI file
--------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596073-7e1b6a82-6273-11e8-9045-68bbbd034281.png
    :align: left
    :alt: Open file
    :scale: 40 %

This button is used to select a GenTL Producer file to load. The shortcut key is ``Ctrl+o``.

--------------------------
Updating GenTL information
--------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596091-9354283a-6273-11e8-8c6f-559db511339a.png
    :align: left
    :alt: Update
    :scale: 40 %

This button is used to update GenTL information of the GenTL Producer that you are loading on Harvester. The shortcut key is ``Ctrl+u``. It might be useful when you newly connect a device to your system.

------------------------------------
Selecting a GenICam compliant device
------------------------------------

This combo box shows a list of available GenICam compliant devices. You can select a device that you want to control.

-----------------------------------------
Connecting a selected device to Harvester
-----------------------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596045-49c61d54-6273-11e8-8424-d16e923b5b3f.png
    :align: left
    :alt: Connect
    :scale: 40 %

This button is used to connect a device which is being selected by the former combo box. The shortcut key is ``Ctrl+c``. Once you connect the device, the device is exclusively controlled.

--------------------------------------------------
Disconnecting the connecting device from Harvester
--------------------------------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596046-49f0fd9e-6273-11e8-83e3-7ba8aad3c4f7.png
    :align: left
    :alt: Disconnect
    :scale: 40 %

This button is used to disconnect the connecting device from Harvester. The shortcut key is ``Ctrl+d``.

--------------------------
Starting image acquisition
--------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596022-34d3d486-6273-11e8-92c3-2349be5fd98f.png
    :align: left
    :alt: Start image acquisition
    :scale: 40 %

This button is used to start image acquisition. The shortcut key is ``Ctrl+j``. The acquired images will be drawing in the following canvas pane.

---------------------
Pausing image drawing
---------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596063-6cae1aba-6273-11e8-9049-2430a042c671.png
    :align: left
    :alt: Pause
    :scale: 40 %

This button is used to temporarily stop drawing images on the canvas pane while it's keep acquiring images in the background. The shortcut key is ``Ctrl+k``. If you want to resume drawing images, just click the button again. You can do the same thing with the start image acquisition button (``Ctrl+j``).

--------------------------
Stopping image acquisition
--------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596024-35d84c86-6273-11e8-89b8-9368db740f22.png
    :align: left
    :alt: Stop image acquisition
    :scale: 40 %

This button is used to stop image acquisition. The shortcut key is ``Ctrl+l``.

-----------------------------------
Showing the device attribute dialog
-----------------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596224-7b2cf0e2-6274-11e8-9088-bb48163968d6.png
    :align: left
    :alt: Device attribute
    :scale: 40 %

This button is used to show the device attribute dialog. The shortcut key is ``Ctrl+a``. The device attribute dialog offers you to a way to intuitively control device attribute over a GUI.

------------------------
Showing the about dialog
------------------------

.. image:: https://user-images.githubusercontent.com/8652625/40596039-449ddc36-6273-11e8-9f91-1eb7830b8e8c.png
    :align: left
    :alt: About
    :scale: 40 %

This button is used to show the about dialog.

**************
Harvester Core
**************

TODO: Finish writing article.

################
Acknowledgements
################

Harvester GUI (but not Harvester Core) uses the following open source libraries/resources.

* VisPy (BSD)

    | Copyright (c) 2013-2018 VisPy developers
    | http://vispy.org/
        
* PyQt5 (GPL)

    | Copyright (c) 2018 Riverbank Computing Limited
    | https://www.riverbankcomputing.com/
        
* Icons8

    | Copyright (c) Icons8 LLC
    | https://icons8.com/

####################################
Why is the library called Harvester?
####################################

Harvester's name was derived from the great Flemish painter, Pieter Bruegel the Elder's painting so-called "The Harvesters". Harvesters harvest a crop every season that has been fully grown and the harvested crop is passed to the consumers. On the other hand, image acquisition libraries acquire images as their crop and the images are passed to the following processes. We found the similarity between them and decided to name our library Harvester.

Apart from anything else, we love its peaceful and friendly name. We hope you also like it ;-)

#######
Credits
#######

The initial idea about Harvester suddenly came up to Kazunari Kudo's head in the early April 2018 and he decided to bring the first prototype to the following International Vision Standards Meeting. During the Frankfurt International Vision Standards Meeting which was held in May 2018, people confirmed Harvester really worked using machine vision cameras provided by well-known machine vision camera manufacturers in the world. Having that fact, the attendees warmly welcomed Harvester.

The following individuals have directly or indirectly contributed to the development activity of Harvester or encouraged the developers by their thoughtful warm words:

    Rod Barman, Stefan Battmer, David Beek, David Bernecker, Chris Beynon, Eric Bourbonnais, George Chamberlain, Thomas Detjen, Friedrich Dierks, Dana Diezemann, Emile Dodin, Reynold Dodson, Sascha Dorenbeck, Erik Eloff, Katie Ensign, Andreas Ertl, James Falconer, Werner Feith, Maciej Gara, Andreas Gau, Sebastien Gendreau, Francois Gobiel, Werner Goeman, Jean-Paul Goglio, Markus Grebing, Eric Gross, Ioannis Hadjicharalambous, Uwe Hagmaier, Tim Handschack, Christopher Hartmann, Reinhard Heister, Gerhard Helfrich, Jochem Herrmann, Heiko Hirschmueller, Tom Hopfner, Karsten Ingeman Christensen, Mattias Johannesson, Mark Jones, Mattias Josefsson, Martin Kersting, Stephan Kieneke, Tom Kirchner, Lutz Koschorreck, Frank Krehl, Maarten Kuijk, Max Larin, Ralf Lay, Min Liu, Sergey Loginonvskikh, Thomas Lueck, Alain Marchand, Rocco Matano, Masahide Matsubara, Stephane Maurice, Robert McCurrach, Mike Miethig, Thies Moeller, Roman Moie, Marcel Naggatz, Hartmut Nebelung, Damian Nesbitt, Quang Nhan Nguyen, Klaus-Henning Noffz, Neerav Patel, Jan Pech, Merlin Plock, Joerg Preckwinkel, Benjamin Pussacq, Dave Reaves, Thomas Reuter, Andreas Rittinger, Ryan Robe, Nicolas P. Rougier, Matthias Schaffland, Michael Schmidt, Jan Scholze, Martin Schwarzbauer, Rupert Stelz, Madhura Suresh, Chendra Hadi Suryanto, Timo Teifel, Laval Tremblay, Tim Vlaar, Silvio Voitzsch, Stefan Von Weihe, Frederik Voncken, Roman Wagner, Ansger Waschki, Anne Wendel, Jean-Michel Wintgens, Manfred Wuetschner, Jang Xu, Christoph Zierl, and Juraj Zopp


