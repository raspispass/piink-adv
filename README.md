# Installation

## Requirements
- Tested on Raspbian light
- Setup with username 'user'
- The git repository is expected to be checked out in the users home directory '~/'

## Install python3 dependencies
`python3 -m venv ~/env`
`source ~/env/bin/activate`
`pip3 install -r ~/PiInk/scripts/requirements.txt`
`sudo apt update && sudo apt upgrade`
`sudo apt install python3-dev`

## Change settings
Search for "CHANGEME" in all files and change the settings (`e.g. grep -R "CHANGEME" *`)

## Execute install script
`chmod +x ~/PiInk/scripts/setup.sh`
`~/PiInk/scripts/setup.sh`
