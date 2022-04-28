import io
import os
import requests
import json
import os.path
import logging
from gi.repository import GObject as gobject

# Google OAuth2 requirements
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# YouTube music player requirements
import pafy
import vlc

# Bluetooth requirements (pybluez lib)
import bluetooth

# Face emotion detection requirements
import face_emotion_detection


# Data Manager Init Listener
# 
# Note:
#   Checks whether device is already initialized
#   Needs to be initialized:
#     * readApikey: read API keys
#     * readDeviceConfig: read device configuration
#     * readSettings: read device settings from local storage
#     * googleAccountAuth: get authentication for user's google account
#     * googleAssistantAuth: get authentivation for google assistant SDK

class DataManagerInitListener:
    INITIALIZED = 0
    NOT_INITIALIZED = 1

    def __init__(self) -> None:
        self.states = {
            'readApikey': DataManagerInitListener.NOT_INITIALIZED,
            'readDeviceConfig': DataManagerInitListener.NOT_INITIALIZED,
            'readSettings': DataManagerInitListener.NOT_INITIALIZED,
            'googleAccountAuth': DataManagerInitListener.NOT_INITIALIZED,
            'googleAssistantAuth': DataManagerInitListener.NOT_INITIALIZED,
        }
    
    def setInitialized(self, key):
        if key in self.states.keys():
            self.states[key] = DataManagerInitListener.INITIALIZED

    def isInitialized(self):
        for value in self.states.values():
            if value != DataManagerInitListener.INITIALIZED:
                return False
        return True

dataManagerInitListener = DataManagerInitListener()


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

dataManagerInitListener.setInitialized('readApikey')


# Reading device configuration
#
# Note:
#   config.json file is required to enable some traits of the device

configurations = {
    "google-drive-enabled": False,
    "google-assistant-enabled": False,
    "youtube-music-enabled": False,
    "face-emotion-detection-enabled": False,
    "device-logging-option": "INFO",
}

try:
    with open('config.json', 'rt') as config:
        content = json.loads(config.read())
        for k, v in content.items():
            configurations[k] = v
except:
    print('config.json not found')

if configurations['device-logging-option'] == "INFO":
    logging.basicConfig(level=logging.INFO)
elif configurations['device-logging-option'] == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)

dataManagerInitListener.setInitialized('readDeviceConfig')


# Reading settings file
#
# Note:
#   Read UI application settings from settings.txt

applicationSettings = {}
defaultApplicationSettings = {
    'lat': 37.56779,  # latitude (initialized as Seoul, Korea)
    'lon': 126.97765,  # longitude (initialized as Seoul, Korea)
    'refresh_term': 30,  # refresh term (initialized as 30 seconds)
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

dataManagerInitListener.setInitialized('readSettings')


# Google login function
#
# Note:
#   Function for obtaining OAuth2 credential

def makeCredentialFromClientfile(clientfile, scopes, savepath):
    creds = None

    if os.path.exists(savepath):
        creds = Credentials.from_authorized_user_file(tokenpath, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(clientfile, scopes)
            creds = flow.run_local_server()
        with open(savepath, 'w') as savefile:
            savefile.write(creds.to_json())

    return creds


# Google login with user authentication
#
# Note:
#   Login to google and generate user token for accessing private information
#   This login process includes user account login and google assistant authentication
#   (Processed by different browser window) 

# User account authentication process
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
    creds = makeCredentialFromClientfile(googleclientIDfilename, google_scope, tokenpath)

dataManagerInitListener.setInitialized('googleAccountAuth')

# Google assistant authentication process
if configurations['google-assistant-enabled']:
    # Get authentication via browser if there's no credential file
    credpath = os.path.join(os.path.expanduser('~'), '.config', 'google-oauthlib-tool', 'credentials.json')
    clientSecretPath = os.path.join('assets', 'keys', apikeys['googleassistantclientfilename'])
    assistant_scope = ['https://www.googleapis.com/auth/assistant-sdk-prototype']
    assistant_creds = makeCredentialFromClientfile(clientSecretPath, assistant_scope, credpath)

dataManagerInitListener.setInitialized('googleAssistantAuth')


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
            logging.error("[WEATHER DOWNLOADER] HTTP request error occurred") 

    def downloadWeatherIcon(self, iconId):  # download icon image from openweathermap api by using iconID
        iconURL = f"http://openweathermap.org/img/wn/{iconId}@2x.png"
        response = requests.get(iconURL)
        if response.status_code == 200:
            return response.content  # return image itself
        else:
            logging.error("[WEATHER DOWNLOADER] HTTP request error occurred") 


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
            logging.error("[SCHEDULE DOWNLOADER] HTTP request error occurred") 


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
        logging.info(f"[BLUETOOTH] Waiting for bluetooth connection: channel {self.port}") 
        self.client_sock, self.client_info = self.server_sock.accept()
        logging.info(f'[BLUETOOTH] Client accepted: {self.client_info}')

    
    def receive(self):
        try:
            data = self.client_sock.recv(1024)
            decodedData = json.loads(data)
            return decodedData
        
        except IOError or KeyboardInterrupt:
            logging.info('[BLUETOOTH] Client disconnected')
            self.client_sock.close()
            return None
    
    def send(self, decodedData):
        try:
            data = json.dumps(decodedData, separators=(',', ':'))
            self.client_sock.send(data)
            print(data)

        except IOError or KeyboardInterrupt:
            logging.info('[BLUETOOTH] Client disconnected')
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

google_assistant_activate = lambda: None

if configurations['google-assistant-enabled']:
    import pushtotalk_modified as pushtotalk
    google_assistant_activate = pushtotalk.main

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

class AssistantTrigger:
    def __init__(self) -> None:
        self.flag = False
    
    def istriggered(self):
        if self.flag:
            self.flag = False
            return True
        return False

    def trigger(self):
        self.flag = True

class AssistantManager:
    def __init__(self) -> None:
        self.assistantListener = AssistantListener()
        self.assistantTrigger = AssistantTrigger()
        pushtotalk.assistant_trigger = self.assistantTrigger

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

cachesDirectoryPath = os.path.join(os.path.curdir, 'caches')
faceEmotionDetectModule = None

if "youtubeapikey" in apikeys.keys():
    pafy.set_api_key(apikeys["youtubeapikey"])

if configurations['face-emotion-detection-enabled']:
    faceEmotionDetectModule = face_emotion_detection.MirrorFaceDetect(face_apikey=apikeys['azureface'], face_api_endpoint=apikeys['azureface-endpoint'])

def readYouTubeCaches():
    with open(os.path.join(cachesDirectoryPath, 'youtube_cache.json'), 'r') as cache:
        cached_data = json.loads(cache.read())
    return cached_data

def writeYouTubeCaches(playlist, query):
    with open(os.path.join(cachesDirectoryPath, 'youtube_cache.json'), 'wt') as cache:
        cache.write(json.dumps({
            'playlist': playlist,
            'query': query,
        }))

class StateListner:
    def __init__(self, initial_state=None) -> None:
        self.state = initial_state
        self.callbacks = []
        
    def edit(self, value):
        self.state = value
        for method, args in self.callbacks:
            method(*args)

    def bind(self, method, *args):
        self.callbacks.append((method, args))

    def __eq__(self, value):
        if isinstance(value, StateListner):
            return self == value
        return self.state == value

class YouTubeMusicManager:
    STOPPED = 0
    PLAYING = 1
    LOADING = 2
    INVALID = 3

    def __init__(self) -> None:
        global creds
        self.creds = creds
        self.nextPageToken = None
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.events = self.player.event_manager()
        self.state = StateListner(YouTubeMusicManager.INVALID)
        
        self.events.event_attach(vlc.EventType.MediaPlayerEndReached, self.autoMoveNext)

        self._ready = False
        self.current_playlist = None
        self.current_index = None
        self.current_query = None

        self.service = build('youtube', 'v3', credentials=self.creds)

        try:
            cached_data = readYouTubeCaches()
            self.current_playlist = cached_data['playlist']
            self.current_index = 0
            self.current_query = cached_data['query']
            self.setPlayer(self.current_playlist[self.current_index]['id']['videoId'])
            self._ready = True
            self.state.edit(YouTubeMusicManager.STOPPED)
        except:
            print('Cannot find youtube caches')

        self.binded = []

    def searchByEmotion(self):
        if not configurations['face-emotion-detection-enabled']:
            return
        
        emotion_result = faceEmotionDetectModule.detect_motion_webcam()

        if emotion_result['exception'] != face_emotion_detection.azure_api_wrapper.NO_EXCEPTION_MSG:
            logging.error('[YOUTUBE MUSIC] Exception occurred on detecting face emotion')
            return False

        pref_result, max_value = None, 0

        for key, value in emotion_result.items():
            if key == 'exception':
                continue
            
            if float(value) > max_value:
                max_value = float(value)
                pref_result = key
        
        logging.info(f'[YOUTUBE MUSIC] Face emotion estimation: {pref_result}')
        
        self.search(query=f"{pref_result} musics")
        return True
    
    def search(self, query=None, cnt=5, nextpage=False):
        try:
            if not self.isStopped():
                self.pause()

            # Use current query if query is None
            if query is None and self.current_query is not None:
                query = self.current_query
            elif query is None and self.current_query is None:
                logging.warning('[YOUTUBE MUSIC] Search warning: query required')
                raise Exception()

            # Send request
            if nextpage and self.nextPageToken is not None:
                # Search by using the given keyword
                search_result = self.service.search().list(
                    q=query, part='snippet', maxResults=cnt, regionCode='KR',
                    type='video', videoCategoryId='10', pageToken=self.nextPageToken
                    ).execute()
            else:
                # Search by using the given keyword
                search_result = self.service.search().list(
                    q=query, part='snippet', maxResults=cnt, regionCode='KR',
                    type='video', videoCategoryId='10'
                    ).execute()

            self.nextPageToken = search_result['nextPageToken']

            if nextpage == False:
                self.current_playlist = search_result['items']
                self.current_query = query
                self.current_index = 0
            elif len(search_result) > 0:
                self.current_playlist += search_result['items']
            else:
                self.current_index = 0
            
            writeYouTubeCaches(self.current_playlist, self.current_query)

            self.state.edit(YouTubeMusicManager.STOPPED)
            self._ready = False
            
        except:
            logging.error(f'[YOUTUBE MUSIC] Error occurred on searching with query: {query}')
    
    def setPlayer(self, videoId):
        self.state.edit(YouTubeMusicManager.LOADING)
        self._ready = False
 
        video_url = f"https://www.youtube.com/watch?v={videoId}"
        video = pafy.new(video_url)
        best = video.getbestaudio()
        playurl = best.url

        media = self.instance.media_new(playurl)
        media.get_mrl()
        self.player.set_media(media)

        self._ready = True
    
    def moveNext(self):
        # self.state.edit(YouTubeMusicManager.LOADING)
        self.player.pause()

        self.current_index += 1
        if self.current_index >= len(self.current_playlist):
                self.search(nextpage=True)
        try:
            self.setPlayer(self.current_playlist[self.current_index]['id']['videoId'])
            self.player.play()
            self.state.edit(YouTubeMusicManager.PLAYING)
        except:
            self.moveNext()

    def movePrev(self):
        # self.state.edit(YouTubeMusicManager.LOADING)
        self.player.pause()
            
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = len(self.current_playlist) - 1
        try:
            self.setPlayer(self.current_playlist[self.current_index]['id']['videoId'])
            self.player.play()
            self.state.edit(YouTubeMusicManager.PLAYING)
        except:
            self.movePrev()
    
    @vlc.callbackmethod
    def autoMoveNext(self, data):
        gobject.idle_add(self.moveNext)

    def play(self):
        # self.state.edit(YouTubeMusicManager.LOADING)
        try:
            if not self._ready:
                if self.current_playlist is not None and self.current_query is not None:
                    if self.current_index is None:
                        self.current_index = 0
                else:
                    self.state.edit(YouTubeMusicManager.STOPPED)
                    return
                self.setPlayer(self.current_playlist[self.current_index]['id']['videoId'])
            self.player.play()
            if self.player.get_state() == vlc.State.Error:
                logging.error('[YOUTUBE MUSIC] Error ocurred on playing music')
                raise Exception()
            self.state.edit(YouTubeMusicManager.PLAYING)
        except:
            logging.info('[YOUTUBE MUSIC] Skipped because an error occurred on playing music')
            self.moveNext()
            self.play()

    def pause(self):
        if self.player.get_state() != vlc.State.Paused:
            self.player.pause()
            self.state.edit(YouTubeMusicManager.STOPPED)

    def bindCallback(self, method, *args):
        self.state.bind(method, *args)
        
    def isStopped(self):
        return self.state == YouTubeMusicManager.STOPPED

    def isPlaying(self):
        return self.state == YouTubeMusicManager.PLAYING

    def isLoading(self):
        return self.state == YouTubeMusicManager.LOADING

    def isInvalid(self):
        return self.state == YouTubeMusicManager.INVALID


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
#
#     def testCallbackFunc(msg, token):
#         print(f'===== {msg}')
#         print(f'===== {token}')
#   
#     manager.activate(testCallbackFunc)


# Testbench code for youtube music manager
# if __name__ == '__main__':
#     import time
#
#     manager = YouTubeMusicManager()
#     res = manager.search('zior park')
#     manager.play()
#
#     while True:
#         c = input('Enter command: ')
#         if c == 'play':
#             manager.play()
#         if c == 'pause':
#             manager.pause()
#         if c == 'next':
#             manager.moveNext()
#             manager.play()
#         if c == 'prev':
#             manager.movePrev()
#             manager.play()


# Testbench code for face emotion detection
if __name__ == '__main__':
    face_emotion_module = face_emotion_detection.MirrorFaceDetect(apikeys['azureface'], apikeys['azureface-endpoint'])
    print(face_emotion_module.detect_motion_webcam())