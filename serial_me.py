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

			count += 1
			x =  random.randint(100, 2000)
			s = struct.pack('i',x)

			self.serial.write('\xff\xaa')
			self.serial.write(struct.pack("4s4s",'4095','4096'))
			self.serial.write('\xff\x55')

			
			time.sleep(0.002)
			
			
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
			if start :
				message += current
				#~ message += struct.unpack("c",current)[0]
			pattern += current
			if len(pattern) ==2:
			#jjj	print repr(pattern)
				if pattern == "\xff\x55": #end  magic
					end = True
					start= False
				if pattern == "\xff\xaa": #end  magic  missed
					#end = True
					start= True
				pattern = pattern[1:2]
			if end :
				end = False
				msg_len = len(message)
			#	print msg_len 
			#	print message 
				try:
					i1,i2= struct.unpack('4s4s',message[0:8])
					print count,'\t' , i1,'\t' ,i2 
					message = ''
				except:
					pass
				count +=1
				if count == 40001:
					break
			
		now = time.time()
		print now-begin


		
if __name__=='__main__':
	
	com1 = serial.Serial(5)
	#~ com2 = serial.Serial(0)
	com1.baudrate = 115200
	#~ com2.baudrate = 115200

	t1 = Serial_read(serial=com1)
	t2 = Serial_write(serial=com1)
	t1.start()
	t2.start()
	
	
