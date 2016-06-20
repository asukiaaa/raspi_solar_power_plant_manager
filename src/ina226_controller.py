# References
# https://www.raspberrypi.org/forums/viewtopic.php?f=44&t=36049
# http://usepocket.com/c/UP552.html
# http://www.acmesystems.it/i2c
# http://strawberry-linux.com/pub/ina226.pdf

import smbus
import time

class Ina226Controller:
  i2c = ''
  address = ''

  def __init__(self, bus_num, address):
    self.address = address
    self.i2c = smbus.SMBus(bus_num)
    # set milli ampere mode
    self.i2c.write_i2c_block_data( self.address, 0x05, [0x0a, 0x00] )

  def get_ampere(self):
    block_data = self.i2c.read_i2c_block_data( self.address, 0x04 )
    raw_ampere = block_data[0]*256 + block_data[1]
    if block_data[0] < 128 :
      return float(raw_ampere) / 1000
    else :
      return float(raw_ampere - 256*256) / 1000

  def get_voltage(self):
    block_data = self.i2c.read_i2c_block_data( self.address, 0x02 )
    return float( block_data[0]*256 + block_data[1] ) * 1.25 / 1000
