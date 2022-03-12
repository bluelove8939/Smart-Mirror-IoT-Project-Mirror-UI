import os
import sys

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QLabel, QGroupBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout  # Layouts

from PyQt5.QtCore import QDate          # Date widgets
from PyQt5.QtCore import QTime, QTimer  # Time widgets
from PyQt5.QtCore import Qt             # Qt.AlignCenter

from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap, QFontDatabase

from dataManager import WeatherDownloader


# Main user interface
#
# Note:
#   Indicates information about current datetime, scheudles, weather ...

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        # Global variables
        self.weatherDownloader = WeatherDownloader()

        # Window Settings
        self.setWindowTitle('Smart Mirror System')
        self.setWindowIcon(QIcon('assets/title_icon.png'))
        self.setStyleSheet('background-color:black;')
        self.setGeometry(0, 0, 700, 1000)

        # Time widget
        self.dateTimeWidget = QLabel()
        self.dateTimeWidget.setAlignment(Qt.AlignCenter)
        self.dateTimeWidget.setStyleSheet("color: white; font-size: 36px; font-weight: bold")

        # Run timer (time widget)
        timer = QTimer(self)                  # generate timer widget
        timer.timeout.connect(self.showTime)  # refresh label widget when timeout called
        timer.start(1000)                     # run timer widget

        # Schedule widget
        self.scheduleWidget = self.generateScheduleWidget()

        # Weather widget
        self.weatherWidget = self.generateWeatherWidget()

        # Generating layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(20, 20, 20, 20)
        mainLayout.addWidget(self.dateTimeWidget)
        mainLayout.addStretch(1)

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.weatherWidget)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.scheduleWidget)
        mainLayout.addLayout(bottomLayout)

        self.setLayout(mainLayout)

        # self.showFullScreen()
        self.show()

    def showTime(self):
        currentTime = QTime.currentTime().toString('hh:mm')
        currentDate = QDate.currentDate().toString('yyyy-MM-dd dddd')
        self.dateTimeWidget.setText(f'{currentDate} {currentTime}')  # change timeWidget

    def generateScheduleWidget(self):
        groupbox = QGroupBox()
        groupbox.setMaximumWidth(250)
        groupbox.setStyleSheet('background-color: grey;'
                               "border-style: solid;"
                               "border-width: 2px;"
                               "border-color: grey;"
                               "border-radius: 15px")

        label = QLabel('schedules')

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.setContentsMargins(20, 20, 20, 20)
        groupbox.setLayout(vbox)

        return groupbox

    def generateWeatherWidget(self):
        groupbox = QGroupBox()
        groupbox.setMaximumWidth(210)
        groupbox.setFixedHeight(250)
        groupbox.setStyleSheet('background-color: grey;'
                               "border-style: solid;"
                               "border-width: 2px;"
                               "border-color: grey;"
                               "border-radius: 15px")

        # Download weather data
        weatherDataJson = self.weatherDownloader.download()

        # Generate weather subwidgets
        cityNameWidget = QLabel(f"{str(weatherDataJson.get('name'))}")
        temperatureWidget = QLabel(f"현재기온 {str(weatherDataJson.get('main').get('temp'))}°C")
        minMaxTemperatureWidget = QLabel(f"(최소 {str(weatherDataJson.get('main').get('temp_min'))}°C 최대 {str(weatherDataJson.get('main').get('temp_max'))}°C)")
        humidityWidget = QLabel(f"습도 {str(weatherDataJson.get('main').get('humidity'))}%")

        # Generate weather icon widget
        weatherIconImage = QImage()
        weatherIconImage.loadFromData(self.weatherDownloader.downloadWeatherIcon(str(weatherDataJson.get('weather')[0].get('icon'))))
        weatherIconPixmap = QPixmap(weatherIconImage)
        weatherIconPixmap.scaledToHeight(64)
        weatherIconwidget = QLabel()
        weatherIconwidget.setPixmap(weatherIconPixmap)

        # Set style of generated sub widgets
        cityNameWidget.setStyleSheet('font-size: 13pt; font-weight: bold')
        temperatureWidget.setStyleSheet('font-size: 13pt; font-weight: bold')
        humidityWidget.setStyleSheet('font-size: 13pt; font-weight: bold')
        minMaxTemperatureWidget.setStyleSheet('font-size: 10pt; font-weight: bold')

        # Generate layouts fo subwidgets and return weather widget
        vbox = QVBoxLayout()
        vbox.addWidget(weatherIconwidget)
        vbox.addWidget(cityNameWidget)
        vbox.addWidget(temperatureWidget)
        vbox.addWidget(minMaxTemperatureWidget)
        vbox.addWidget(humidityWidget)
        vbox.setContentsMargins(20, 0, 20, 20)
        groupbox.setLayout(vbox)

        return groupbox


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()


    # Set font as 'SUIT'
    #   This font is open-source font from the link below
    #   URL: https://sunn.us/suit/

    fontDirname = os.path.join(os.getcwd(), 'assets', 'fonts')
    fontFilenames = [filename for filename in os.listdir(fontDirname) if
                     os.path.isfile(os.path.join(fontDirname, filename))]
    fontIds = []
    for targetFilename in fontFilenames:
        fontIds.append(QFontDatabase.addApplicationFont(os.path.join(fontDirname, targetFilename)))
    app.setFont(QFont('SUIT'))


    # Running the application

    sys.exit(app.exec_())