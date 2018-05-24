#########
Harvester
#########

Harvester is a friendly companion for people who those want to learn computer vision.

The Harvester project develops an open source Python library that consumes the GenTL Standard based image acquisition libraries, so-called GenTL Producers. If you have an officially certified GenTL Producer and GenICam compliant machine vision cameras, Harvester offers you high-performance image acquisition from the cameras and visualization of the acquired images on all major platforms. In addition, it offers you interface for numpy to make image processing easier and productive.

Currently, Harvester is MIT licensed and it has been developed and maintained by the volunteer contributors all over the world.

.. figure:: image/readme/harvesters.jpg
    :align: center
    :alt: The Harvesters
    :scale: 55 %

    Pieter Bruegel the Elder, The Harvesters, 1565, oil on wood, © 2000–2018 The Metropolitan Museum of Art

################################
What would harvester do for you?
################################

Harvester mainly consists of two Python modules, one is an image acquisition engine Harvester Core and the other is GUI, Harvester GUI. In this section, we learn what Harvester offer us.

**************
Harvester Core
**************

Harvester Core is an image acquisition engine. No GUI. It acquires images from GenTL Producers through the GenTL-Python Binding. You'll be able to download the GenTL-Python Binding runtime library from the EMVA website but it's not available as of May 25th, 2018, because it's not officially released.

Harvester Core also works with the GenApi-Python Binding and it will allow us to control GenICam feature nodes. If you don't need runtime image data visualization, just involve this Python module in your program. In this case, Matplotlib would be ideal for you to draw the acquired images.

The main features of Harvester Core are listed as follows:

* Image acquisition over GenTL Producers
* Multiple loading of GenTL Producers in a single Python script
* GenICam node manipulation of the target device

Note that the second item implies you can involve multiple types of transport layers in your Python script. It means you don't have to care anything about how the images are transmitted. Each transport layer has own advantages and disadvantages and you should choose appropriate transport layers following your application's requirement. You just need to acquire images for some purposes and the GenTL Producers deliver the images somehow. It truly is the great benefit of encapsulation by the GenTL Standard!

On the other hand, Harvester Core could be called a simplified version of the GenTL-Python Binding. It just offers you a relationship between you and a device. Nothing more. If you need to manipulate more relevant GenTL modules or go on a hardcore stuff, you should directly involve the GenTL-Python Binding.

*************
Harvester GUI
*************

Harvester GUI works on the top of Harvester Core and offers you high-performance data visualization on the fly. It involves VisPy for controlling OpenGL functionality and PyQt for providing GUI.

The main features of Harvester GUI are listed as follows:

* Data visualization of the acquired images
* Zooming-in/-out using mouse wheel or trackpad
* Image dragging using mouse or trackpad
* An arbitrary selection of image displaying point in the data path (Not implemented yet)

Unlike Harvester Core, Harvester GUI limits the number of GenTL Producers to load is just one. This is just a limitation to not make the GUI complicated. In general, the user should know which GenTL Producer should be loaded to control his target device. It's not necessary to load multiple GenTL Producers for this use case. However, this is just an idea in an early stage. We might support multiple loading on even Harvester GUI in the future.

Note that VisPy is BSD licensed but PyQt is GPL/Commercial licensed.

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
* Windows 7

###########
Screenshots
###########

In this section, we see some useful GUI which Harvester offers you.

The image visualizer widget (below) offers you visualization of the acquired images. In this screenshot, Harvester is acquiring a 4000 x 3000 pixel of RGB8 Packed image at 30 fps; it means it's acquiring images at 8.6 Gbps.

.. image:: image/readme/image_visualizer.png
    :align: center
    :alt: Image Visualizer
    :scale: 40 %

The attribute controller widget (below) offers you to manipulate GenICam feature nodes of the target device. Changing exposure time, triggering the target device for image acquisition, storing a set of camera configuration so-called User Set, etc, you can manually control the target device anytime when you want to.

.. image:: image/readme/attribute_controller.png
    :align: center
    :alt: Attribute Controller
    :scale: 40 %


The following screenshot shows Harvester Core is running on IPython. Harvester Core returns the latest image data at the moment as a Numpy array every time its user call the ``latest_image`` property. Once you get an image you should be able to immediately start image processing! If you're running on Jupyter notebook, you should be able to visualize the data using Matplotlib.

.. image:: image/readme/harvester_on_ipython.png
    :align: center
    :alt: Attribute Controller
    :scale: 40 %

####################################
Why is the library called Harvester?
####################################

Harvester's name was derived from the great Flemish painter, Pieter Bruegel the Elder's painting so-called "The Harvesters". Harvesters harvest a crop every season that has been fully grown and the harvested crop is passed to the consumers. On the other hand, image acquisition libraries acquire images as their crop and the images are passed to the following processes. We found the similarity between them and decided to name our library Harvester.

Apart from anything else, we love its peaceful and friendly name. We hope you also like it ;-)

############
Contributors
############

The initial idea about Harvester suddenly came up to Kazunari Kudo's head in the early April 2018 and he decided to bring the first prototype to the following International Vision Standards Meeting. During the Frankfurt International Vision Standards Meeting which was held in May 2018, people confirmed Harvester really worked using machine vision cameras provided by well-known machine vision camera manufacturers in the world. Having that fact, the attendees warmly welcomed Harvester.

The following individuals have directly or indirectly contributed to the development activity of Harvester or encouraged the developers by their thoughtful warm words:

    Rod Barman, Stefan Battmer, David Beek, David Bernecker, Chris Beynon, Eric Bourbonnais, George Chamberlain, Thomas Detjen, Friedrich Dierks, Dana Diezemann, Emile Dodin, Reynold Dodson, Sascha Dorenbeck, Erik Eloff, Katie Ensign, Andreas Ertl, James Falconer, Werner Feith, Maciej Gara, Andreas Gau, Sebastien Gendreau, Francois Gobiel, Werner Goeman, Jean-Paul Goglio, Markus Grebing, Eric Gross, Ioannis Hadjicharalambous, Uwe Hagmaier, Tim Handschack, Christopher Hartmann, Reinhard Heister, Gerhard Helfrich, Jochem Herrmann, Heiko Hirschmueller, Tom Hopfner, Karsten Ingeman Christensen, Mattias Johannesson, Mark Jones, Mattias Josefsson, Martin Kersting, Stephan Kieneke, Tom Kirchner, Lutz Koschorreck, Frank Krehl, Maarten Kuijk, Max Larin, Ralf Lay, Min Liu, Sergey Loginonvskikh, Thomas Lueck, Alain Marchand, Rocco Matano, Masahide Matsubara, Stephane Maurice, Robert McCurrach, Mike Miethig, Thies Moeller, Roman Moie, Marcel Naggatz, Hartmut Nebelung, Damian Nesbitt, Quang Nhan Nguyen, Klaus-Henning Noffz, Neerav Patel, Jan Pech, Merlin Plock, Joerg Preckwinkel, Benjamin Pussacq, Dave Reaves, Thomas Reuter, Andreas Rittinger, Ryan Robe, Nicolas P. Rougier, Matthias Schaffland, Michael Schmidt, Jan Scholze, Martin Schwarzbauer, Rupert Stelz, Madhura Suresh, Chendra Hadi Suryanto, Timo Teifel, Laval Tremblay, Tim Vlaar, Silvio Voitzsch, Stefan Von Weihe, Frederik Voncken, Roman Wagner, Ansger Waschki, Anne Wendel, Jean-Michel Wintgens, Manfred Wuetschner, Jang Xu, Christoph Zierl, and Juraj Zopp


