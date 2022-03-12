import os
import requests
import json


# Reading required apikeys
#
# Note:
#   API keys is at file named 'assets/keys/apikeys.txt'
#   Make your own CSV file for API keys or just manually generate the 'apikeys' dictionary

apikeys = {}

with open(os.path.join('assets', 'keys', 'apikeys.txt'), 'rt') as keyFile:
    content = list(map(lambda x: x.split(','), keyFile.readlines()))
    for keyname, keycontent in content:
        apikeys[keyname] = keycontent.strip()


# Reading settings file
#
# Note:
#   Read UI application settings from settings.txt

applicationSettings = {}
defaultApplicationSettings = {
    'lat': '37.56779',  # latitude of Seoul, Korea
    'lon': '126.97765',  # longitude of Seoul, Korea
}

with open('settings.txt', 'rt') as settingsFile:
    content = list(map(lambda x: x.split(','), settingsFile.readlines()))

    for name, value in defaultApplicationSettings.items():  # copy default settings
        applicationSettings[name] = value

    for name, value in content:  # read settings from settings file
        applicationSettings[name] = value.strip()


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

