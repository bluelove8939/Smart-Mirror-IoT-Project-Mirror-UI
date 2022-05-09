from gc import callbacks
import os
import sys
import functools
import datetime
import time

from PyQt5 import sip
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QLabel, QGroupBox, QPushButton, QMessageBox, QProgressBar
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout  # Layouts

from PyQt5 import QtCore
from PyQt5.QtCore import QDate          # Date widgets
from PyQt5.QtCore import QTime, QTimer  # Time widgets
from PyQt5.QtCore import Qt             # Qt.AlignCenter
from PyQt5.QtCore import QThread

from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap, QFontDatabase

from data_manager import vlc
from data_manager import dataManagerInitListener
from data_manager import WeatherDownloader, ScheduleDownloader, BluetoothController, AssistantManager, YouTubeMusicManager, SkinConditionUploader, StyleRecommendationManager
from data_manager import changeSettings, saveSettings, getSettings, weekDay, lastDay

from hardware_manager import MoistureManager, AudioManager, ButtonManager


# Widget styles
widgetDefaultStyleSheet = 'background-color: black; border-style: solid; border-color: white; border-width: 0.5px; border-radius: 10px;'
labelDefaultStyleSheet = 'border-style: none;'

# Image urls
imgdir = os.path.join(os.path.abspath(os.path.curdir), 'assets', 'images')
assistant_logo = os.path.join(imgdir, 'assistant_logo.PNG')
button_play = os.path.join(imgdir, 'play.PNG')
button_pause = os.path.join(imgdir, 'pause.PNG')
button_next = os.path.join(imgdir, 'next.PNG')
button_prev = os.path.join(imgdir, 'prev.PNG')
button_opening = os.path.join(imgdir, 'opening.PNG')

# Sidebar icons
sidebar_imgdir = os.path.join(imgdir, 'sidebar_icons')
sidebar_assistant = os.path.join(sidebar_imgdir, 'sidebar_assistant.PNG')
sidebar_back = os.path.join(sidebar_imgdir, 'sidebar_back.PNG')
sidebar_cloth = os.path.join(sidebar_imgdir, 'sidebar_cloth.PNG')
sidebar_expression = os.path.join(sidebar_imgdir, 'sidebar_expression.PNG')
sidebar_play = os.path.join(sidebar_imgdir, 'sidebar_play.PNG')
sidebar_refresh = os.path.join(sidebar_imgdir, 'sidebar_refresh.PNG')
sidebar_select = os.path.join(sidebar_imgdir, 'sidebar_select.PNG')
sidebar_water = os.path.join(sidebar_imgdir, 'sidebar_water.PNG')
sidebar_music = os.path.join(sidebar_imgdir, 'sidebar_music.PNG')
sidebar_next = os.path.join(sidebar_imgdir, 'sidebar_next.PNG')
sidebar_prev = os.path.join(sidebar_imgdir, 'sidebar_prev.PNG')
sidebar_settings = os.path.join(sidebar_imgdir, 'sidebar_settings.PNG')
sidebar_volumn_up = os.path.join(sidebar_imgdir, 'sidebar_volumn_up.PNG')
sidebar_volumn_down = os.path.join(sidebar_imgdir, 'sidebar_volumn_down.PNG')


# Google Assistant thread
# 
# Note:
#   Google assistant managing thread

class AssistantThread(QThread):
    threadEvent = QtCore.pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.manager = AssistantManager()
    
    def run(self):
        while not dataManagerInitListener.isInitialized():
            continue

        self.manager.activate(self.acceptToken)

    def trigger(self):
        self.manager.assistantTrigger.trigger()
    
    def acceptToken(self, msg, token):
        if token is None:
            self.threadEvent.emit({
                'type': 'assistant_msg',
                'args': [msg if msg is not None else '음성을 입력하세요'],
            })
        else:
            self.threadEvent.emit({
                'type': token.name,
                'args': token.args,
            })


# Bluetooth thread
#
# Note:
#   Receives token from smartphone application and sends response token

class DeviceMetadata:
    def __init__(self) -> None:
        self.music_title = 'default'
        self.music_playing = 'false'
        self.current_volume = 'default'

class BluetoothThread(QThread):
    threadEvent = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.controller = BluetoothController()
        self.metadata = DeviceMetadata()
    
    def run(self):
        while True:
            self.controller.connect()
            while True:
                token = self.controller.receive()
                self.autoSend()
                if token is None:
                    break
                else:
                    sendToken = self.generateSendToken(ticket=token['ticket'], tokentype=token['type'])
                    self.controller.send(sendToken)
                    self.threadEvent.emit(token)
    
    def generateSendToken(self, ticket=-1, tokentype='init'):
        sendtoken = {
            'ticket': ticket,
            'type': tokentype,
        }

        sendtoken['args'] = [
            self.metadata.music_title,
            self.metadata.music_playing,
            self.metadata.current_volume
        ]

        return sendtoken

    def autoSend(self, tokentype='init'):
        sendtoken = self.generateSendToken(tokentype=tokentype)
        self.controller.send(sendtoken)


# Music Player Module
#
# Note:
#   Youtube music player module including manager and widget

class MusicPlayerModule(object):
    def __init__(self, parent=None, callbacks=[]) -> None:
        self.parent = parent
        self.manager = YouTubeMusicManager()

        self.widget = None
        self.manager.bindCallback(self.refresh)
        for method in callbacks:
            self.manager.bindCallback(method)
        self.title_widget = None
        self.play_button_widget = None
        self.play_button_signal_connected = False

        self.drawWindow()

    def disconnectPlayButtonSignal(self):
        if self.play_button_signal_connected:
            self.play_button_widget.clicked.disconnect()

    def drawWindow(self):
        self.widget = QGroupBox()
        
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        
        music_title = 'Music player'
        if self.manager.current_playlist is not None and self.manager.current_index is not None:
            music_title = self.manager.current_playlist[self.manager.current_index]['snippet']['title']
        
        self.title_widget = QLabel(music_title)
        self.title_widget.setStyleSheet(labelDefaultStyleSheet + 
            'color: white; font-size: 10pt; font-weight: bold; border-style: none;')
        title_layout = QHBoxLayout()
        title_layout.addStretch(1)
        title_layout.addWidget(self.title_widget)
        title_layout.addStretch(1)
        self.layout.addLayout(title_layout)
        self.layout.addStretch(1)

        self.play_button_widget = QPushButton()
        self.play_button_widget.setStyleSheet(f'border-style: none')
        self.disconnectPlayButtonSignal()
        if self.manager.isPlaying():
            self.play_button_widget.clicked.connect(self.manager.pause)
            self.play_button_widget.setIcon(QIcon(button_pause))
        else:
            self.play_button_widget.clicked.connect(self.manager.play)
            self.play_button_widget.setIcon(QIcon(button_play))
        self.play_button_signal_connected = True
        self.play_button_widget.setIconSize(QtCore.QSize(50, 50))

        next_button_widget = QPushButton()
        next_button_widget.setStyleSheet(f'border-style: none')
        next_button_widget.clicked.connect(self.manager.moveNext)
        next_button_widget.setIcon(QIcon(button_next))
        next_button_widget.setIconSize(QtCore.QSize(50, 50))

        prev_button_widget = QPushButton()
        prev_button_widget.setStyleSheet(f'border-style: none')
        prev_button_widget.clicked.connect(self.manager.movePrev)
        prev_button_widget.setIcon(QIcon(button_prev))
        prev_button_widget.setIconSize(QtCore.QSize(50, 50))

        button_layout = QHBoxLayout()
        button_layout.addWidget(prev_button_widget)
        button_layout.addStretch(1)
        button_layout.addWidget(self.play_button_widget)
        button_layout.addStretch(1)
        button_layout.addWidget(next_button_widget)
        self.layout.addLayout(button_layout)
        self.layout.addStretch(1)

        self.widget.setLayout(self.layout)

    def refresh(self):
        music_title = 'Music player'
        if self.manager.current_playlist is not None and self.manager.current_index is not None:
            music_title = self.manager.current_playlist[self.manager.current_index]['snippet']['title']
        self.title_widget.setText(music_title)

        self.disconnectPlayButtonSignal()
        if self.manager.isPlaying():
            self.play_button_widget.clicked.connect(self.manager.pause)
            self.play_button_widget.setIcon(QIcon(button_pause))
        else:
            self.play_button_widget.clicked.connect(self.manager.play)
            self.play_button_widget.setIcon(QIcon(button_play))
        self.play_button_signal_connected = True

    def currentMusicTitle(self):
        music_title = 'default'
        if self.manager.current_playlist is not None and self.manager.current_index is not None:
            music_title = self.manager.current_playlist[self.manager.current_index]['snippet']['title']
        return music_title


# Sidebar Module
#
# Note:
#   Manages sidebar widget of main window

class SidebarConfig:
    def __init__(self, name, icon_url, action_token) -> None:
        self.name = name
        self.icon_url = icon_url
        self.action_token = action_token

class SidebarActionToken:
    def __init__(self, name, args=[]) -> None:
        self.name = name
        self.args = args[:]

class SidebarModule:
    MODE_MAIN = 0
    MODE_SELECT = 1
    MODE_MUSIC = 2
    MODE_SETTINGS = 3

    configs = {
        MODE_MAIN: [
            SidebarConfig(name=0, icon_url=sidebar_settings, action_token=SidebarActionToken('settings')),
            SidebarConfig(name=1, icon_url=sidebar_music, action_token=SidebarActionToken('music')),
            SidebarConfig(name=2, icon_url=sidebar_assistant, action_token=SidebarActionToken('assistant')),
            SidebarConfig(name=3, icon_url=sidebar_select, action_token=SidebarActionToken('select')),
        ],
        MODE_SELECT: [
            SidebarConfig(name=0, icon_url=sidebar_expression, action_token=SidebarActionToken('play_music_by_emotion')),
            SidebarConfig(name=1, icon_url=sidebar_water, action_token=SidebarActionToken('moisture')),
            SidebarConfig(name=2, icon_url=sidebar_cloth, action_token=SidebarActionToken('style')),
            SidebarConfig(name=3, icon_url=sidebar_back, action_token=SidebarActionToken('back')),
        ],
        MODE_MUSIC: [
            SidebarConfig(name=0, icon_url=sidebar_play, action_token=SidebarActionToken('music_autoplay')),
            SidebarConfig(name=1, icon_url=sidebar_next, action_token=SidebarActionToken('music_next')),
            SidebarConfig(name=2, icon_url=sidebar_prev, action_token=SidebarActionToken('music_prev')),
            SidebarConfig(name=3, icon_url=sidebar_back, action_token=SidebarActionToken('back')),
        ],
        MODE_SETTINGS: [
            SidebarConfig(name=0, icon_url=sidebar_refresh, action_token=SidebarActionToken('refresh')),
            SidebarConfig(name=1, icon_url=sidebar_volumn_up, action_token=SidebarActionToken('master_volume_up')),
            SidebarConfig(name=2, icon_url=sidebar_volumn_down, action_token=SidebarActionToken('master_volume_down')),
            SidebarConfig(name=3, icon_url=sidebar_back, action_token=SidebarActionToken('back')),
        ],
    }

    def __init__(self, parent) -> None:
        self.mode = SidebarModule.MODE_MAIN
        self.parent = parent  # main GUI widget that includes this sidebar module (requires 'takeAction' method)
        self.widget = None
        self.buttons = []
        self.initWindow()

        self.hardwareButtonManager = ButtonManager()  # Hardware button trigger manager
        self.hardwareButtonManager.bind(ButtonManager.BUTTON0, self.trigger, 0)
        self.hardwareButtonManager.bind(ButtonManager.BUTTON1, self.trigger, 1)
        self.hardwareButtonManager.bind(ButtonManager.BUTTON2, self.trigger, 2)
        self.hardwareButtonManager.bind(ButtonManager.BUTTON3, self.trigger, 3)

    def initWindow(self):
        self.widget = QGroupBox()
        mainlayout = QVBoxLayout()
        mainlayout.addStretch(1)

        for idx in range(4):
            button = QPushButton()
            button.setStyleSheet(f'border-style: none')
            button.clicked.connect(functools.partial(self.trigger, idx))
            button.setIcon(QIcon(SidebarModule.configs[self.mode][idx].icon_url))
            button.setIconSize(QtCore.QSize(20, 20))
            self.buttons.append(button)

            mainlayout.addWidget(button)
            mainlayout.addStretch(1)

        self.widget.setLayout(mainlayout)

    def changeMode(self, nxt_mode):
        if nxt_mode not in SidebarModule.configs.keys():
            return
        if self.mode == nxt_mode:
            return
        
        for idx in range(4):
            self.buttons[idx].setIcon(QIcon(SidebarModule.configs[nxt_mode][idx].icon_url))
        
        self.mode = nxt_mode

    def trigger(self, idx):
        targetToken = SidebarModule.configs[self.mode][idx].action_token

        if targetToken.name == 'select':
            self.changeMode(SidebarModule.MODE_SELECT)
        elif targetToken.name == 'back':
            self.changeMode(SidebarModule.MODE_MAIN)
        elif targetToken.name == 'music':
            self.changeMode(SidebarModule.MODE_MUSIC)
        elif targetToken.name == 'settings':
            self.changeMode(SidebarModule.MODE_SETTINGS)

        self.parent.takeAction(token={
            'type': targetToken.name,
            'args': targetToken.args,
        })


class AlertDialog(QMessageBox):
    def __init__(self, title, msg, timeout=3, parent=None):
        super(AlertDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet('font-size: 10pt; color: white')
        self.time_to_wait = timeout
        self.msg = msg
        self.setText(f"{self.msg}\n({self.time_to_wait}초 뒤에 자동으로 창이 닫힙니다)")
        self.setStandardButtons(QMessageBox.NoButton)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()

    def changeContent(self):
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
            self.close()
        self.setText(f"{self.msg}\n({self.time_to_wait}초 뒤에 자동으로 창이 닫힙니다)")

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


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
        self.musicPlayerModule = MusicPlayerModule(callbacks=[self.autoSendMetadata])
        self.sidebarModule = SidebarModule(parent=self)
        self.moistureModule = MoistureManager()
        self.audioModule = AudioManager(callbacks=[self.autoSendMetadata])
        self.skinConditionUploader = SkinConditionUploader()
        self.styleRecommendationManager = StyleRecommendationManager()

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

        # Run bluetooth thread
        self.bluetoothThread = BluetoothThread()
        self.metadata = self.bluetoothThread.metadata
        self.setMetaData()
        self.bluetoothThread.start()
        self.bluetoothThread.threadEvent.connect(self.takeAction)

        # [TEST] Run assistant thread
        self.assistantThread = AssistantThread()
        self.assistantThread.start()
        self.assistantThread.threadEvent.connect(self.takeAction)
        self.assistantMsgLabel = QLabel('Google Assistant')
        self.assistantMsgLabel.setStyleSheet(labelDefaultStyleSheet + 
            'color: white; font-size: 11pt; font-weight: bold; border-style: none;')
        self.assistant_trigger_widget = QPushButton()
        self.assistant_trigger_widget.setStyleSheet(f'border-style: none')
        self.assistant_trigger_widget.clicked.connect(self.assistantThread.trigger)
        self.assistant_trigger_widget.setIcon(QIcon(assistant_logo))
        self.assistant_trigger_widget.setIconSize(QtCore.QSize(30, 30))

        # Generate main window layout and show that in full screen
        self.scheduleWidget = None     # schedule widget
        self.assistantWidget = None    # assistant widget
        self.weatherWidget = None      # weather widget
        self.calendarWidget = None     # calendar widget
        self.playerWidget = None       # youtube music player widget
        self.sidebarWidget = None      # sidebar widget
        self.progressbarWidget = None  # progressbar widget
        self.mainLayout = None
        self.drawWindow()  # generate main layout and set widget layout as main layout

        # self.showFullScreen()
        self.show()

    def drawWindow(self):
        # Required widget
        self.scheduleWidget = self.generateScheduleWidget()
        self.assistantWidget = self.generateAssistantWidget()
        self.weatherWidget = self.generateWeatherWidget()
        self.calendarWidget = self.generateCalenderWidget()
        self.playerWidget = self.generateMusicPlayerWidget()
        self.sidebarWidget = self.generateSidebarWidget()
        self.progressbarWidget = self.generateProgressbarWidget()

        # Generating layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.addWidget(self.dateTimeWidget)
        
        self.mainLayout.addStretch(1)

        sidebarLayout = QHBoxLayout()
        sidebarLayout.addStretch(1)
        sidebarLayout.addWidget(self.sidebarWidget)
        self.mainLayout.addLayout(sidebarLayout)

        self.mainLayout.addStretch(1)

        centerLayout = QHBoxLayout()
        centerLayout.addWidget(self.scheduleWidget)
        centerLayout.addStretch(1)
        centerLayout.addWidget(self.playerWidget)
        self.mainLayout.addLayout(centerLayout)

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.weatherWidget)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(self.calendarWidget)
        self.mainLayout.addLayout(bottomLayout)

        assistantLayout = QHBoxLayout()
        assistantLayout.addStretch(1)
        assistantLayout.addWidget(self.assistantWidget)
        assistantLayout.addStretch(1)
        self.mainLayout.addLayout(assistantLayout)

        self.mainLayout.addWidget(self.progressbarWidget)

        self.setLayout(self.mainLayout)

    def showTime(self):
        currentTime = QTime.currentTime().toString('hh:mm')
        currentDate = QDate.currentDate().toString('yyyy-MM-dd dddd')
        self.dateTimeWidget.setText(f'{currentDate} {currentTime}')  # change timeWidget

        refreshTerm = getSettings('refresh_term')
        if (self.refreshedTime.secsTo(QTime.currentTime()) // 60) >= refreshTerm:
            self.refresh()

    def generateProgressbarWidget(self):
        barWidget = QProgressBar()
        barWidget.setLayoutDirection(Qt.LeftToRight)
        barWidget.setStyleSheet("QProgressBar{\n"
                                "    background-color: rgb(98, 114, 164);\n"
                                "    color:rgb(200,200,200);\n"
                                "    border-style: none;\n"
                                "    border-bottom-right-radius: 10px;\n"
                                "    border-bottom-left-radius: 10px;\n"
                                "    border-top-right-radius: 10px;\n"
                                "    border-top-left-radius: 10px;\n"
                                "    text-align: center;\n"
                                "}\n"
                                "QProgressBar::chunk{\n"
                                "    border-bottom-right-radius: 10px;\n"
                                "    border-bottom-left-radius: 10px;\n"
                                "    border-top-right-radius: 10px;\n"
                                "    border-top-left-radius: 10px;\n"
                                "    background-color: qlineargradient(spread:pad, x1:0, y1:0.511364, x2:1, y2:0.523, stop:0 rgba(254, 121, 199, 255), stop:1 rgba(170, 85, 255, 255));\n"
                                "}\n"
                                "\n"
                                "")
        return barWidget

    def generateMusicPlayerWidget(self):
        groupbox = self.musicPlayerModule.widget
        groupbox.setFixedWidth(190)
        groupbox.setStyleSheet(widgetDefaultStyleSheet)

        return groupbox

    def generateSidebarWidget(self):
        groupbox = self.sidebarModule.widget
        groupbox.setFixedHeight(120)
        groupbox.setStyleSheet(widgetDefaultStyleSheet)

        return groupbox

    def generateAssistantWidget(self):
        groupbox = QGroupBox()
        groupbox.setFixedWidth(440)
        groupbox.setStyleSheet(widgetDefaultStyleSheet)

        vbox = QVBoxLayout()
        vbox.addStretch(1)

        hbox = QHBoxLayout()
        # hbox.addStretch(1)
        hbox.addWidget(self.assistant_trigger_widget)
        hbox.addWidget(self.assistantMsgLabel)
        hbox.addStretch(1)
        
        vbox.addLayout(hbox)
        vbox.addStretch(1)
        groupbox.setLayout(vbox)

        return groupbox
        
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

    def setMetaData(self):
        self.metadata.music_title = self.musicPlayerModule.currentMusicTitle()
        self.metadata.music_playing = 'true' if self.musicPlayerModule.manager.isPlaying() else 'false'
        self.metadata.current_volume = str(self.audioModule.current_volume)
    
    def autoSendMetadata(self):
        self.setMetaData()
        self.bluetoothThread.autoSend()

    @QtCore.pyqtSlot(dict)
    def takeThreadAction(self, token):
        self.takeAction(token)

    def takeAction(self, token):
        if token['type'] == 'set_location':
            changeSettings('lat', token['args'][0])
            changeSettings('lon', token['args'][1])
            saveSettings()
            self.weatherDownloader.refreshLocation()
            self.refresh()
        
        elif token['type'] == 'refresh':
            self.refresh()

        elif token['type'] == 'refresh_assistant':
            self.refresh()
            self.assistantMsgLabel.setText(token['args'][0])

        elif token['type'] == 'set_auto_interval':
            changeSettings('refresh_term', token['args'][0])
            self.refresh()

        elif token['type'] == 'music_autoplay':
            if not self.musicPlayerModule.manager.isInvalid():
                if not self.musicPlayerModule.manager.isStopped():
                    self.musicPlayerModule.manager.pause()
                else:
                    self.musicPlayerModule.manager.play()
        
        elif token['type'] == 'music_next':
            if not self.musicPlayerModule.manager.isInvalid():
                self.musicPlayerModule.manager.moveNext()
        
        elif token['type'] == 'music_prev':
            if not self.musicPlayerModule.manager.isInvalid():
                self.musicPlayerModule.manager.movePrev()

        elif token['type'] == 'play_music_by_keyword':
            if not self.musicPlayerModule.manager.isStopped():
                self.musicPlayerModule.manager.pause()
            self.musicPlayerModule.manager.search(token['args'][1])
            self.musicPlayerModule.manager.play()
            self.assistantMsgLabel.setText(token['args'][0])

        elif token['type'] == 'play_music_by_emotion':
            alertDialog = AlertDialog(title='표정 분석', msg='표정 분석을 위해 얼굴을 비추세요', timeout=3, parent=self)
            alertDialog.exec_()

            if not self.musicPlayerModule.manager.isStopped():
                self.musicPlayerModule.manager.pause()
            result_valid = self.musicPlayerModule.manager.searchByEmotion()
            msg = "표정 분석에 실패했습니다"

            if result_valid:
                self.musicPlayerModule.manager.play()
                msg=f"현재 감정 상태: {result_valid}\n적절한 음악을 재생합니다"
            
            alertDialog = AlertDialog(title='표정 분석', msg=msg, timeout=5, parent=self)
            alertDialog.exec_()

        elif token['type'] == 'moisture':
            msg = ""
            measured_results = []
            error_flag = False
            median_value = -1

            alertDialog = AlertDialog(title='피부 상태 분석', msg='피부 상태 분석을 위해 센서를 피부와 접촉하세요', timeout=3, parent=self)
            alertDialog.exec_()

            try:
                measured_results = self.moistureModule.measure(max_cnt=7, time_interval=0.5)
                measured_results.sort()
                median_value = measured_results[len(measured_results) // 2]
                msg = f"측정된 결과는 다음과 같습니다: {median_value}"
                if len(measured_results) < 4:
                    msg += '\n경고: 결과값이 부족하여 측정된 결과가 정확하지 않을 수 있습니다.'
            except:
                msg = "측정 중 심각한 오류가 발생하였습니다.\n센서가 제대로 동작하고 있는지 확인하세요."
                error_flag = True

            alertDialog = AlertDialog(title='피부 수분측정', msg=msg, timeout=5, parent=self)
            alertDialog.exec_()

            if median_value != -1 and not error_flag:  # Upload to google drive storage
                self.skinConditionUploader.upload(median_value, datetime.date.today())

        elif token['type'] == 'style':
            msg = ""
            results = None

            alertDialog = AlertDialog(title='스타일 분석', msg='스타일 분석을 위해 전신을 비추세요\n창이 닫히면 스타일을 특정합니다', timeout=5, parent=self)
            alertDialog.exec_()
            try:
                self.styleRecommendationManager.capture()
                results = self.styleRecommendationManager.search()
                self.styleRecommendationManager.upload(targetData=results)
                msg = "분석 결과를 스마트폰을 통해 확인하세요"
            except:
                msg = "분석 중 심각한 오류가 발생하였습니다.\n카메라가 제대로 동작하고 있는지 확인하세요."

            alertDialog = AlertDialog(title='스타일 분석', msg=msg, timeout=5, parent=self)
            alertDialog.exec_()

            print(results)
        
        elif token['type'] == 'assistant':
            self.assistantThread.trigger()

        elif token['type'] == 'assistant_msg':
            self.assistantMsgLabel.setText(token['args'][0])

        elif token['type'] == 'master_volume_up':
            self.audioModule.volumnUp()

        elif token['type'] == 'master_volume_down':
            self.audioModule.volumnDown()

        elif token['type'] == 'vlc_volume_up':
            self.musicPlayerModule.manager.volumnUp()

        elif token['type'] == 'vlc_volume_down':
            self.musicPlayerModule.manager.volumeDown()


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