# reference
# http://blog.lekermeur.net/?p=2052
# https://github.com/xxv/tracer/blob/master/arduino/Tracer/Tracer.ino

import serial
import time

class TracerChargeController:
  # tracer command setting
  tracer_start_command = "\xAA\x55\xAA\x55\xAA\x55\xEB\x90\xEB\x90\xEB\x90"
  tracer_id = "\x16"
  tracer_kind_command = "\xA0\x00\xB1\xA7\x7F"
  tracer_command_to_send = tracer_start_command + tracer_id + tracer_kind_command

  port = ''
  data = ''
  info = ''
  info_length = 0

  def __init__(self, serial_path, baudrate = 9600, timeout = 1.0):
    # serial port setting
    self.port = serial.Serial(serial_path, baudrate=baudrate, timeout=timeout)
    self.port.open()
    time.sleep(1)
    self.port.flushInput()
    self.port.flushOutput()

  def __exit__(self):
    self.port.close()

  def update_status(self):
    self.port.write(self.tracer_command_to_send)
    #print 'send: ' + tracer_command_to_send.encode('hex')

    #self.port.flush()
    self.data = self.port.read(100)
    self.info_length = int(self.data[8].encode('hex'), 16)
    self.info = self.data[9:9+self.info_length]

  def print_status(self):
    print 'received: ' + self.data.encode('hex')
    print ''

    print 'syncro: '  + self.data[0:6].encode('hex')
    print 'address: ' + self.data[6].encode('hex')
    print 'command: ' + self.data[7].encode('hex')
    print 'length: '  + str(self.info_length) + '(' + self.data[8].encode('hex') + ')'
    print 'info: '    + self.info.encode('hex')
    print 'crc16: '   + self.data[9+self.info_length:11+self.info_length].encode('hex')
    print 'end: '     + self.data[11+self.info_length].encode('hex')

    print ''
    print 'battery_volt: '   + str(self.battery_volt())
    print 'panel_volt: '     + str(self.panel_volt())
    print 'reserved: '       + self.info[4:6].encode('hex')
    print 'out_ampere: '     + str(self.out_ampere())
    print 'out_volt: '       + str(self.out_volt())
    print 'batt_full_volt: ' + str(self.batt_full_volt())
    print 'outputting?: '    + self.info[12].encode('hex')
    print 'over_output?: '   + self.info[13].encode('hex')
    print 'is_outputting?: ' + self.info[14].encode('hex')
    print 'reserved: '       + self.info[15].encode('hex')

    print 'is_overloaded_battery?: '     + self.info[16].encode('hex')
    print 'is_overdischarged_battery?: ' + self.info[17].encode('hex')
    print 'is_full?: '      + self.info[18].encode('hex')
    print 'is_charging?: '  + str(self.is_charging())
    print 'battery_temp: '  + str(self.battery_temp())
    print 'charge_ampere: ' + str(self.battery_charge_ampere())
    print 'reserved: '      + self.info[23].encode('hex')

  def hex_2bytes_to_int(self, hex_2byte):
    return int(hex_2byte[1].encode('hex') + hex_2byte[0].encode('hex'), 16)

  def info_2bytes_to_float(self, start, divide):
    return float( self.hex_2bytes_to_int( self.info[int(start) : int(start) + 2] ) ) / divide

  def battery_volt(self):
    return self.info_2bytes_to_float(0, 100)

  def panel_volt(self):
    return self.info_2bytes_to_float(2, 100)

  def out_ampere(self):
    return self.info_2bytes_to_float(6, 100)

  def out_volt(self):
    return self.info_2bytes_to_float(8, 100)

  def batt_full_volt(self):
    return self.info_2bytes_to_float(10, 100)

  def is_charging(self):
    return int(self.info[19].encode('hex'), 16)

  def battery_temp(self):
    return int(self.info[20].encode('hex'), 16) -30

  def battery_charge_ampere(self):
    return self.info_2bytes_to_float(21, 100)
