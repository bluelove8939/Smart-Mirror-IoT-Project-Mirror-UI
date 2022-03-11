import os
import requests
import json


class WeatherDownloader:
    def __init__(self):
        self.lat = 37.29410404832249
        self.lon = 126.97533756753458
        self.apikey = 'bfbfaac336f64b9f2b20f8b1bb583e56'

    def download(self):
        URL = f'http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.apikey}&lang=kr&units=metric'
        response = requests.get(URL)
        if response.status_code == 200:
            ret = json.loads(response.text)
            return ret
        else:
            assert "HTTP request error occurred"

    def downloadWeatherIcon(self, iconId):
        iconURL = f"http://openweathermap.org/img/wn/{iconId}@2x.png"
        response = requests.get(iconURL)
        if response.status_code == 200:
            return response.content
        else:
            assert "HTTP request error occurred"

