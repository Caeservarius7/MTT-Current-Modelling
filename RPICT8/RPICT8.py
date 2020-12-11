#!/usr/bin/python2 
 import serial 
 ser = serial.Serial('/dev/ttyAMA0', 38400) 

 try: 
        while 1: 
             # Read one line from the serial buffer 
             line = ser.readline()   

             # Remove the trailing carriage return line feed 
             line = line[:-2]  

             # Create an array of the data 
             Z = line.split(' ') 

             # Print it nicely 
             print ("----------") 
             for i in range(len(Z)): 
                 if i==0: 
                     print ("NodeID: %s" % Z[0]) 
                 else: 
                     print ("Power %d: %s W" % (i, Z[i])) 

 except KeyboardInterrupt: 
        ser.close() 
