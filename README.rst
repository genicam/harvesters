#########
Harvester
#########

Harvester is a friendly companion for people who those want to learn computer vision.

The Harvester project develops an open source Python library that consumes the GenTL Standard based image acquisition libraries, so-called GenTL Producers. If you have an officially certified GenTL Producer and GenICam compliant machine vision cameras, Harvester offers you high-performance image acquisition from the cameras and visualization of the acquired images on all major platforms. In addition, it offers you interface for numpy to make image processing easier and productive.

Currently, Harvester is Apache-2.0 licensed and it has been developed and maintained by the volunteer contributors all over the world.

.. figure:: image/readme/harvesters.jpg
    :align: center
    :alt: The Harvesters
    :scale: 55 %

    Pieter Bruegel the Elder, The Harvesters, 1565, oil on wood, © 2000–2018 The Metropolitan Museum of Art

.. contents:: Table of Contents

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

* Mono8
* RGB8 and RGB8Packed
* BayerRG8, BayerGR8, BayerBG8, and BayerGB8
    | It displays them in the raw format. No demosaicing supported.

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

***********
Screenshots
***********

In this section, we see some useful widgets which Harvester offers you.

The image visualizer widget (below) offers you a visualization of the acquired images. In this screenshot, Harvester is acquiring a 4000 x 3000 pixel of RGB8 Packed image at 30 fps; it means it's acquiring images at 8.6 Gbps. It's quite fast isn't it?

.. image:: image/readme/image_visualizer.png
    :align: center
    :alt: Image visualizer
    :scale: 40 %

The attribute controller widget (below) offers you to manipulate GenICam feature nodes of the target device. Changing exposure time, triggering the target device for image acquisition, storing a set of camera configuration so-called User Set, etc, you can manually control the target device anytime when you want to. It supports visibility filter feature and regular expression feature. These features are useful in a case where you need to display only the features you are interested.

.. image:: image/readme/attribute_controller.png
    :align: center
    :alt: Attribute Controller
    :scale: 40 %

The following screenshot shows Harvester Core is running on IPython. Harvester Core returns the latest image data at the moment as a Numpy array every time its user call the ``get_latest_image()`` method. Once you get an image you should be able to immediately start image processing. If you're running on Jupyter notebook, you should be able to visualize the data using Matplotlib. This step should be helpful to check what's going on your trial in the image processing flow.

.. image:: image/readme/harvester_on_ipython.png
    :align: center
    :alt: Attribute Controller
    :scale: 40 %

############
Installation
############

For installation instructions and requirements, see the INSTALL.rst file.

####################
How to use Harvester
####################

For usage instructions, see the TUTORIAL.rst file.

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


