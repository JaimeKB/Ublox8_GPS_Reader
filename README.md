# Ublox8_GPS_Reader
Library that lets you read data from the UBlox8 RTK GPS

The dependancy is that you have memcache installed and enabled by running "apt-get install memcache" in a terminal,
and also run "sudo pip3 install python3-memcached" in a terminal to get memcache in python.

To use this, simply download the python file into your chosen directory, and run it using python 3.
This will start reading from the GPS and storing the latest read data into memory, which can be accessed at any time.

To access the latest data, in your own python code you must do "from Ublox8 import ReadMemcache", and then set any variable, 
e.g. Data = ReadMemcache(), and you will have the latest data from that time stored in data. This gives you full control over
the speed of which you retrieve data from the GPS, 
and you can have multiple processes/scripts retrieve data from memcache running simultaneously 
