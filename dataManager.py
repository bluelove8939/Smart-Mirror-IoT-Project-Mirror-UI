import io
import os
import requests
import json
import pafy
import vlc
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

import bluetooth  # pybluez library


# Reading required apikeys
#
# Note:
#   API keys is at file named 'assets/keys/apikeys.txt'
#   Make your own CSV file for API keys or just manually generate the 'apikeys' dictionary
#
# Included Keys:
#   - openweathermap

apikeys = {}
apikeysDirectoryPath = os.path.join(os.path.curdir, 'assets', 'keys')

with open(os.path.join('assets', 'keys', 'apikeys.json'), 'rt') as keyFile:
    readApiKeys = json.loads(keyFile.read())
    for k, v in readApiKeys.items():
        apikeys[k] = v


# Reading device configuration
#
# Note:
#   config.json file is required to enable some traits of the device

configurations = {
    "google-drive-enabled": False,
    "google-assistant-enabled": False,
    "youtube-music-enabled": False,
}

try:
    with open('config.json', 'rt') as config:
        content = json.loads(config.read())
        for k, v in content.items():
            configurations[k] = v
except:
    print('config.json not found')


# Reading settings file
#
# Note:
#   Read UI application settings from settings.txt

applicationSettings = {}
defaultApplicationSettings = {
    'lat': 37.56779,  # latitude of Seoul, Korea
    'lon': 126.97765,  # longitude of Seoul, Korea
    'refresh_term': 30,  # refresh main widget after every 30 minutes
}

with open('settings.json', 'rt') as settingsFile:
    content = json.loads(settingsFile.read())

    for name, value in defaultApplicationSettings.items():  # copy default settings
        applicationSettings[name] = value

    for name, value in content.items():  # read settings from settings file
        applicationSettings[name.strip()] = value

def changeSettings(name, value):
    applicationSettings[name] = value
    saveSettings()

def saveSettings():
    with open('settings.json', 'wt') as settingsFile:
        settingsFile.write(json.dumps(applicationSettings))

def getSettings(name):
    return applicationSettings[name]


# Google login
#
# Note:
#   Login to google and generate user token for accessing private information

google_scope = []
if configurations['google-drive-enabled']:
    google_scope.append('https://www.googleapis.com/auth/drive.readonly')
if configurations['youtube-music-enabled']:
    google_scope.append('https://www.googleapis.com/auth/youtube.readonly')

if len(google_scope) != 0:
    googleclientIDfilename = apikeys['googleclientfilename']

    if 'user_account_tokens' not in os.listdir('assets'):
        os.mkdir(os.path.join('assets', 'user_account_tokens'))  # generate user_account_tokens directory

    # Generate login token via web browser
    tokenpath = os.path.join('assets', 'user_account_tokens', 'token.json')
    creds = None
    if os.path.exists(tokenpath):
        creds = Credentials.from_authorized_user_file(tokenpath, google_scope)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(f'assets/keys/{googleclientIDfilename}', google_scope)
            creds = flow.run_local_server()
        print(creds.to_json())
        with open(tokenpath, 'w') as token:
            token.write(creds.to_json())


# Weather data downloader
#
# Note:
#   Module for downloading weather data from given coordinate
#   Download weather data from openweathermap API
#   API link: https://openweathermap.org/

class WeatherDownloader:
    def __init__(self):
        self.lat = applicationSettings['lat']
        self.lon = applicationSettings['lon']
        self.apikey = apikeys['openweathermap']

    def refreshLocation(self):
        self.lat = applicationSettings['lat']
        self.lon = applicationSettings['lon']

    def download(self):
        URL = f'http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.apikey}&lang=kr&units=metric'
        response = requests.get(URL)
        if response.status_code == 200:
            ret = json.loads(response.text)
            return ret
        else:
            assert "HTTP request error occurred"

    def downloadWeatherIcon(self, iconId):  # download icon image from openweathermap api by using iconID
        iconURL = f"http://openweathermap.org/img/wn/{iconId}@2x.png"
        response = requests.get(iconURL)
        if response.status_code == 200:
            return response.content  # return image itself
        else:
            assert "HTTP request error occurred"


# Schedule data downloader
#
# Note:
#   Module for downloading scheudle data from user's private google drive storage
#   Download schedule data via Google Drive API (v3)
#   API link: https://developers.google.com/drive/api/v3/about-files

rootDirName = 'Ice Cream Hub'
scheduleDirName = 'Schedules'
driveFolderType = 'application/vnd.google-apps.folder'
driveTextFileType = 'text/plain'

class ScheduleDownloader:
    def __init__(self):
        global creds
        self.creds = creds

    def download(self, targetDate):
        try:
            service = build('drive', 'v3', credentials=self.creds)

            # Find out application root folder ID
            results = service.files().list(
                q=f"mimeType = '{driveFolderType}' and name = '{rootDirName}' and trashed = false",
                spaces='drive',
                fields='nextPageToken, files(id, name)').execute()
            items = results.get('files', [])
            if not items:
                return []
            rootDirID = items[0]['id']

            # Find out schedule folder
            results = service.files().list(
                q=f"mimeType = '{driveFolderType}' and name = '{scheduleDirName}' and trashed = false and '{rootDirID}' in parents",
                spaces='drive',
                fields='nextPageToken, files(id, name)').execute()
            items = results.get('files', [])
            if not items:
                return []
            scheduleDirID = items[0]['id']

            # Find out target file ID
            results = service.files().list(
                q=f"name = '{targetDate}.csv' and trashed = false and '{scheduleDirID}' in parents",
                spaces='drive',
                fields='nextPageToken, files(id, name)').execute()
            items = results.get('files', [])
            if not items:
                return []
            targetFileID = items[0]['id']

            # Download target file
            request = service.files().get_media(fileId=targetFileID)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%." % int(status.progress() * 100))

            # Parse downloaded content and return the data
            content = str(fh.getvalue(), 'utf-8')
            parsed = []
            for line in content.split('\n'):
                parsed.append(line.split(','))

            return parsed

        except HttpError as error:
            print(f'An error occurred: {error}')


# Bluetooth controlller
#
# Note:
#   Module for connecting with android app via bluetooth
#   Uses pybluez library (targetted on rasbian and linux OS)
#   Dependencies can be obtained by running command below:
#     => bash raspberry-bluetooth-setup.sh

class BluetoothController:
    def __init__(self):
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(('', bluetooth.PORT_ANY))
        self.server_sock.listen(1)

        self.port = self.server_sock.getsockname()[1]

        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

        bluetooth.advertise_service(
            self.server_sock, "Smart Mirror SSS001 service", service_id=uuid,
            service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
            profiles=[bluetooth.SERIAL_PORT_PROFILE],
        )

        self.client_sock = None
        self.client_info = None

    def connect(self):
        print(f'Waiting for connection: channel {self.port}')
        self.client_sock, self.client_info = self.server_sock.accept()
        print(f'Client accepted: {self.client_info}')

    
    def receive(self):
        try:
            data = self.client_sock.recv(1024)
            decodedData = json.loads(data)
            return decodedData
        
        except IOError or KeyboardInterrupt:
            print('Client disconnected')
            self.client_sock.close()
            return None
    
    def send(self, decodedData):
        try:
            data = json.dumps(decodedData, separators=(',', ':'))
            self.client_sock.send(data)
            print(data)

        except IOError or KeyboardInterrupt:
            print('Client disconnected')
            self.client_sock.close()
            return None


# Calender methods

def isLeapYear(year):
    return year % 4 == 0 and year % 100 != 0 or year % 400 == 0

def lastDay(year, month):
    m = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    m[1] = 29 if isLeapYear(year) else 28
    return m[month - 1]

def totalDay(year, month, day):
    total = ((year-1) * 365) + ((year-1) // 4) - ((year-1) // 100) + ((year-1) // 400)
    for i in range(1, month):
        total += lastDay(year, i)
    return total + day

def weekDay(year, month, day):
    return totalDay(year, month, day) % 7


# Google Assistant (Custom assistant-sdk-python)
#
# Note:
#   To enable google assistant, you need separaed file named 'config.json'
#   Add the code below:
#       {
#           "google-assistant-enabled": true
#       }
#   Before adding the file, check if you followed all of the instructions below
#
#   Prior to enable the google assistant, run "googlesample-assistant-pushtotalk" to make
#   sure that you already installed google assistant sdk to your environment and generated
#   your google OAuth2 credential file inside the appdir
#   If there's a problem, see the website below and follow the instruction
#     => https://developers.google.com/assistant/sdk/guides/service/python/
# 
#   There can be deprecated method inside google assistant sdk
#   For example, 'array.array.tostring()' is deprecated in python3.9 (audio_helpers.py)
#   So you need to use another method 'array.array.tobytes()' to avoid the error
#
#   The pushtotalk.py needs to be modified to use the code block below
#   Modified pushtotalk.py is provided within this project
#   Note that this modified pushtotalk.py is licenced by Google and cannot be used in
#   commercial purpose.

google_assistant_activate = lambda message_listner: None

if configurations['google-assistant-enabled']:
    import pushtotalk_modified as pushtotalk
    google_assistant_activate = pushtotalk.main

    # Get authentication via browser if there's no credential file
    credpath = os.path.join(os.path.expanduser('~'), '.config', 'google-oauthlib-tool')
    clientSecretPath = os.path.join(apikeysDirectoryPath, apikeys['googleassistantclientfilename'])
    if 'credentials.json' not in os.listdir(credpath):
        os.system(f"google-oauthlib-tool --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless --client-secrets {clientSecretPath}")

class AssistantListener(object):
        def __init__(self) -> None:
            self.msg = None
            self.token = None
            self.observers = []
        
        def edit(self, message, token=None):
            if self.msg is None or self.msg != message or (token is not None and self.token != token):
                self.msg = message
                self.token = token
                for callback in self.observers:
                    callback(self.msg, self.token)
        
        def initialize(self):
            self.msg = None
            self.token = None
            self.observers = []
        
        def bind(self, callback):
            self.observers.append(callback)

class AssistantManager:
    def __init__(self) -> None:
        self.assistantListener = AssistantListener()

    def activate(self, callback):
        if configurations['google-assistant-enabled']:
            self.assistantListener.initialize()
            pushtotalk.message_listener = self.assistantListener
            self.assistantListener.bind(callback)
            google_assistant_activate()


# YouTube music manager
#
# Note:
#   Plays a music from youtube metadata and vlc player

class YouTubeMusicManager:
    def __init__(self) -> None:
        global creds
        self.creds = creds


# # Testbench code for bluetooth connection (RFCOMM)
#
# if __name__ == '__main__':
#     bluetoothController = BluetoothController()
#     while True:
#         bluetoothController.connect()
#         while True:
#             token = bluetoothController.receive()  # Receive
#             if token is None:
#                 break


# # Testbench code for google assistant (custom assistant-sdk-python)
# if __name__ == '__main__':
#     manager = AssistantManager()
    
#     def testCallbackFunc(msg, token):
#         print(f'===== {msg}')
#         print(f'===== {token}')
    
#     manager.activate(testCallbackFunc)