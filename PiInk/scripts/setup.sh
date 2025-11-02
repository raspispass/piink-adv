#!/bin/bash

enable_interfaces(){
  #enable spi
  sudo sed -i 's/^dtparam=spi=.*/dtparam=spi=on/' /boot/config.txt
  sudo sed -i 's/^#dtparam=spi=.*/dtparam=spi=on/' /boot/config.txt
  sudo raspi-config nonint do_spi 0
  echo "SPI Interface has been enabled."
  #enable i2c
  sudo sed -i 's/^dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/config.txt
  sudo sed -i 's/^#dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/config.txt
  #disable SPI's chip-select to avoid the error (see https://github.com/pimoroni/inky)
  sudo bash -c 'echo "dtoverlay=spi0-0cs" >> /boot/firmware/config.txt'
  sudo raspi-config nonint do_i2c 0
  echo "I2C Interface has been enabled."
}

enable_interfaces
echo "create piink systemd service"
sudo cp ~/piink.service /etc/systemd/system/piink.service
sudo systemctl daemon-reload
sudo systemctl enable piink

echo "create crontab entry for automatic shutdown and reboot via RTC (works only with https://github.com/bablokb/pcb-pi-batman)"
# Alternative without pcb-pi-batman shield, just regularly check for new incoming mails instead (configured via web ui):
# sudo bash -c 'echo "*/10 *  * * *  root    /home/user/rtc-cron.sh" >> /etc/crontab'
chmod +x ~/checkmail.py
chmod +x ~/rtc-cron.sh
sudo bash -c 'echo "@reboot	root	/home/user/rtc-cron.sh" >> /etc/crontab'
sudo systemctl restart cron

echo "restart"
sudo shutdown -r now
