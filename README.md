# SSS Smart Mirror UI

## Setup guide

This project is targetted to raspberry pi 4. Make sure you device supports python and bluetooth(RFCOMM) before using this project.

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