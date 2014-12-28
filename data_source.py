#-*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys 
import os 
import string
import threading
import random
import time
from socket import *
import const
from Queue import Queue
import math
import sig_filter
import server_endpoints
import struct 
import config_db
import wx.lib.newevent

MyEvent, EVT_MY_EVENT = wx.lib.newevent.NewCommandEvent()

class Endpoint():
	def __init__(self, url="127.0.0.1:8088/com1"):
		self.SetUrl(url)
		
	def SetIP(self,url):
		return url.split(':')[0]
		

	def SetPort(self,url):
		__parts = url.split(':')
		parts = __parts[1].split('/')
		return string.atoi(parts[0])

	def SetEpIndex(self,url):
		__parts = url.split(':')
		parts = __parts[1].split('/')
		return parts[1]


	def GetIP(self):# example string "127.0.0.1"
		return self.ip
		

	def GetPort(self):# example integer 8088
		return self.port

	def GetEpIndex(self):# example string "com1" , "com2" ...
		return self.ep_index

	def SetUrl(self,url):
		self.ip=self.SetIP(url) # example string "127.0.0.1"
		self.port =self.SetPort(url) # example integer 8088
		self.ep_index =self.SetEpIndex(url)# example string "com1" , "com2" ...


############################################################################################################################################
class Data_Source(threading.Thread,wx.Object):
	def __init__(self,window=None,url='',queue_in=None,queue_out_=None):
		threading.Thread.__init__(self)
		self.window = window
		self.url = url 
		self.queue_cmd_in   = queue_in
		self.queue_out = queue_out_
		self.endpoint = Endpoint(url)
		self.run_flag =  False
		self.tcpCliSock = socket(AF_INET,SOCK_STREAM)
		self.buffer_recv=[]
		#~ sys.stdout = self
		self.feed_flag = True
		self.data_count = 0
		self.Q4filter_cmd_in= Queue(-10)
		self.Q4filter_cmd_out= Queue(-10)
		self.Q4filter_data_in= Queue(-10)
		self.Q4filter_data_out= Queue(-10)

		self.signal_filter = sig_filter.Grouping_Filter(self.Q4filter_cmd_in,self.Q4filter_cmd_out,self.Q4filter_data_in,self.Q4filter_data_out)
		#self.signal_filter.start()
		self.signals = []

	def write(self,TE):
		pass

	def RegisterSignal(self,signal):
		self.signals.append(signal)

	def FeedDog(self):
		self.tcpCliSock.send('feed:dog\n') #
		threading.Timer(5,self.FeedDog).start()

	def run(self):#运行一个线程
		threading.Timer(5,self.FeedDog).start()
	#	print self.endpoint.GetIP()
	#	print self.endpoint.GetPort()
		self.tcpCliSock.connect( ( self.endpoint.GetIP(), self.endpoint.GetPort() ) )
		self.tcpCliSock.setblocking(0)
		while True:
			time.sleep(0.001)
			self.deal_cmd()
			if self.run_flag == True : # get data  from endpoint by socket, and upload to UI
				self.GetData()
			else: #!!!~~~~~~~~~~~~~~~~~~~~继续接收数据, 以避免程序运行异常~~~~~~~~~~~~~~~~~~~~~~~~~!!!
				try:
					recv_segment = self.tcpCliSock.recv(1024)
				except:
					pass

	def SetEndpoint(self,url):
		self.endpoint.SetUrl(url)

	def run_adc(self):
		self.tcpCliSock.send("adc:cfg:manual:Y\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:cfg:interval:20\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:cfg:channel:0\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:run:\n")
		time.sleep(0.01)
	
	def sample(self):
		self.tcpCliSock.send("adc:cfg:channel:0\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:sample:\n") # request sample
		time.sleep(0.01)		# wait for data from source
		self.GetData()   # data is in self.queue_out 
		return self.queue_out.get() # fetch value from self.queue_out[pos,value),....]

	def deal_cmd(self):
		if self.queue_cmd_in.empty():
			return
		command = self.queue_cmd_in.get() #get command (from self.queue_cmd_in), then process it and response(to  self.queue_out)
		#print "thread_source command: %s" % command
		if command.startswith("stop"): #excute
			self.run_flag =  False
			while not self.queue_out.empty(): # 清除输出队列中的过期数据
				self.queue_out.get()
		#	self.queue_out.put("endpoint stopped by command.\n")
		elif command.startswith("run"):# 
			self.run_flag = True 
			while not self.queue_out.empty(): # 清除输出队列中的过期数据
				self.queue_out.get()
			#~ time.sleep(3)
		#	self.run_adc()
		elif  command.startswith("get_status"): #excute 
			self.queue_out.put(self.run_flag)
		elif  command.startswith("calibrate:") and self.run_flag==False: #excute 
			self.calibrate(command[len("calibrate:"):])
		#print command + '\n' 
		self.tcpCliSock.send(command + '\n') #

	def GetData(self):
		try:
			recv_segment = self.tcpCliSock.recv(1024)
			#print recv_segment
			while '\n' in recv_segment:
				pos_newline = recv_segment.find('\n')
				self.buffer_recv.append(recv_segment[:pos_newline] )
				raw_data = ''.join(self.buffer_recv)
				if raw_data.startswith("0x:"):
					data_str = raw_data[3:]
					len_data = data_str.find('\0')/8 
					#input data now 
					for i in range(0,len_data):
						str4X = data_str[i*8:i*8+4]
						str4Y = data_str[i*8+4:i*8+8]
						data_x = int(str4X,16)
						data_y = int(str4Y,16)
						#print str4X,str4Y,data_x,data_y
						#self.signal_filter.append_to_ibuffer((data_x,data_y))
						self.Q4filter_data_in.put((data_x,data_y))
					#filter data now 
					self.signal_filter.filter_data()
				self.buffer_recv = []
				try:
					recv_segment = recv_segment[pos_newline+1:]
				except:
					pass
			self.buffer_recv.append(recv_segment)
			#get filtered data 
			while not self.Q4filter_data_out.empty():
				data = self.Q4filter_data_out.get()
				self.queue_out.put(data)
				for signal in self.signals:
					signal.in_data_queue.put(data)
				wx.PostEvent(self.window,MyEvent(60001)) #tell GUI to update
				
		
		except Exception, e:
			pass 




############################################################################################################################################
if __name__=='__main__':
	queue_cmd_in = Queue(0)
	queue_data_out = Queue(9999999) 
	port = '%d'%(server_endpoints.PORT)
	ip = '%s'%(server_endpoints.IP_ADDRESS)
	URL = ip+':'+port+'/'+'usb1'
	print URL
	dsource = Data_Source(window="",
			url=URL,
			queue_in =queue_cmd_in ,
			queue_out_= queue_data_out)

	dsource.start()
	time.sleep(0.5)
	queue_cmd_in.put("open:com1:38400\n")
	time.sleep(0.5)
	queue_cmd_in.put("run\n")
	while (True):
		while  not queue_data_out.empty():
			print "from_data_source............", queue_data_out.get()
		time.sleep(0.01)


