![Enviro Plus pHAT](https://raw.githubusercontent.com/pimoroni/enviroplus-python/main/Enviro-Plus-pHAT.jpg)
![Enviro Mini pHAT](https://raw.githubusercontent.com/pimoroni/enviroplus-python/main/Enviro-mini-pHAT.jpg)

# Installing
:warning: This library now supports Python 3 only

Follow Standard Pimoroni Install instructions.

## Install and configure dependencies from GitHub:

* `git clone https://github.com/pimoroni/enviroplus-python` or `git clone https://github.com/kurayamin0/enviroplus-python`
* `cd enviroplus-python`
* `./install.sh`

**Note** Libraries will be installed in the "pimoroni" virtual environment, you will need to activate it to run examples:

```
source ~/.virtualenvs/pimoroni/bin/activate
```

**Note** this will not perform any of the required configuration changes on your Pi, you may additionally need to:
```
* Enable i2c: `raspi-config nonint do_i2c 0`
* Enable SPI: `raspi-config nonint do_spi 0`
```

And if you're using a PMS5003 sensor you will need to:

### Bookworm

* Enable serial: `raspi-config nonint do_serial_hw 0`
* Disable serial terminal: `raspi-config nonint do_serial_cons 1`
* Add `dtoverlay=pi3-miniuart-bt` to your `/boot/firmware/config.txt`

### Autorun

* Firstly create a new service. `sudo nano /etc/systemd/system/<servicename>.service` This creates a service called  whatever you wish to name the service to auto run your script.

* In this .service file you will need to add some details about the service. Below is a template, but you will need to    change the directories etc as required.

```
[Unit]
Description=<Whatever you want to call the service eg enviroplus with virtual env>
After=network.target

[Service]
User=<username>
Group=<group> 
WorkingDirectory=/home/<username>/enviroplus-python/examples/
ExecStart=/home/<username>/.virtualenvs/pimoroni/bin/python /home/<username>/enviroplus-python/examples/<scriptname>.py
Restart=always
StandardOutput=inherit
StandardError=inherit
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

* Once you've made the changes to username save the changes.
* Run the follow three commands
```
sudo systemctl daemon-reload
sudo systemctl start <your_service_name>.service
sudo systemctl status <your_service_name>.service
```

You should now be fully installed and after rebooting your script should automatically run.

### csv-tempcomp.py
I've included my personal script that I am running. 
* It runs everything including PMS5003, although it doesn't include noise. The main difference between my script is that it saves the readings to a memory buffer and only writes them to the SD card every 15 minutes. I've done this to avoid constantly writing data to the SD card for increased longevity.

* The data is saved as a .csv file named 'sensor_data' with the following headings.
  timestamp in D-M-Y H:M:S format, temperature, humidity, pressure, light, oxidising, reducing, nh3, pm1, pm2_5, pm10.

* It also includes temperature compensation as found in the standard Pimoroni Scripts.
