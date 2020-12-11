//Download for Serial library
$ sudo apt-get install python-serial 

//Config tool download
$ wget lechacal.com/RPICT/tools/lcl-rpict-config.py.zip 
$ unzip lcl-rpict-config.py.zip 
$ sudo cp lcl-rpict-config.py /usr/local/bin 

//default config file
$ lcl-rpict-config.py 

//To download the desired values output from the online configurator download
$ lcl-rpict-config.py -w my_rpict.conf 

//Reset the device then run the python script
