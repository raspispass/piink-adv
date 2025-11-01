#!/bin/bash

# Helpers
# cat /proc/driver/rtc

# Get variables
SETTINGS_FILE="/home/user/PiInk/config/settings.json"
AUTO_IMG_RANDOMIZE=$(jq -r '.auto_img_randomize' $SETTINGS_FILE)
CHECKMAIL=$(jq -r '.checkmail' $SETTINGS_FILE)
REBOOT_INTERVAL=$(jq -r '.reboot_interval' $SETTINGS_FILE)
REBOOT_ACTIVE=$(jq -r '.reboot_active' $SETTINGS_FILE)

# Write log
date >> /home/user/cronlog

# Wait to finish initialization
sleep 30

if [[ "$AUTO_IMG_RANDOMIZE" == "y" ]]; then 
	curl http://localhost/random
fi

if [[ "$CHECKMAIL" == "y" ]]; then 
	/home/user/env/bin/python3  /home/user/checkmail.py
fi

if [[ "$REBOOT_ACTIVE" == "y" ]]; then 
	# Set the RTC alarm using rtcwake
	/usr/sbin/rtcwake -m no -s $REBOOT_INTERVAL
	sleep 60
	/sbin/shutdown -h now
fi
