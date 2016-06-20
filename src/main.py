# reference
# http://blog.lekermeur.net/?p=2052
# https://github.com/xxv/tracer/blob/master/arduino/Tracer/Tracer.ino

import serial
import time
import requests
import os
import logging
import RPi.GPIO as GPIO
import ConfigParser

relay_pin = 18

this_dir_path = os.path.dirname(os.path.realpath(__file__))

def hex_2byte_to_int(hex_2byte):
  return int(hex_2byte[1].encode('hex') + hex_2byte[0].encode('hex'), 16)

# read config
config = ConfigParser.ConfigParser()
config.readfp(open(this_dir_path + '/power_plant.cfg'))

# log setting
# https://zonca.github.io/2013/10/how-to-log-exceptions-in-python.html
log_dir_path = this_dir_path + '/../log'
log_file_path = log_dir_path + '/error.log' 

if not os.path.exists(log_dir_path):
  os.mkdir(log_dir_path)

def log_exception(e):
  logging.error(
    "raised {expection_class} ({expection_docstring}): {expection_message}".format(
        expection_class     = e.__class__,
        expection_docstring = e.__doc__,
        expection_message   = e.message
      )
    )

logging.basicConfig(
  filename=log_file_path,
  # filemode='a', # default a
  level=logging.ERROR,
  format='%(asctime)s - %(levelname)s - %(message)s'
)

# gpio settind
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, False)

# tracer command setting
tracer_start_command = "\xAA\x55\xAA\x55\xAA\x55\xEB\x90\xEB\x90\xEB\x90"
tracer_id = "\x16"
tracer_kind_command = "\xA0\x00\xB1\xA7\x7F"

tracer_command_to_send = tracer_start_command + tracer_id + tracer_kind_command

# serial port setting
port = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=1.0)
port.open()
time.sleep(1)
port.flushInput()
port.flushOutput()

while (1):
#for run_time_count in [1]:
  panel_volt_sum            = 0
  battery_charge_ampere_sum = 0
  battery_volt_sum          = 0

  # get average of 6 time in 1 min
  for i_per_10sec in range(6):
    port.write(tracer_command_to_send)
    #print 'send: ' + tracer_command_to_send.encode('hex')

    #port.flush()
    data = port.read(100)
    #print 'received: ' + data.encode('hex')
    #print ''

    #print 'syncro: '  + data[0:6].encode('hex')
    #print 'address: ' + data[6].encode('hex')
    #print 'command: ' + data[7].encode('hex')
    length = int(data[8].encode('hex'), 16)
    #print 'length: '  + data[8].encode('hex') + '(' + str(length) + ')'
    info = data[9:9+length]
    #print 'info: '  + info.encode('hex')
    #print 'crc16: ' + data[9+length:11+length].encode('hex')
    #print 'end: '   + data[11+length].encode('hex')

    #print ''
    battery_volt = hex_2byte_to_int(info[0:2])
    #print 'battery_volt: ' + str(battery_volt)
    panel_volt = hex_2byte_to_int(info[2:4])
    #print 'panel_volt: ' + str(panel_volt)
    #print 'reserved: ' + str(hex_2byte_to_int(info[4:6]))
    #out_ampere = hex_2byte_to_int(info[6:8])
    #print 'out_ampere: ' + str(out_ampere)
    #out_volt = hex_2byte_to_int(info[8:10])
    #print 'out_volt: ' + str(out_volt)
    #batt_full_volt = hex_2byte_to_int(info[10:12])
    #print 'batt_full_volt: ' + str(batt_full_volt)
    #print 'outputting?: ' + info[12].encode('hex')
    #print 'over_output?: ' + info[13].encode('hex')
    #print 'loading_to_circuit?: ' + info[14].encode('hex')
    #print 'reserved: ' + info[15].encode('hex')
    #print 'is_overloaded_battery?: ' + info[16].encode('hex')
    #print 'is_overdischarged_battery?: ' + info[17].encode('hex')
    #print 'is_full?: ' + info[18].encode('hex')
    is_charging = int(info[19].encode('hex'), 16)
    #print 'is_charging?: ' + str(is_charging)
    #print 'battery_temp: ' + str(int(info[20].encode('hex'), 16) -30)
    battery_charge_ampere = hex_2byte_to_int(info[21:23])
    #print 'charge_ampere: ' + str(battery_charge_ampere)
    #print 'reserved: ' + info[23].encode('hex')

    #print is_charging
    #print float(battery_volt) / 100
    #print float(panel_volt) / 100
    #print float(charge_ampere) / 100
    #print ''
    panel_volt_sum            += float(panel_volt)            / 100
    battery_charge_ampere_sum += float(battery_charge_ampere) / 100
    battery_volt_sum          += float(battery_volt)          / 100
    time.sleep(10)

  panel_volt_to_send            = panel_volt_sum            / 6
  battery_charge_ampere_to_send = battery_charge_ampere_sum / 6
  battery_volt_to_send          = battery_volt_sum          / 6
  charged_watt_to_send          = battery_volt_to_send * battery_charge_ampere_to_send

  # solalog staging
  try:
    r = requests.post('http://staging.solalog.link/api/v1/power_log',
      auth = (config.get('default', 'solalog_staging_auth_id'), config.get('default', 'solalog_staging_auth_pass')),
      data = {
        'voltage' : battery_volt_to_send,
        'ampere'  : battery_charge_ampere_to_send,
        'api_key' : config.get('default', 'solalog_staging_api_key'),
      },
      timeout=10)
    print r.text
  except Exception as e:
    log_exception(e)
    pass

  # for thingspeak
  try:
    r = requests.post('https://api.thingspeak.com/update.json',
      data = {
        'field1'  : panel_volt_to_send,
        'field2'  : battery_charge_ampere_to_send,
        'field3'  : battery_volt_to_send,
        'field4'  : charged_watt_to_send,
        'api_key' : config.get('default', 'thing_speak_api_key'),
      },
      timeout=10)
    print r.text
  except Exception as e:
    log_exception(e)
    pass

  # for solalog
  try:
    r = requests.post('http://solalog.link/api/v1/power_log',
      data = {
        'voltage' : battery_volt_to_send,
        'ampere'  : battery_charge_ampere_to_send,
        'api_key' : config.get('default', 'solalog_api_key'),
      },
      timeout=10)
    print r.text
  except Exception as e:
    log_exception(e)
    pass

  # update relay connected to gpio
  if ( battery_volt_to_send > 25.4 ) or \
     ( ( charged_watt_to_send > 50 ) and ( battery_volt_to_send > 24.7 ) ) :
    GPIO.output(relay_pin, True)
  else :
    GPIO.output(relay_pin, False)
