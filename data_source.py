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
from util import *

#index for x,y
_X = 0
_Y = 1


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
	x10_magic = 65536
	A1_to_A2  = 10.0
	new_trigger = abs(0.05)
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
		self.Q4filter_cmd_in= Queue(-1)
		self.Q4filter_cmd_out= Queue(-1)
		self.Q4filter_data_in= Queue(-1)
		self.Q4filter_data_out= Queue(-1)
		self.not_filted_count = 0
		self.filter_option = True

		self.signal_filter = sig_filter.Grouping_Filter(self.Q4filter_cmd_in,self.Q4filter_cmd_out,self.Q4filter_data_in,self.Q4filter_data_out)
		#self.signal_filter.start()
		self.signals = []
		self.buffer_group=[]
	def write(self,TE):
		pass

	def RegisterSignal(self,signal):
		self.signals.append(signal)

	def GetFilterOption(self):
		return self.filter_option

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
			#!!!~~~~~~~~~~~~~~~~~~~~继续接收数据, 以避免程序运行异常~~~~~~~~~~~~~~~~~~~~~~~~~!!!
			else: 
				try:
					recv_segment = self.tcpCliSock.recv(1024)
				except:
					pass

	
	def deal_cmd(self):
		if self.queue_cmd_in.empty():
			return
		command = self.queue_cmd_in.get() #get command (from self.queue_cmd_in), then process it and response(to  self.queue_out)
		#print "thread_source command: %s" % command
		if command.startswith("stop"): #excute
			print "data source stop"
			self.run_flag =  False
			while not self.queue_out.empty(): # 清除输出队列中的过期数据
				self.queue_out.get()
		#	self.queue_out.put("endpoint stopped by command.\n")
		elif command.startswith("run"):# 
			print "data source run"
			self.run_flag = True 
			while not self.queue_out.empty(): # 清除输出队列中的过期数据
				self.queue_out.get()
			#~ time.sleep(3)
		elif command.startswith("Filter:On"):
			self.filter_option = True
		elif command.startswith("Filter:Off"):
			self.filter_option = False
		elif command.startswith("get_status"): #excute 
			self.queue_out.put(self.run_flag)
		elif command.startswith("calibrate:") and self.run_flag==False: #excute 
			self.calibrate(command[len("calibrate:"):])
		#print command + '\n' 
		self.tcpCliSock.send(command + '\n') #


#######  thermo (ntc,pt) data: '0t:nnnnpppp.............................\n'
#        liquid (x,   y) data: '0x:xxxxyyyy.............................\n'
	def group_data(self):
		while not self.Q4filter_data_in.empty():
			#!!!!input data must be (pos_,value) tuple or list
			self.not_filted_count += 1
			if self.not_filted_count - 4000 == 0:#update 4000/screen
				self.not_filted_count = 0
				self.Q4filter_data_out.put(str("sleep"))
				self.Q4filter_data_out.put(str("trigger"))
				del self.buffer_group
				self.buffer_group = []

			newX,newY__ = self.Q4filter_data_in.get() 
			#print newX,newY__
			if newY__ == 0:# avoid error of devide_by_zero
				newY__ = 0.01
			if float(newY__) >= float(self.x10_magic) :
				newY= (float(newY__)-float(self.x10_magic) )/self.A1_to_A2
			else:
				newY= float(newY__)
			if not self.buffer_group:
				self.buffer_group.append( {"length":int(1),"value":(newX,newY),"flag":"new"} )
			else:
				lastY=self.buffer_group[-1]["value"][_Y]
				diff =  abs( (lastY-newY)/lastY)
				if diff > 3.0:
					continue
				if  diff > self.new_trigger:
					#self.new_flag =  True
					self.Q4filter_data_out.put(self.buffer_group[-1])
					self.buffer_group.append( {"length":int(1),"value":(newX,newY),"flag":"new"} )
				else:
					self.buffer_group[-1]["length"] += 1

	def GetData(self):
		try:
			recv_segment = self.tcpCliSock.recv(1024)
			#print recv_segment
			while '\n' in recv_segment:
				newline_pos = recv_segment.find('\n')
				self.buffer_recv.append(recv_segment[:newline_pos] )
				raw_data = ''.join(self.buffer_recv)
				if raw_data.startswith("0t:"):
					self.queue_out.put(raw_data)
				elif raw_data.startswith("0x:"):
					#print "data source raw_data: %s\n"%raw_data[0:123]
					data_str = raw_data[3:123]
					#print "data source raw_data: %s\n"%data_str
					len_data = len(data_str)/8# data format is 0xppppssss 
					#print len_data
					#input data now 
					for i in range(0,len_data):
						str4X = data_str[i*8:i*8+4]
						str4Y = data_str[i*8+4:i*8+8]
						data_x = int(str4X,16)
						data_y = int(str4Y,16)
						#print str4X,str4Y,data_x,data_y
						#self.signal_filter.append_to_ibuffer((data_x,data_y))
						self.Q4filter_data_in.put((data_x,float(data_y)))
					#filter data now 
					if self.filter_option == True:
						self.signal_filter.filter_data()
					else:
						self.group_data()
				self.buffer_recv = []
				try:
					recv_segment = recv_segment[newline_pos+1:]
				except:
					pass
			self.buffer_recv.append(recv_segment)
			#get filtered data 
			if not self.Q4filter_data_out.empty():
				while not self.Q4filter_data_out.empty():
					data = self.Q4filter_data_out.get()
					self.queue_out.put(data)
					#for signal in self.signals:
						#signal.in_data_queue.put(data)
				wx.PostEvent(self.window,MyEvent(60001)) #tell GUI to update
				
		
		except Exception, e:
			pass 




############################################################################################################################################
if __name__=='__main__':
	gServer.start()
	time.sleep(0.5)
	#app = wx.App()
	queue_cmd_in = Queue(0)
	queue_data_out = Queue(9999999) 
	port = '%d'%(server_endpoints.PORT)
	ip = '%s'%(server_endpoints.IP_ADDRESS)
	URL = ip+':'+port+'/'+'usb1/1'
	print URL
	dsource = Data_Source(window="",
			url=URL,
			queue_in =queue_cmd_in ,
			queue_out_= queue_data_out)

	dsource.filter_option = False
	dsource.new_trigger = 0.15
	dsource.start()
	time.sleep(0.5)
	queue_cmd_in.put("open:usb1:38400\n")
	time.sleep(0.5)
	queue_cmd_in.put("run:\n")
	while (True):
		while  not queue_data_out.empty():
			print "from_data_source............", queue_data_out.get(),'\n'
		time.sleep(0.0001)


