#########################
Harvester's Documentation
#########################

.. figure:: https://user-images.githubusercontent.com/8652625/40595190-1e16e90e-626e-11e8-9dc7-207d691c6d6d.jpg
    :align: center
    :alt: The Harvesters

    Pieter Bruegel the Elder, The Harvesters, 1565, (c) The Metropolitan Museum of Art

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

*****************
Table of Contents
*****************

.. toctree::
  :maxdepth: 2

  reference/harvester_core
