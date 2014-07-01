# -*- coding: utf-8 -*-
#!python
"""---endpoints server module---"""


from socket import *
from time import ctime
import const
import string
import threading
import time
import random
import re
from Queue import Queue
import serial
import struct 


PORT=20001



class Serial_Writer(threading.Thread):
	def __init__(self,serial):
		threading.Thread.__init__(self)
		self.serial = serial
		self.data=[ (45,	0.01,	0.04),
				(55,	5.6,	0.04),
				(76,	11.2,	0.04),
				(97,	16.8,	0.01),
				(118,	22.4,	0.01),
				(139,	28,	0.01),
				(160,	33.6,	0.01),
				(181,	39.2,	0.01),
				(202,	44.8,	0.01),
				(223,	50.4,	0.01),
				(244,	56.6,	0.01),
				(265,	62.8,	0.01),
				(286,	69,	0.01),
				(307,	75.2,	0.01),
				(328,	81.4,	0.01),
				(349,	89.6,	0.01),
				(370,	100.6,	0.01),
				(391,	115.6,	0.01),
				(412,	130.6,	0.01),
				(433,	150.6,	0.01),
				(454,	170.6,	0.01),]
		self.direction = "up"
		self.index = 0

	def run(self):
		print "write start..\n", self.serial
		index = 0
		while True:
			if self.direction == "up":
				index +=  1
				if index == 20:
					self.direction = "down"
			else:
				index -=  1
				if index == 0 :
					self.direction = "up"
			tmp1 = struct.pack("2f",self.data[index][0],self.data[index][1])
			i1,i2 = struct.unpack("2I",tmp1)
			self.serial.write('0x:')
			self.serial.write("%x%x"%(i1,i2))
			self.serial.write('\n')
			time.sleep(0.001)
			
			
class Serial_reader(threading.Thread):
	def __init__(self,serial,cmd_queue,data_queue):
		threading.Thread.__init__(self)
		self.cmd_queue  = cmd_queue
		self.data_queue = data_queue
		self.serial = serial
		
		self.message = ''
		self.pattern = ''
		self.end_flag = False
		self.start_flag = False
		self.run_flag = False
		self.count = 0 


	def run(self):
		Serial_Writer(self.serial).start()
		print "read thread start....\n",self.serial
		while True:
			self.get_data()
			time.sleep(0.001)

	def get_data(self):
			message = self.serial.readline()
			print "messge:%s\n" % message
			index = message.find("0x:")
			print "index:",index,"\n"
#			if self.start_flag :
#				self.message += current
#			self.pattern += current
#			if len(self.pattern) ==2:
#				if self.pattern == "\xff\x55": #end_flag  magic
#					self.end_flag = True
#					self.start_flag= False
#				if self.pattern == "\xff\xaa": #end_flag  magic  missed
#					#end_flag = True
#					self.start_flag= True
#				self.pattern = self.pattern[1:2]
#			if self.end_flag :
#				self.end_flag = False
			try:
				pos_  = string.atoi(message[index+3:index+11],16)
				value_= string.atoi(message[index+11:index+19],16)
				tmp1  = struct.pack("2I",pos_,value_)
				pos,value=struct.unpack("2f",tmp1)
				print pos
				print value

				self.data_queue.put("data:pos=%.2f;value=%.2f"%(pos,value) )
			except:
				print "unpack error...........................\n"
				pass
		



class Endpoint(threading.Thread):
	def __init__(self,CliSock):
		threading.Thread.__init__(self)
		self.CliSock = CliSock
		self.run_flag  = False
		self.quit_flag = False
		self.queue_cmd_in = Queue(-1)
		self.queue_data  = Queue(-1)
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
		count = 0
		while True:
			if self.quit_flag == True:
				print "ep quiting....\n"
				self.com.close()
				#threading.exit()
				break
			self.get_cmd() 
			while not self.queue_cmd_in.empty():
				self.deal_cmd()
			while  self.run_flag and  (not self.queue_data.empty() ) :
				count += 1
				data = self.queue_data.get() # 从后台读数据源线程对象取数据	
				try:
					self.CliSock.send(data+'\n')
				except:
					break
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
			#~ self.run_flag =  "serial openning...\n"
			#~ print self.run_flag,'\n'
			ep_name,baudrate = command[5:].split(':')
			self.OpenEndpoint(ep_name,baudrate)
			print "serial %s@%s openned!!!\n"%(ep_name,baudrate)
		elif command.startswith("stop"): #excute once and stop
			#~ self.StopEndpoint()
			self.run_flag =  False
		elif command.startswith("run"):#excute in loop 
			
			#~ self.StartEndpoint()
			self.run_flag = True
			while not self.queue_data.empty():
				self.queue_data.get()#flush old data 
		elif command.startswith("feed"):#excute in loop 
			
			#~ self.StartEndpoint()
			self.FeedDog()
		else:
			pass
		#~ print self.run_flag,'\n'
	
	
	def OpenEndpoint(self,endpoint_name,baudrate):
		print endpoint_name,"\t", baudrate
		ep_serial = string.atoi(endpoint_name[3:]) - 1
		self.com = serial.Serial(ep_serial)
		self.com.baudrate = string.atoi(baudrate) 
		reader = Serial_reader(self.com,self.queue_cmd_in,self.queue_data )
		reader.setDaemon(True)
		reader.start()



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
			print 'waiting for connection...'
			tcpCliSock,addr=tcpSerSock.accept()
			new_endpoint = Endpoint(CliSock=tcpCliSock)
			new_endpoint.start()
			time.sleep(0.001)
		
class Client_Endpoints(threading.Thread):
	def __init__(self,host='127.0.0.1',port=20001):
		threading.Thread.__init__(self)
		self.host = host
		self.port = port
		self.feed_flag = False
		self.life = 5

	def FeedDog(self):
		self.feed_flag = True
		self.life -=1
		if self.life >= 0:
			threading.Timer(5,self.FeedDog).start()

	def run(self):
		threading.Timer(5,self.FeedDog).start()
		CliSock = socket(AF_INET,SOCK_STREAM)
		CliSock.connect((self.host,self.port))
		CliSock.send("open:com6:115200\n")
		#~ time.sleep(3)
		#~ while 1:
		CliSock.send("run\n")
		while 1:
			if self.feed_flag == True:
				self.feed_flag = False
				CliSock.send("feed:dog\n")
			#print "client___",CliSock.recv(1024)
			CliSock.recv(1024)
			time.sleep(0.001)
			pass

		#~ CliSock.send("stop\n")


if __name__=='__main__':
	server = Server_Endpoints(host='127.0.0.1',port=PORT)
	server.start()
#	client = Client_Endpoints(host='127.0.0.1',port=PORT)
#	client.start()


	
	
	
