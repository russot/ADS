# -*- coding: utf-8 -*-
#!python
"""---endpoints server module---"""


from socket import *
from time import ctime
import string
import threading
import time
import random
from Queue import Queue
import serial
import struct 




class Serial_write(threading.Thread):
	def __init__(self,serial):
		threading.Thread.__init__(self)
		self.serial = serial


	def run(self):
		print "write start..\n", self.serial
		count = 0
		while True:
			self.serial.write('\xfe\x28')
			self.serial.write('\xfe\x28')
			self.serial.write('\xfe\x01')
			self.serial.write(' UNIMAS                                ************************* ')
			
			time.sleep(2.002)
			
			
class Serial_read(threading.Thread):
	def __init__(self,serial):
		threading.Thread.__init__(self)
		self.serial = serial


	def run(self):
		print "read start..\n", self.serial
		message = ''
		pattern = ''
		end = False
		start = False
		count = 0 
		begin = time.time()
		while True:

			current = self.serial.read(1)
			message += current
			if current == '\x00':
				print message
				message = ''
			
		now = time.time()
		print now-begin


		
if __name__=='__main__':
	
	com1 = serial.Serial(1)
	#~ com2 = serial.Serial(0)
	com1.baudrate = 2400
	#~ com2.baudrate = 115200

	t1 = Serial_read(serial=com1)
	t2 = Serial_write(serial=com1)
	t1.start()
	t2.start()
	
	
