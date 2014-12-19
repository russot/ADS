# -*- coding: utf-8 -*-
#!python
"""---endpoints server module---"""


from socket import *
from time import ctime
import sys
import const
import string
import threading
import time
import random
import re
from Queue import Queue
#import serial
import struct 
import eut 
import refer_entry 
#import usb.core
#import usb.util

PORT=8088
IP_ADDRESS = '127.0.0.1'
DEMO_PN    = 'R939-55'

			
			
class Serial_reader(threading.Thread):
	def __init__(self,serial_in,data_queue):
		threading.Thread.__init__(self)
		self.queue_out= data_queue
		self.serial = serial_in
		
		self.eut_demo=eut.Eut()
		self.eut_demo.RestoreFromDBZ(DEMO_PN)
		table0,table1 = self.eut_demo.GetReferTable()
		x0 = table0[0].GetXvalue()
		xn = table0[-1].GetXvalue()
		if x0 > xn:
			self.xmax = x0
			self.xmin = xn
		else:
			self.xmax = xn
			self.xmin = x0
		refer_entry1 = self.eut_demo.GetReferEntry(Xvalue=self.xmin)
		refer_entry2 = self.eut_demo.GetReferEntry(Xvalue=self.xmax)
		y1 = refer_entry1.GetYvalue()
		y2 = refer_entry2.GetYvalue()
		if y1> y2:
			self.ymax = y1
			self.ymin = y2
		else:
			self.ymax = y2
			self.ymin = y1
		self.count = 0 
		self.out = ''
		print self.xmin,'\t',self.xmax,'\t',self.ymin,'\t',self.ymax,'\t',




	def run(self):
		#Serial_Writer(self.serial).start()
		print "read thread start....\n",self.serial
		while True:
		#	self.get_usb_data()
			self.get_debug_data()
			time.sleep(0.001)

	def get_usb_data(self):
		self.out = ''
		try:
			for byte__ in self.serial.read(size=64):
				if byte__  != 0:
					self.out += chr(byte__)
			self.queue_out.put(self.out)

		except:
			pass

	def get_debug_data(self):
		self.up_()
		self.max_()
		self.down_()
		self.min_()
		self.pull_()
		self.null_()
		self.pull_()
		self.min_()

	def up_(self):
		rand_value_all = 0 
		value_ = 0
		self.out='0x:'
		self.count = 0
		for X in range (int(self.xmin*10),int(self.xmax*10+10)):
			if X%50 < 10: 
				print 0.1*X
				refer_entry= self.eut_demo.GetReferEntry(Xvalue=0.1*X)
				refer_valueY= refer_entry.GetYvalue()
				rand_value_once= random.random()* refer_valueY*0.1
				Y = refer_valueY*1.05 + rand_value_once
			else:
				if X%50 ==10:
					rand_value_once= random.random()* refer_valueY*0.03
					Y = refer_valueY*1.01 - rand_value_once
			self.out += '%04x%04x'%(X,Y)
			self.count +=1
			if self.count%7 ==0:
				self.queue_out.put(self.out)
				self.out='0x:'
				time.sleep(0.001)
	def max_(self):
		#remain high for sometime

		for X in range (1,800):
			self.out += '%04x%04x'%(self.xmax*10,self.ymax)
			self.count +=1
			if self.count%7 ==0:
				self.queue_out.put(self.out)
				self.out='0x:'
				time.sleep(0.001)
	def min_(self):
		#remain high for sometime
		for X in range (1,800):
			self.out += '%04x%04x'%(self.xmin*10,self.ymin)
			self.count +=1
			if self.count%7 ==0:
				self.queue_out.put(self.out)
				self.out='0x:'
				time.sleep(0.001)
	def down_(self):
		for X in range (int(self.xmin*10),int(self.xmax*10+10)):
			if X%50 < 10: 
				refer_entry= self.eut_demo.GetReferEntry(Xvalue=(self.xmax-self.xmin-0.1*X))
				refer_valueY= refer_entry.GetYvalue()
				rand_value= random.random()* refer_valueY*0.1
				Y = refer_valueY *1.05-rand_value
			else:
				if X%50 ==10:
					rand_value= random.random()* refer_valueY*0.03
					Y = refer_valueY*1.01 - rand_value
			self.out += '%04x%04x'%(X,Y)
			self.count +=1
			if self.count%7 ==0:
				self.queue_out.put(self.out)
				self.out='0x:'
				time.sleep(0.001)
	def pull_(self):
		#pull out eut and remain high
		for X in range (1,100):
			rand_value_once= random.random()* 4095
			self.out += '%04x%04x'%(self.xmin*10,rand_value_once)
			self.count +=1
			if self.count%7 ==0:
				self.queue_out.put(self.out)
				self.out='0x:'
				time.sleep(0.001)
	def null_(self):
		for X in range (1,1200):
			self.out += '%04x%04x'%(self.xmin*10,4095)
			self.count +=1
			if self.count%7 ==0:
				self.queue_out.put(self.out)
				self.out='0x:'
				time.sleep(0.001)



class Motor():
	def __init__(self,serial_out):
		self.serial = serial_out

	def accl(self,accl_speed,accl_dir):
		print "motor accl....."
		time.sleep(0.001)
		speed = 1/float(accl_speed)
		if accl_dir == "plus":
			cmd = "motor:accl:x+"
		elif accl_dir == "minus":
			cmd = "motor:accl:x-"
		else:
			return
		for i in range (1,33):
			self.serial.write(cmd)
			time.sleep(speed)
		time.sleep(0.001)

	def move(self,move_dir):
		print "motor moving....."
		time.sleep(0.001)
		if move_dir == "plus":
			cmd = "motor:move:x+"
		else:
			cmd = "motor:move:x-"
		self.serial.write(cmd)
		time.sleep(0.001)

	def stop(self):
		print "motor stopped....."
		time.sleep(0.001)
		cmd = "motor:stop:"
		self.serial.write(cmd)
		time.sleep(0.001)

	def setup(self,command):
		print "motor setup....."
		time.sleep(0.001)
		cmd = "motor:%s:" % command
		self.serial.write(cmd)
		time.sleep(0.001)

	def run(self):
		print "motor running....."
		cmd = "motor:auto:Y"
		self.serial.write(cmd)
		time.sleep(0.01)
		cmd = "motor:move:x>"
		self.serial.write(cmd)
		time.sleep(0.001)

	def adc(self,command):
		print "adc cmd %s....."%command
		self.serial.write(command)
		time.sleep(0.01)


		



class Endpoint(threading.Thread):
	def __init__(self,CliSock):
		threading.Thread.__init__(self)
		self.CliSock = CliSock
		self.run_flag  = False
		self.quit_flag = False
		self.queue_cmd_in = Queue(0)
		self.queue_data  = Queue(0)
		self.buffer_cmd = []
		self.life = 3
	       
	
	def FeedDog(self):
		self.life = 3

	def Watchdog(self):
		if self.run_flag == True:
			self.life -= 1
			print u"life remain %d sec"%(self.life*5)
		if self.life == 0:
			self.quit_flag = True
		else:
			threading.Timer(5,self.Watchdog).start()
	def run(self):
		threading.Timer(5,self.Watchdog).start()
		print "endpoint start...\n"
		self.CliSock.setblocking(0)
		self.count = 0
		while True:
			if self.quit_flag == True:
				print "ep quiting....\n"
				#threading.exit()
				break
			self.get_cmd() 
			while not self.queue_cmd_in.empty():
				self.deal_cmd()
			while  self.run_flag and  (not self.queue_data.empty() ) :
				data = self.queue_data.get() # 从后台读数据源线程对象取数据	
			#	print data+'\n'
				try:
					self.CliSock.send(data+'\0'+'\n')
				except:
					pass
				#~ print count,':___',data,'\n'
			time.sleep(0.001)

	def get_cmd(self):
		try:
			recv_segment = self.CliSock.recv(1024) #get command from socket_in 
			#~ print recv_segment
			while '\n' in recv_segment:
				pos_newline = recv_segment.find('\n')
				#~ print pos_newline, repr(recv_segment[:pos_newline])
				self.buffer_cmd.append(recv_segment[:pos_newline])
				#~ print ' '.join(self.buffer_cmd)
				self.queue_cmd_in.put(''.join(self.buffer_cmd))
				self.buffer_cmd=[]
				try:
					recv_segment = recv_segment[pos_newline+1:]
				except:
					pass
			self.buffer_cmd.append(recv_segment)
		except:
			pass

	def deal_cmd(self):
		command = self.queue_cmd_in.get()
		print 'command:%s\n' % command
		if command.startswith("open"): #excute once and stop
			ep_name,baudrate = command[5:].split(':')
			self.OpenEndpoint(ep_name,baudrate)
			print "serial %s@%s openned!!!\n"%(ep_name,baudrate)
		elif command.startswith("stop"): #excute once and stop
			#~ self.StopEndpoint()
			self.run_flag =  False
			self.motor.stop()

		elif command.startswith("run"):#excute in loop 
			
			#~ self.StartEndpoint()
			self.run_flag = True
			while not self.queue_data.empty():
				self.queue_data.get()#flush old data 
			#self.motor.run()

		elif command.startswith("accl"):#excute in loop 
			if command.startswith("accl:plus"):
				self.motor.accl(100,"plus")
			elif command.startswith("accl:minus"):
				self.motor.accl(100,"minus")

		elif command.startswith("move"):#excute in loop 
			
			#~ self.StartEndpoint()
			if command.startswith("move:plus"):
				self.motor.move("plus")
			elif command.startswith("move:minus"):
				self.motor.move("minus")

		elif command.startswith("setup"):#excute in loop 
			self.motor.setup(command)


		elif command.startswith("feed:dog"):#excute in loop 
			
			#~ self.StartEndpoint()
			self.FeedDog()
		elif command.startswith("adc:"):#
			self.motor.adc(command)
		else:
			print "!!!>unkown cmd to ENDPOINT"
			pass
		#~ print self.run_flag,'\n'
	
	
	def OpenEndpoint(self,endpoint_name,baudrate):
		print "open ep of usb"
		try:
			dev = usb.core.find(idVendor=0x0483, idProduct=0x5750)
		
			# was it found?
			if dev is None:
				raise ValueError('Device not found')
			print "usb-device with pid/vid=0483/5750 found!!"
		
			# set the active configuration. With no arguments, the first
			# configuration will be the active one
			dev.set_configuration()
		
			# get an endpoint instance
			cfg = dev.get_active_configuration()
			intf = cfg[(0,0)]
		
			ep_out = usb.util.find_descriptor(
				intf,
				# match the first OUT endpoint
				custom_match =lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
			ep_in = usb.util.find_descriptor(
				intf,
				# match the first IN endpoint
				custom_match =lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
	
		except: 
			print "open ep_out error...,now quit"
			pass
		# below two lines for debug only
		ep_out = sys.stdout
		ep_in = sys.stdin
		self.motor = Motor(serial_out=ep_out)	
		self.reader = Serial_reader(serial_in=ep_in, data_queue=self.queue_data)
		self.reader.setDaemon(True)
		self.reader.start()
	


class Server_Endpoints(threading.Thread):
	def __init__(self,host='127.0.0.1',port=20001):
		threading.Thread.__init__(self)
		self.host = host
		self.port = port
		
	def run(self):
		tcpSerSock = socket(AF_INET,SOCK_STREAM)
		tcpSerSock.bind((self.host,self.port))
		tcpSerSock.listen(5)
		while True:
			print 'waiting for connection on %s:%d...'%(self.host,self.port)
			tcpCliSock,addr=tcpSerSock.accept()
			new_endpoint = Endpoint(CliSock=tcpCliSock)
			new_endpoint.start()
			time.sleep(0.01)
		
class Client_Endpoints(threading.Thread):
	def __init__(self,host='127.0.0.1',port=20001):
		threading.Thread.__init__(self)
		self.host = host
		self.port = port
		self.CliSock = socket(AF_INET,SOCK_STREAM)
		self.CliSock.connect((self.host,self.port))
		self.CliSock.setblocking(0)
		self.timer = threading.Timer(1,self.FeedDog).start()
		self.buffer_cmd=[]
		self.queue_ep = Queue(0)

	def FeedDog(self):
		self.CliSock.send("feed:dog\n")
		self.timer = threading.Timer(1,self.FeedDog).start()

	def run(self):
		self.CliSock.send("open:com6:115200\n")
		time.sleep(1.01)
		self.CliSock.send("run:\n")
		time.sleep(1.01)
		#~ time.sleep(3)
		self.CliSock.send("adc:cfg:manual:Y\n")
		time.sleep(0.01)
		self.CliSock.send("adc:cfg:interval:2000\n")
		time.sleep(0.01)
		self.CliSock.send("adc:cfg:channel:0\n")
		time.sleep(0.01)
		self.CliSock.send("adc:run:\n")
		time.sleep(0.01)
		while True:
			try:
				recv_segment = self.CliSock.recv(1024) #get command from socket_in 
				#~ print recv_segment
				while '\n' in recv_segment:
					pos_newline = recv_segment.find('\n')
					#~ print pos_newline, repr(recv_segment[:pos_newline])
					self.buffer_cmd.append(recv_segment[:pos_newline])
					#~ print ' '.join(self.buffer_cmd)
					self.queue_ep.put(''.join(self.buffer_cmd))
					self.buffer_cmd=[]
					try:
						recv_segment = recv_segment[pos_newline+1:]
					except:
						pass
				self.buffer_cmd.append(recv_segment)
			except:
				pass
			while not self.queue_ep.empty():
				print "ep_client reads:%s" % self.queue_ep.get()

if __name__=='__main__':
	server = Server_Endpoints(host=IP_ADDRESS,port=PORT)
	server.start()
	#client = Client_Endpoints(host='127.0.0.1',port=PORT)
	#client.start()


	
	
	
