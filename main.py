import os
import sys

from PyQt5 import sip
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QLabel, QGroupBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout  # Layouts

from PyQt5 import QtCore
from PyQt5.QtCore import QDate          # Date widgets
from PyQt5.QtCore import QTime, QTimer  # Time widgets
from PyQt5.QtCore import Qt             # Qt.AlignCenter
from PyQt5.QtCore import QThread

from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap, QFontDatabase

from dataManager import WeatherDownloader, ScheduleDownloader, BluetoothController
from dataManager import changeSettings, saveSettings, getSettings, weekDay, lastDay


# Widget styles

widgetDefaultStyleSheet = 'background-color: black; border-style: solid; border-color: white; border-width: 0.5px; border-radius: 10px;'
labelDefaultStyleSheet = 'border-style: none;'


# Bluetooth thread
#
# Note:
#   Receives token from smartphone application and sends response token

class BluetoothThread(QThread):
    threadEvent = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.controller = BluetoothController()
    
    def run(self):
        while True:
            self.controller.connect()
            while True:
                token = self.controller.receive()
                if token is None:
                    break
                else:
                    sendToken = self.generateSendToken(token)
                    self.controller.send(sendToken)
                    self.threadEvent.emit(token)
    
    def generateSendToken(self, token):
        return token


# Main user interface
#
# Note:
#   Indicates information about current datetime, scheudles, weather ...

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        # Global variables
        self.refreshedTime = QTime.currentTime()
        self.weatherDownloader = WeatherDownloader()
        self.scheduleDownloader = ScheduleDownloader()

        # Window Settings
        self.setWindowTitle('Smart Mirror System')
        self.setWindowIcon(QIcon('assets/title_icon.png'))
        self.setStyleSheet('background-color:black;')
        # self.setGeometry(0, 0, 1400, 1000)
        self.updatesEnabled = True

        # Time widget
        self.dateTimeWidget = QLabel()
        self.dateTimeWidget.setAlignment(Qt.AlignCenter)
        self.dateTimeWidget.setStyleSheet("color: white; font-size: 36px; font-weight: bold")

        # Run timer (time widget)
        timer = QTimer(self)                  # generate timer widget
        timer.timeout.connect(self.showTime)  # refresh label widget when timeout called
        timer.start(1000)                     # run timer widget

        # Generate main window layout
        self.scheduleWidget = None  # schedule widget
        self.weatherWidget = None   # weather widget
        self.calendarWidget = None  # calendar widget
        self.mainLayout = None
        self.drawWindow()  # generate main layout and set widget layout as main layout

        # Run bluetooth thread
        self.bluetoothThread = BluetoothThread()
        self.bluetoothThread.start()
        self.bluetoothThread.threadEvent.connect(self.takeAction)

        self.showFullScreen()
        # self.show()

    def drawWindow(self):
        # Schedule widget
        self.scheduleWidget = self.generateScheduleWidget()

        # Weather widget
        self.weatherWidget = self.generateWeatherWidget()

        # Calendar widget
        self.calendarWidget = self.generateCalenderWidget()

        # Generating layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.addWidget(self.dateTimeWidget)
        
        self.mainLayout.addStretch(1)

        centerLayout = QHBoxLayout()
        centerLayout.addWidget(self.scheduleWidget)
        centerLayout.addStretch(1)
        self.mainLayout.addLayout(centerLayout)
        
        self.mainLayout.addStretch(1)

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.weatherWidget)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.calendarWidget)
        self.mainLayout.addLayout(bottomLayout)

        self.setLayout(self.mainLayout)

    def showTime(self):
        currentTime = QTime.currentTime().toString('hh:mm')
        currentDate = QDate.currentDate().toString('yyyy-MM-dd dddd')
        self.dateTimeWidget.setText(f'{currentDate} {currentTime}')  # change timeWidget

        refreshTerm = getSettings('refresh_term')
        if (self.refreshedTime.secsTo(QTime.currentTime()) // 60) >= refreshTerm:
            self.refresh()
        
    def generateScheduleWidget(self):
        groupbox = QGroupBox()
        groupbox.setFixedWidth(190)
        groupbox.setStyleSheet(widgetDefaultStyleSheet)

        scheduleDataList = self.scheduleDownloader.download(QDate.currentDate().toString('yyyy-MM-dd'))

        titleLabel = QLabel("일정" if len(scheduleDataList) > 0 else "일정을 추가하세요")
        titleLabel.setStyleSheet(labelDefaultStyleSheet + 
            'color: white; font-size: 11pt; font-weight: bold; border-style: none;')

        labels = [titleLabel]
        for schedule in scheduleDataList:
            label = QLabel(schedule[0])
            if schedule[1] == '1':
                label.setStyleSheet(labelDefaultStyleSheet + 
                    'color: white; font-size: 10pt; font-weight: bold; text-decoration: line-through;')
            else:
                label.setStyleSheet(labelDefaultStyleSheet + 
                    'color: white; font-size: 10pt; font-weight: bold; border-style: none;')
            labels.append(label)

        vbox = QVBoxLayout()
        if len(scheduleDataList) == 0:
            vbox.setAlignment(Qt.AlignCenter)
            vbox.addStretch(1)
        for widget in labels:
            vbox.addWidget(widget)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.addStretch(1)
        groupbox.setLayout(vbox)

        return groupbox

    def generateWeatherWidget(self):
        groupbox = QGroupBox()
        groupbox.setFixedWidth(190)
        groupbox.setFixedHeight(240)
        groupbox.setStyleSheet(widgetDefaultStyleSheet)

        # Download weather data
        weatherDataJson = self.weatherDownloader.download()

        # Generate weather subwidgets
        cityNameWidget = QLabel(f"{str(weatherDataJson.get('name'))}")
        temperatureWidget = QLabel(f"현재기온 {str(weatherDataJson.get('main').get('temp'))}°C")
        minMaxTemperatureWidget = QLabel(f"(최소 {str(weatherDataJson.get('main').get('temp_min'))}°C 최대 {str(weatherDataJson.get('main').get('temp_max'))}°C)")
        humidityWidget = QLabel(f"습도 {str(weatherDataJson.get('main').get('humidity'))}%")
        refreshedTimeWidget = QLabel(f"{self.refreshedTime.toString('hh:mm:ss')}에 새로고침 됨")

        # Generate weather icon widget
        weatherIconImage = QImage()
        weatherIconImage.loadFromData(self.weatherDownloader.downloadWeatherIcon(str(weatherDataJson.get('weather')[0].get('icon'))))
        weatherIconPixmap = QPixmap(weatherIconImage)
        weatherIconPixmap.scaledToHeight(64)
        weatherIconwidget = QLabel()
        weatherIconwidget.setPixmap(weatherIconPixmap)

        # Set style of generated sub widgets
        cityNameWidget.setStyleSheet(labelDefaultStyleSheet + 'font-size: 10pt; font-weight: bold; color: white;')
        temperatureWidget.setStyleSheet(labelDefaultStyleSheet + 'font-size: 10pt; font-weight: bold; color: white;')
        humidityWidget.setStyleSheet(labelDefaultStyleSheet + 'font-size: 10pt; font-weight: bold; color: white;')
        minMaxTemperatureWidget.setStyleSheet(labelDefaultStyleSheet + 'font-size: 8pt; font-weight: bold; color: white;')
        refreshedTimeWidget.setStyleSheet(labelDefaultStyleSheet + 'font-size: 8pt; font-weight: normal;  color: white;')
        weatherIconwidget.setStyleSheet('border-style: none')

        # Generate layouts fo subwidgets and return weather widget
        vbox = QVBoxLayout()
        vbox.addWidget(weatherIconwidget)
        vbox.addWidget(cityNameWidget)
        vbox.addWidget(temperatureWidget)
        vbox.addWidget(minMaxTemperatureWidget)
        vbox.addWidget(humidityWidget)
        vbox.addWidget(refreshedTimeWidget)
        vbox.setContentsMargins(20, 0, 20, 20)
        groupbox.setLayout(vbox)

        return groupbox

    def generateCalenderWidget(self):
        groupbox = QGroupBox()
        groupbox.setFixedWidth(190)
        groupbox.setStyleSheet(widgetDefaultStyleSheet)
        
        today = QDate.currentDate()
        targetMonth = today.month()
        targetYear = today.year()

        # Generate calender layouts
        vbox = QVBoxLayout()  # main layout
        vbox.addStretch(1)
        
        # 1. Layout for calender header
        calenderHeaderLabel = QLabel(f'{targetYear}년 {targetMonth}월')
        calenderHeaderLabel.setStyleSheet(labelDefaultStyleSheet + 'font-size: 11pt; font-weight: bold; color: white;')
        headerLayout = QHBoxLayout()
        headerLayout.addStretch(1)
        headerLayout.addWidget(calenderHeaderLabel)
        headerLayout.addStretch(1)
        vbox.addStretch(1)
        vbox.addLayout(headerLayout)
        vbox.addStretch(1)
        
        
        # 2. Layout for weekdays
        calenderBodyGridLayout = QGridLayout()
        weekdayNames = ['일', '월', '화', '수', '목', '금', '토']

        for cidx, name in enumerate(weekdayNames):
            lbl = QLabel(name)
            if cidx == 0:
                lbl.setStyleSheet(labelDefaultStyleSheet + 'font-size: 9pt; font-weight: bold; color: red;')
            else:
                lbl.setStyleSheet(labelDefaultStyleSheet + 'font-size: 9pt; font-weight: bold; color: white;')
            calenderBodyGridLayout.addWidget(lbl, 0, cidx)
        

        # 3. Layout for calender body
        ridx, cidx = 1, weekDay(targetYear, targetMonth, 1)
        
        for targetDay in range(1, lastDay(targetYear, targetMonth)+1):  
            lbl = QLabel(str(targetDay))
            if cidx == 0:
                lbl.setStyleSheet(labelDefaultStyleSheet + 'font-size: 9pt; font-weight: bold; color: red;')
            elif QDate.currentDate() == QDate(targetYear, targetMonth, targetDay):
                lbl.setStyleSheet(labelDefaultStyleSheet + 'font-size: 9pt; font-weight: bold; color: black; background-color: white;')
            else:
                lbl.setStyleSheet(labelDefaultStyleSheet + 'font-size: 9pt; font-weight: bold; color: white;')
            calenderBodyGridLayout.addWidget(lbl, ridx, cidx)
            cidx += 1
            
            if cidx == 7:
                ridx += 1
                cidx = 0
        
        calenderBodyLayout = QHBoxLayout()
        calenderBodyLayout.addStretch(1)
        calenderBodyLayout.addLayout(calenderBodyGridLayout)
        calenderBodyLayout.addStretch(1)
        vbox.addLayout(calenderBodyLayout)
        vbox.addStretch(1)
        vbox.setContentsMargins(20, 0, 20, 20)
        groupbox.setLayout(vbox)

        return groupbox


    def deleteLayout(self, cur_lay):
        if cur_lay is not None:
            while cur_lay.count():
                item = cur_lay.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteLayout(item.layout())
            sip.delete(cur_lay)

    def refresh(self):
        self.refreshedTime = QTime.currentTime()
        self.deleteLayout(self.mainLayout)  # remove main layout
        self.drawWindow()  # regenerate main layout and set widget layout as main layout

    @QtCore.pyqtSlot(dict)
    def takeAction(self, token):
        if token['type'] == 'set_location':
            changeSettings('lat', token['args'][0])
            changeSettings('lon', token['args'][1])
            saveSettings()
            self.weatherDownloader.refreshLocation()
            self.refresh()
        
        elif token['type'] == 'refresh':
            self.refresh()

        elif token['type'] == 'set_auto_interval':
            changeSettings('refresh_term', token['args'][0])
            self.refresh()


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