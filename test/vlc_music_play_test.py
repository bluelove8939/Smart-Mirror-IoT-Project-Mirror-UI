import os
import json
import pafy
import vlc


# os.add_dll_directory(os.getcwd())

apikeys = {}
apikeysDirectoryPath = os.path.join(os.path.dirname(__file__), '..', 'assets', 'keys')

with open(os.path.join(os.path.dirname(__file__), '..', 'assets', 'keys', 'apikeys.json'), 'rt') as keyFile:
    readApiKeys = json.loads(keyFile.read())
    for k, v in readApiKeys.items():
        apikeys[k] = v

status = 0

@vlc.callbackmethod
def test_callback_func(data):
    print('callback called')
    global status
    status = 1

if "youtubeapikey" in apikeys.keys():
    pafy.set_api_key(apikeys["youtubeapikey"])

url = "https://www.youtube.com/watch?v=L6HRp9GUTT0"
video = pafy.new(url)
best = video.getbestaudio()
playurl = best.url

Instance = vlc.Instance()
player = Instance.media_player_new()
Media = Instance.media_new(playurl)
Media.get_mrl()
player.set_media(Media)
events = player.event_manager()
events.event_attach(vlc.EventType.MediaPlayerEndReached, test_callback_func, 1)

player.play()

while status == 0:
    continue
