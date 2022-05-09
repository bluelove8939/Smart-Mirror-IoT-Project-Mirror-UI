# SSS Smart Mirror UI

## Setup guide

This project is targetted to raspberry pi 4. Make sure your device supports python3.9 and bluetooth(RFCOMM) before using this project.

First, make a clone of this project by using command below

    $ git clone https://github.com/bluelove8939/Smart-Mirror-IoT-Project-Mirror-UI.git

And run setup bash codes inside the project. This code installs all the dependencies required.

    $ cd Smart-Mirror-IoT-Project-Mirror-UI
    $ bash raspberrypi-setup.sh

To enable sdptool, you need to add compatibility flag to the line starting with ExecStart of the file below.

    /lib/systemd/system/bluetooth.service 
        -> ExecStart=/usr/lib/bluetooth/bluetoothd -C

And then run the code below.

    $ sudo systemctl daemon-reload
    $ sudo systemctl restart bluetooth

You need some API keys to use this project.
These are the keys required.

    openweathermap
    google client file name
    google assistant client file name
    youtube api key
    azure face api key

Make 'assets/keys' directory to your repository and put your key and secret files to the directory.
And make 'apikeys.json' inside the directory with the given format below.

    {
        "openweathermap": "<your openweathermap key>",
        "googleclientfilename": "<your google client file name>",
        "googleassistantclientfilename": "<your google assistant client file name>",
        "youtubeapikey": "<your youtube api key>",
        "azureface": "<your azure face api key>",
        "azureface-endpoint": "<your azure face api endpoint>"
    }

Now your device is ready to run this project. Run 'main.py'.
Note that you need to run 'raspberrypi-bluetooth-setup.sh' prior to run the main code.
    
    $ bash raspberrypi-bluetooth-setup.sh
    $ python main.py


## Google Assistant Setup Guide

You can add Google Assistant to your smart mirror.
Make sure you already have your microphone and speaker attatched to raspberry pi4 before starting with this guide.

Prior to enable the Google Assistant, run "googlesample-assistant-pushtotalk" to make sure that you already installed 
Google Assistant SDK to your environment and generated your google OAuth2 credential file inside the appdir.
If there's any problem, see the website below and follow the instruction.

    https://developers.google.com/assistant/sdk/guides/service/python/

And then enable Google Assistant simply by editing config.json just like below:

    "google-assistant-enabled": true

There can be deprecated method inside Google Assistant SDK.
For example, 'array.array.tostring()' is deprecated in python3.9 (audio_helpers.py).
So you need to use another method 'array.array.tobytes()' to avoid the error.

The pushtotalk.py needs to be modified.
Modified pushtotalk.py is provided within this project.
Note that this modified pushtotalk.py is licenced by Google and cannot be used for commercial purpose.


## YouTube Music setup guide

You can add YouTube music player to your smart mirror.
Make sure you already have your speaker attatched to raspberry pi4 before starting with this guide.

Prior to enable the YouTube music player, you need to install VLC player to your raspberry pi from the website below.

    https://www.videolan.org/vlc/index.ko.html

And run the code below.

    $ bash raspberrypi-vlc-setup.sh

There can be deprecated method inside python vlc and pafy library.
For example, 'dislike_count' is no longer used in YouTube system.
So you need comment the line 54 of 'backend_youtube_dl.py' inside pafy library.
Run 'test/vlc_music_play_test.py' to check if there's no problem for running this project.

    $ python ./test/vlc_music_play_test.py


## Face emotion detection setup guide

This feature is designed by codeveloper named 'freezinghands'.
Note that codes listed below are originally written and licensed by him:

    face_emotion_detection.py
    azure_api_wrapper.py

You can access to the github repository of original face emotion detection project by the link below:

    https://github.com/freezinghands/face-analysis-webcam

You need to run setup code before enabling this feature.
Run the code below:

    $ bash raspberrypi-face-setup.sh

And then check whether all of the packages are installed properly.
Note that the recent version of opencv may not campatible with some specific version of numpy.
Make sure that your device has a compatible version of numpy.
Also you this feature requires webcam to take picture of user's face.
Before enabling this feature, you need to install webcam or raspberry pi camera module.
If you already checked your device works fine, enable this feature simply by editing config.json just like below:

    "face-emotion-detection-enabled": true


## Skin moisture measuring feature setup guide

This feature is designed by codeveloper named 'kimBoeGeun'.
Note that codes listed below are originally written and licensed by him:

    moisture_driver.py
    hardware_manger.py (MoistureManager)

You can access to the github repository of original face emotion detection project by the link below:

    https://github.com/kimBoeGeun/jongsul_KBG

Please follow the instruction from the repository above.
And run the code below to install all depencies required.

    bash raspberrypi-skin-setup.sh

Make sure that you already have your sensor attached to the device.
If you followed all the instruction above, then enable this feature by editing config.json.

    "skin-condition-enabled": true


## Style recommendation feature setup guide

This feature is designed by codeveloper named 'kimBoeGeun' and 'freezinghands'.
Note that codes listed below are originally written and licensed by him:

    data_manager.py (SkinRecommendationManager)
    reverse_image_api-wrapper.py

Make sure that you already have your webcam attached to the device.
Run setup code before enabling this feature.

    bash raspberrypi-style-recom-setup.sh

After running the code above, make AWS credential file to shared directory by running the code below.

    aws configure

Check there's a file named 'credentials' inside the directory '~/pi/.aws/'
If you followed all the instruction above, then enable this feature by editing config.json.

    "style-recommendation-enabled": true