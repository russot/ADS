#coding=gb18030


import sys,threading,time;
import serial;
import binascii,encodings;
import re;
import socket;


class Serial_rw(threading.Thread):
	def __init__(self, l_serial,read=None):
		threading.Thread.__init__(self)
		self.l_serial = l_serial;
		self.read = read;


	def run(self):
		if self.read:
			buffer = ""
			while 1:
				char = self.l_serial.read(1)
				if char == '\n':
					print buffer
					buffer = ""
				else:
					buffer = buffer + char
		else:
			while 1:
				self.l_serial.write("hello puppy!\n");
				
		




#测试用部分llo
if __name__ == '__main__':
	t = serial.Serial(5)
	
	s1 = Serial_rw(t, read='y')
	s2 = Serial_rw(t, read='')
	
	s1.start()
	s2.start()
	
	
	
	