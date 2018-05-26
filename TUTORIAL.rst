#########
Tutorials
#########

In this section, we will learn how to use Harvester GUI and Harvester Core.

.. contents:: Table of Contents

*************
Harvester GUI
*************

When you finished building the Python bindings, then you can launch Harvester. To launch Harvester Core or Harvester GUI, we would recommend you to do it on an IDE called PyCharm. You can download the community version of PyCharm for free at the following URL:

    https://www.jetbrains.com/pycharm/download

After installing PyCharm, open the Harvester package, that you have downloaded from GitHub, from PyCharm.

[IMPORTANT] By default, PyCharm doesn't know where the Python Bings are located. You can tell PyCharm the location in the Preference dialog. You should be able to find the right place just searching from the top-left corner. Then clicking ``Add Content Root`` button in the top-right corner and specify the directory.

.. image:: image/readme/project_structure.png
    :align: center
    :alt: Project Structure
    :scale: 40 %

In the Project Structure page, please add content root where the Python Bindings are located. In general, you should point at the following directory:

    genicam_root/bin/[target dependent]

Having that information, PyCharm can find out those modules which Harvester asks Python to import.

After that, you're ready to launch Harvester GUI (not only Harvester Core). To launch Harvester GUI, selecting ``harvester.py`` in the project pane, then right click it. There you should be able to find ``Run harvester`` in the popped up menu. Just click it. Harvester GUI should pop up.

.. image:: image/readme/run_harvester.png
    :align: center
    :alt: Loaded TLSimu
    :scale: 40 %

Now it is the time to select a GenTL Producer to load. In the toolbar, clicking the left most button, select a CTI file to load. Then a file selection dialog should pop up. In the following example, we chose a GenTL Producer simulator so-called TLSimu.

.. image:: image/readme/loaded_tlsimu.png
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

.. image:: image/icon/open_file.png
    :align: left
    :alt: Open file
    :scale: 40 %

This button is used to select a GenTL Producer file to load. The shortcut key is ``Ctrl+o``.

--------------------------
Updating GenTL information
--------------------------

.. image:: image/icon/update.png
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

.. image:: image/icon/connect.png
    :align: left
    :alt: Connect
    :scale: 40 %

This button is used to connect a device which is being selected by the former combo box. The shortcut key is ``Ctrl+c``. Once you connect the device, the device is exclusively controlled.

--------------------------------------------------
Disconnecting the connecting device from Harvester
--------------------------------------------------

.. image:: image/icon/disconnect.png
    :align: left
    :alt: Disconnect
    :scale: 40 %

This button is used to disconnect the connecting device from Harvester. The shortcut key is ``Ctrl+d``.

--------------------------
Starting image acquisition
--------------------------

.. image:: image/icon/start_acquisition.png
    :align: left
    :alt: Start image acquisition
    :scale: 40 %

This button is used to start image acquisition. The shortcut key is ``Ctrl+j``. The acquired images will be drawing in the following canvas pane.

---------------------
Pausing image drawing
---------------------

.. image:: image/icon/pause.png
    :align: left
    :alt: Pause
    :scale: 40 %

This button is used to temporarily stop drawing images on the canvas pane while it's keep acquiring images in the background. The shortcut key is ``Ctrl+k``. If you want to resume drawing images, just click the button again. You can do the same thing with the start image acquisition button (``Ctrl+j``).

--------------------------
Stopping image acquisition
--------------------------

.. image:: image/icon/stop_acquisition.png
    :align: left
    :alt: Stop image acquisition
    :scale: 40 %

This button is used to stop image acquisition. The shortcut key is ``Ctrl+l``.

-----------------------------------
Showing the device attribute dialog
-----------------------------------

.. image:: image/icon/device_attribute.png
    :align: left
    :alt: Device attribute
    :scale: 40 %

This button is used to show the device attribute dialog. The shortcut key is ``Ctrl+a``. The device attribute dialog offers you to a way to intuitively control device attribute over a GUI.

------------------------
Showing the about dialog
------------------------

.. image:: image/icon/about.png
    :align: left
    :alt: About
    :scale: 40 %

This button is used to show the about dialog.

**************
Harvester Core
**************

TODO: Finish writing article.

