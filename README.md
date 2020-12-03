Onaird is a python program for the FLEX-6000 series radios that watches for TX from the radio and trips a
relay on the Raspberry Pi so that you can light a sign or do other physical actions.

```
usage: onaird.py [-h] [--gpio GPIO] radio_ip

Drive the On Air sign from the radio information

positional arguments:
  radio_ip     IP address of the radio

optional arguments:
  -h, --help   show this help message and exit
  --gpio GPIO  Line number of the GPIO line

```