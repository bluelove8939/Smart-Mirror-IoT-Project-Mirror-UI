import logging
import time
import json
import RPi.GPIO as GPIO

# Alsa audio mixer
import alsaaudio


# Read device configuration
configurations = {
    "skin-condition-enabled": False,
    "hardware-button-enabled": False,
}

try:
    with open('config.json', 'rt') as config:
        content = json.loads(config.read())
        for k, v in content.items():
            configurations[k] = v
except Exception as error:
    logging.warning(f'[DATA MANAGER] config.json not found: {error}')

# I2C driver
if configurations['skin-condition-enabled']:
    import moisture_driver


# Moisture manager
# 
# Note:
#   Manages moisture sensor with I2C driver

class MoistureManager:
    def __init__(self):
        if not configurations['skin-condition-enabled']:
            self.isvalid = False
            return

        self.isvalid = True
        try:
            self.moisture = moisture_driver.i2c_moisture()
        except:
            logging.error('[MOISTURE] Error ocurred on initializing I2C driver')
            self.isvalid = False

    def measure(self, time_interval = 0.1, max_cnt = 7, tolerance = 50):
        if not self.isvalid:
            logging.error('[MOISTURE] Manager is not valid')
            return []

        results = []
        status = (self.moisture.read_word(0x18) & 0x0800)
        cnt_iter = 0
        cnt = 0

        try:
            while cnt < max_cnt:
                if status:
                    water = self.moisture.read_word(0x00)
                    water = water & 0xFF0F
                    masked_water1=(water&0x0F)<<12
                    masked_water2=(water>>4)
                    final_water=(masked_water1 | masked_water2)>>4
                    
                    results.append(100-int(final_water))
                    time.sleep(time_interval)
                    
                    while not status:
                        status = (self.moisture.read_word(0x18) & 0x0800)
                        time.sleep(time_interval)
                        cnt_iter += 1

                        if cnt_iter > tolerance:
                            logging.error('[SKIN MOISTURE] Error ocurred: exceeds tolerance on measuring skin moisture (value may not valid)')
                            return results
                        
                    cnt += 1
        except:
            logging.error('[SKIN MOISTURE] Fatal error ocurred on measuring skin moisture')
            results = []

        return results


# Button manager
#
# Note:
#   Manages button callbacks
#
# Description:
#   Uses GPIO pin of raspberry pi4 for button input
#   It uses 7, 11, 13, 15 pin by default

class ButtonManager:
    BUTTON0 = 7   # pin number 7  is assigned as button0
    BUTTON1 = 11  # pin number 11 is assigned as button1
    BUTTON2 = 13  # pin number 13 is assigned as button2
    BUTTON3 = 15  # pin number 15 is assigned as button3
    BUTTON_TYPES = (BUTTON0, BUTTON1, BUTTON2, BUTTON3,)

    def __init__(self):
        self.isvalid = True

        if not configurations['hardware-button-enabled']:
            self.isvalid = False
            return

        self._pin_callback_mappings = {
            ButtonManager.BUTTON0: (self.defaultCallback, (ButtonManager.BUTTON0,)),
            ButtonManager.BUTTON1: (self.defaultCallback, (ButtonManager.BUTTON1,)),
            ButtonManager.BUTTON2: (self.defaultCallback, (ButtonManager.BUTTON2,)),
            ButtonManager.BUTTON3: (self.defaultCallback, (ButtonManager.BUTTON3,)),
        }

        self.initGPIO()

    def initGPIO(self):
        if not self.isvalid:
            return

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        for pinnum in self._pin_callback_mappings.keys():
            GPIO.setup(pinnum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(pinnum, GPIO.RISING, callback=self.buttonCallback, bouncetime=300)

    def bind(self, pinnum, method, *args):
        if not self.isvalid:
            return

        self._pin_callback_mappings[pinnum] = (method, args)

    def remove(self, pinnum):
        if not self.isvalid:
            return

        self._pin_callback_mappings[pinnum] = (self.defaultCallback, (pinnum,))

    def defaultCallback(self, *args):
        logging.info(f"[BUTTON MANAGER] Default callback called: args({args})")

    def buttonCallback(self, channel):
        for button_idx, pinnum in enumerate(ButtonManager.BUTTON_TYPES):
            if GPIO.input(pinnum) == 1:
                method, args = self._pin_callback_mappings[pinnum]
                method(*args)
                break


class AudioManager:
    def __init__(self) -> None:
        self.mixer = alsaaudio.Mixer()
        self.mixer.setvolume(70)
        self.current_volume = self.mixer.getvolume()[0]
        self.callbacks = []

    def bind(self, method, *args):
        self.callbacks.append((method, args))

    def volumnUp(self):
        self.mixer.setvolume(min(int(self.current_volume) + 10, 100))
        self.current_volume = self.mixer.getvolume()[0]
        for method, args in self.callbacks:
            method(*args)

    def volumnDown(self):
        self.mixer.setvolume(max(int(self.current_volume) - 10, 0))
        self.current_volume = self.mixer.getvolume()[0]
        for method, args in self.callbacks:
            method(*args)


# # Testbench code for moisture manager
# if __name__ == "__main__":
#     manager = MoistureManager()
#     print(manager.measure())
        
