#########################
Harvester's Documentation
#########################

----

*Even though we just wanted to research image processing algorithms, why did we have to change our image acquisition library every time we change the camera that we use for the research?
- Anonymous*

----

.. contents:: Table of Contents
    :depth: 1

***************
About Harvester
***************

Harvester was created to be a public and friendly image acquisition library for all people who those want to learn computer/machine vision. Technically speaking, Harvester is a Python library which is responsible for the following tasks:

* Image acquisition
* Device manipulation
* Image data visualization (optional)

Harvester consumes image acquisition libraries, so-called GenTL Producers. If you have an officially certified GenTL Producer and GenICam compliant machine vision cameras, then Harvester supply you the acquired image data as `numpy <http://www.numpy.org>`_ array to make your image processing task productive.

You can freely use, modify, distribute Harvester under `Apache License-2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_ without worrying about the use of your software: personal, internal or commercial.

Currently, Harvester is being developed and maintained by the motivated volunteer contributors from all over the world.

***************************
Why is it called Harvester?
***************************

Harvester's name was derived from the great Flemish painter, Pieter Bruegel the Elder's painting so-called "The Harvesters". Harvesters harvest a crop every season that has been fully grown and the harvested crop is passed to the consumers. On the other hand, image acquisition libraries acquire images as their crop and the images are passed to the following processes. We found the similarity between them and decided to name our library Harvester.

Apart from anything else, we love its peaceful and friendly name. We hope you also like it ;-)

.. figure:: https://user-images.githubusercontent.com/8652625/40595190-1e16e90e-626e-11e8-9dc7-207d691c6d6d.jpg
    :align: center
    :alt: The Harvesters
    :scale: 55 %

    Pieter Bruegel the Elder, The Harvesters, 1565, (c) 2000–2018 The Metropolitan Museum of Art

****************
Asking questions
****************

We have prepared a chat room in Gitter. Please don't hesitate to drop your message when you get a question regarding Harvester!

https://gitter.im/genicam-harvester/chatroom

**************
External links
**************

* `GitHub <https://github.com/genicam/harvesters>`_: This is the main repository of Harvester
* `PyPI <https://pypi.org/project/harvesters/>`_: This is the package distribution page of Harvester which is located in PyPI
* `Read the Docs <https://harvesters.readthedocs.io/en/latest/>`_: You can find the API reference of Harvester Core and Harvester GUI

*****************
Table of Contents
*****************

.. toctree::
  :maxdepth: 2

  reference/index

