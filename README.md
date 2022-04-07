# SSS Smart Mirror UI

## Setup guide

This project is targetted to raspberry pi 4. Make sure your device supports python3.9 and bluetooth(RFCOMM) before using this project.

First, make a clone of this project by using command below

    $ git clone https://github.com/bluelove8939/Smart-Mirror-IoT-Project-Mirror-UI.git

And run setup bash codes inside the project. This code installs all dependencies required.

    $ cd Smart-Mirror-IoT-Project-Mirror-UI
    $ bash raspberrypi-setup.sh

To enable sdptool, you need to add compatibility flag to the line starting with ExecStart of the file below.

    /lib/systemd/system/bluetooth.service 
        -> ExecStart=/usr/lib/bluetooth/bluetoothd -C

And then run the code below.

    $ sudo systemctl daemon-reload
    $ sudo systemctl restart bluetooth
    $ bash raspberrypi-bluetooth-setup.sh

Now your device is ready to run this project. Run main.py.

    $ python main.py


## Google Assistant Setup Guide

You can add Google Assistant to your smart mirror.
Make sure you already have your microphone and speaker attatched to raspberry pi4 before starting with this guide.

Prior to enable the Google Assistant, run "googlesample-assistant-pushtotalk" to make sure that you already installed 
Google Assistant SDK to your environment and generated your google OAuth2 credential file inside the appdir.
If there's a problem, see the website below and follow the instruction.

    https://developers.google.com/assistant/sdk/guides/service/python/

And then enable Google Assistant simply by editing config.json just like below:

    "google-assistant-enabled": false

There can be deprecated method inside Google Assistant SDK.
For example, 'array.array.tostring()' is deprecated in python3.9 (audio_helpers.py).
So you need to use another method 'array.array.tobytes()' to avoid the error.

The pushtotalk.py needs to be modified to use the code block below.
Modified pushtotalk.py is provided within this project.
Note that this modified pushtotalk.py is licenced by Google and cannot be used in commercial purpose.