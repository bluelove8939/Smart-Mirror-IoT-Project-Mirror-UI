import logging
import time

# I2C driver
import moisture_driver

# Alsa audio mixer
import alsaaudio


# Moisture manager
# 
# Note:
#   Manages moisture sensor with I2C driver

class MoistureManager:
    def __init__(self):
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


class ButtonManager:
    def __init__(self):
        pass


class AudioManager:
    def __init__(self) -> None:
        self.mixer = alsaaudio.Mixer()
        self.mixer.setvolume(70)
        self.current_volume = self.mixer.getvolume()

    def volumnUp(self):
        self.mixer.setvolume(int(self.current_volume[0]) + 10)
        self.current_volume = self.mixer.getvolume()

    def volumnDown(self):
        self.mixer.setvolume(int(self.current_volume[0]) - 10)
        self.current_volume = self.mixer.getvolume()


# Testbench code for moisture manager
if __name__ == "__main__":
    manager = MoistureManager()
    print(manager.measure())
        
