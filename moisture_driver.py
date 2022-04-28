import logging


# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2CBUS = 1

# LCD Address
ADDRESS = 0x2A

# commands                      
FDC2214_DEVICE_ID = 0x7F
FDC2214_MUX_CONFIG = 0x1B
#-------------------------------
FDC2214_CONFIG = 0x1A
FDC2214_RCOUNT_CH0 = 0x08
FDC2214_OFFSET_CH0 = 0x0C         			
FDC2214_SETTLECOUNT_CH0 = 0x10    		
FDC2214_CLOCK_DIVIDERS_CH0 = 0x14 	   	
FDC2214_DRIVE_CH0 = 0x1e     
#-------------------------------
FDC2214_STATUS = 0x18
FDC2214_DATA_CH0_MSB = 0x00


#mask for 28bit data to filter out flag bits
FDC2214_DATA_CHx_MASK_DATA = 0x0FFF

FDC2214_DATA_CHx_MASK_ERRAW = 0x1000  
FDC2214_DATA_CHx_MASK_ERRWD = 0x2000

#bitmasks
FDC2214_CH0_UNREADCONV = 0x0008         
FDC2214_CH1_UNREADCONV = 0x0004         
FDC2214_CH2_UNREADCONV = 0x0002         
FDC2214_CH3_UNREADCONV = 0x0001      

import smbus2 as smbus
from time import sleep

class i2c_moisture:
   def __init__(self, addr=ADDRESS, port=I2CBUS):           
      self.addr = addr
      self.bus = smbus.SMBus(port)
      sleep(0.0001)

      #init register
      try:
         self.write_word(FDC2214_CONFIG, 0x0114)   
         self.write_word(FDC2214_SETTLECOUNT_CH0, 0xffff)
         self.write_word(FDC2214_RCOUNT_CH0, 0x2983)
         self.write_word(FDC2214_OFFSET_CH0, 0x0200)
         self.write_word(FDC2214_CLOCK_DIVIDERS_CH0, 0x0a20)  ####point
         self.write_word(FDC2214_DRIVE_CH0, 0x00F8)
         self.write_word(FDC2214_MUX_CONFIG, 0x0d02)
      except:
         logging.error('[I2C DRIVER] Error ocurred on initliazing driver')
         raise Exception()

   # Write a command and argument
   def write_word(self, cmd, data):
      try:
         self.bus.write_word_data(self.addr, cmd, data)                     #1바이트 쓰기   ex Bus.write_byte_data(0x68, 0x01, 0x07)   -> 1워드 쓰기로 수정
         sleep(0.0001)
      except:
         logging.error('[I2C DRIVER] Error ocurred on write word operation')
         raise Exception()

   # Write a block of data
   def write_block_data(self, cmd, data):
      try:
         self.bus.write_i2c_block_data(self.addr, cmd, data)                   #여러 블록(byte)쓰기   ex Bus.write_i2c_block_data(0x68, 0x00, [0, 1, 2, 3, 4, 5])
         sleep(0.0001)
      except:
         logging.error('[I2C DRIVER] Error ocurred on write block data operation')
         raise Exception()

   # Read
   def read_word(self, cmd):
      try:
         return self.bus.read_word_data(self.addr, cmd)                    # 1바이트 읽기 ex  Bus.read_byte_data (0x68, 0x01)   ->1워드 읽기로 수정
      except:
         logging.error('[I2C DRIVER] Error ocurred on read word operation')
         raise Exception()

   # Read a block of data
   def read_block_data(self, cmd, block_of_bytes):
      try:
         return self.bus.read_i2c_block_data(self.addr, cmd, block_of_bytes)           # 여러 블록 읽기 ex)  Bus.read_i2c_block_data(0x68, 0x00, 8)
      except:
         logging.error('[I2C DRIVER] Error ocurred on read block data operation')
         raise Exception()


        
