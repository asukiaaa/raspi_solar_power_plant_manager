# raspi_solar_power_plant_manager
Package to manage a solar power plant by raspberry pi with Tracer2210RN and thingspeak.

# Hardware setting
## Components
This system uses the following components.
- Raspberry pi (which connected to Internet)
- Power charge controller (I use Tracer2210RN)
- Relay (to use surplus power)

## Connection
- raspi rx <-> Power charge controller tx
- raspi tx <-> Power charge controller rx
- raspi GND <-> Power charge controller GND
- raspi 18 pin <-> Relay trigger

# Useage
## Requirements
- python-smbus

## Download
```
mkdir ~/gitprojects
cd ~/gitprojects
git clone git@github.com:asukiaaa/raspi_solar_power_plant_manager.git
```

## Create your config file for logging with using thingspeak
If you want to create log for power status, you can do it with using [thingspeak](https://thingspeak.com/).

```
cd ~/gitprojects/raspi_solar_power_plant_manager/src
cp power_plant.cfg_example power_plant.cfg
```

## Run Manually
```
cd ~/gitprojects/raspi_solar_power_plant_manager/src
sudo python src/main.py
```

## Check error log
```
tail -f ~/gitprojects/raspi_solar_power_plant_manager/log/error.log
```

## Auto run setting
```
sudo crontab -e
```


Add a job after reboot with absolute path.
```
@reboot python /home/pi/gitprojects/raspi_solar_power_plant_manager/src/main.py &
```

# License
MIT

# References
- http://blog.lekermeur.net/?p=2052
- https://github.com/xxv/tracer/blob/master/arduino/Tracer/Tracer.ino
