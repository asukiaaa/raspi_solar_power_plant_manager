import serial
import time
import requests
import os
import logging
import RPi.GPIO as GPIO
import ConfigParser
import tracer_charge_controller
import ina226_controller

this_dir_path = os.path.dirname(os.path.realpath(__file__))

relay_pin = 18

# get average of 6 time in 1 min
loop_num_to_get_average = 6
loop_interval_sec = 10

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

# gpio setting
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, False)

# charge controller setting
charge_controller = tracer_charge_controller.TracerChargeController("/dev/ttyAMA0")

# using power sensor setting
try:
  direct_use_power_sensor = ina226_controller.Ina226Controller(1, int(config.get('default', 'direct_use_power_sensor_address'), 16))
except Exception as e:
  log_exception(e)
  direct_use_power_sensor = ""
  pass

is_battery_full = False

while (1):
#for run_time_count in [1]:
  panel_volt_sum            = 0
  battery_charge_ampere_sum = 0
  battery_volt_sum          = 0
  direct_use_ampere_sum     = 0
  direct_use_volt_sum       = 0

  for i_per_10sec in range(loop_num_to_get_average):
    if direct_use_power_sensor != "":
      direct_use_ampere_sum  += direct_use_power_sensor.get_ampere()
      direct_use_volt_sum    += direct_use_power_sensor.get_voltage()

    charge_controller.update_status()
    # charge_controller.print_status()
    panel_volt_sum            += charge_controller.panel_volt()
    battery_charge_ampere_sum += charge_controller.battery_charge_ampere()
    battery_volt_sum          += charge_controller.battery_volt()
    time.sleep(loop_interval_sec)

  panel_volt_to_send            = panel_volt_sum            / loop_num_to_get_average
  battery_charge_ampere_to_send = battery_charge_ampere_sum / loop_num_to_get_average
  battery_volt_to_send          = battery_volt_sum          / loop_num_to_get_average
  charged_watt_to_send          = battery_volt_to_send * battery_charge_ampere_to_send
  direct_use_ampere_to_send     = direct_use_ampere_sum     / loop_num_to_get_average
  direct_use_volt_to_send       = direct_use_volt_sum       / loop_num_to_get_average
  direct_use_watt_to_send       = direct_use_ampere_to_send * direct_use_volt_to_send

  # for thingspeak charge channel
  try:
    r = requests.post('https://api.thingspeak.com/update.json',
      data = {
        'field1'  : panel_volt_to_send,
        'field2'  : battery_charge_ampere_to_send,
        'field3'  : battery_volt_to_send,
        'field4'  : charged_watt_to_send,
        'api_key' : config.get('default', 'thingspeak_charge_channel_api_key'),
      },
      timeout=10)
    print r.text
  except Exception as e:
    log_exception(e)
    pass

  # for thingspeak consumed power channel
  data_to_send = {}
  if direct_use_power_sensor != "":
    data_to_send['field1'] = direct_use_ampere_to_send
    data_to_send['field2'] = direct_use_volt_to_send
    data_to_send['field3'] = direct_use_watt_to_send

  if data_to_send != {}:
    try:
      data_to_send['api_key'] = config.get('default', 'thingspeak_consumed_power_channel_api_key')
      r = requests.post('https://api.thingspeak.com/update.json',
        data = data_to_send,
        timeout=10)
      print r.text
    except Exception as e:
      log_exception(e)
      pass

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

  # update connected relay status
  if ( battery_volt_to_send > 25.6 ) :
    is_battery_full = True
  if ( is_battery_full ) :
    # if ( charged_watt_to_send < 20 and battery_volt_to_send < 25.3 ) :
    #   is_battery_full = False
    if ( battery_volt_to_send < 24.5 ) :
      is_battery_full = False

  if ( is_battery_full ):
    GPIO.output(relay_pin, True)
  else :
    GPIO.output(relay_pin, False)
