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
import serial
import struct 
import eut 
import refer_entry 
import usb.core
import usb.util

import eut 
import refer_entry 
#index for Devices.queues
_CMD	= 0
_DAT	= 1

#index for Devices.serial
_IN	= 0
_OUT	= 1

#index for Devices.type_
USB	= 0
COM	= 1
SIM	= 2


PORT=8088
IP_ADDRESS = '127.0.0.1'
DEMO_PN    = 'R939-5x'

USB_IDVendor=0x0483
USB_IDProduct=0x5750
			
			
class Serial_Reader(threading.Thread):
#----------------------------------------------------------------------------------------------------
	def __init__(self,serial_in,data_queues,dev_type=USB):
		threading.Thread.__init__(self)
		self.data_queues = data_queues
		self.serial_in   = serial_in
		self.dev_type    = dev_type 

		#self.eut_demo=eut.Eut()
		#self.eut_demo.RestoreFromDBZ(DEMO_PN)
		#print self.eut_demo
		#table0,table1 = self.eut_demo.GetReferTable()
		#print table0
		#x0 = table0[0].GetXvalue()
		#xn = table0[-1].GetXvalue()
		#if x0 > xn:
		#	self.xmax = x0
		#	self.xmin = xn
		#else:
		#	self.xmax = xn
		#	self.xmin = x0
		#refer_entry1 = self.eut_demo.GetReferEntry(Xvalue=self.xmin)
		#refer_entry2 = self.eut_demo.GetReferEntry(Xvalue=self.xmax)
		#y1 = refer_entry1.GetYvalue()
		#y2 = refer_entry2.GetYvalue()
		#if y1> y2:
		#	self.ymax = y1
		#	self.ymin = y2
		#else:
		#	self.ymax = y2
		#	self.ymin = y1
		#self.count = 0 
		#self.out = ''
		#print self.xmin,'\t',self.xmax,'\t',self.ymin,'\t',self.ymax,'\t',
	

#----------------------------------------------------------------------------------------------------
	def run(self):
		#print "read thread start....\n",self.serial_in
		while True:
			self.get_data()
			#self.get_debug_data()
			time.sleep(0.0002)

#----------------------------------------------------------------------------------------------------
	def get_data(self):
		if self.dev_type == COM:
			self.get_com_data()
		elif self.dev_type == USB:
			self.get_usb_data()
		#elif self.dev_type == SIM:
		#	self.get_sim_data()
		else:
			pass

#----------------------------------------------------------------------------------------------------
	def get_com_data(self):
		try:
			data = self.serial_in.readline()
			self.output(data)
			print self.serial_in
			print "com received data:%s\n"%data
		except:
			pass
#----------------------------------------------------------------------------------------------------
	def get_usb_data(self):
		try:
			raw_ = self.serial_in.read(size=64)#mMaxPacketSize for USB_bulk
			raw_bytes = ''
			for x in raw_:
				raw_bytes +=chr(x)
			if raw_bytes.startswith('0x:'):
				datas = struct.unpack('30H', str(raw_bytes)[4:64])#mMaxPacketSize for USB_bulk
				out = '0x:'
				for data in datas:
					out += '%04x'%data
				#print "usb__device__________:%s\n",out
				self.output(out)
			else:
				self.output(raw_bytes)

		except Exception,e:
			pass
			#print e

#----------------------------------------------------------------------------------------------------
	def output(self,data):
		for queue in self.data_queues:
			queue.put(data)

#----------------------------------------------------------------------------------------------------
	def get_sim_data(self):
		self.up_()
		self.max_()
		self.down_()
		self.min_()
		self.pull_()
		self.null_()
		self.pull_()
		self.min_()

#----------------------------------------------------------------------------------------------------
	def out_(self):
		if self.count%7 ==0:
			self.output(self.out)
			#print self.out
			self.out='0x:'
			time.sleep(0.0001)

#----------------------------------------------------------------------------------------------------
	def up_(self):
		rand_value_all = 0 
		value_ = 0
		self.out='0x:'
		self.count = 0
		refer_valueY= 0.00001
		for X in range (int(self.xmin),int(self.xmax)):
				#print 0.1*X
			refer_entry= self.eut_demo.GetReferEntry(Xvalue=X)
			refer_valueY= refer_entry.GetYvalue()*4096/self.ymax
			print " up Yvalue is ........",int(refer_entry.GetYvalue())
			Y = int(refer_valueY)
			self.out += '%04x%04x'%(X,Y)
			self.count +=1
			self.out_()
		out_thermo = '0t:0a90097d'
		self.output(out_thermo)
		#print thermo.Validate(hex_NTC=0xa90,hex_PT=0x97d)


#----------------------------------------------------------------------------------------------------
	def down_(self):
		for X in range (int(self.xmin),int(self.xmax)):
			refer_entry= self.eut_demo.GetReferEntry(Xvalue=(self.xmax+self.xmin-X))
			refer_valueY= refer_entry.GetYvalue()*4096/self.ymax
			print "down Yvalue is ........",int(refer_entry.GetYvalue())
			Y = int(refer_valueY)
			self.out += '%04x%04x'%(self.xmax+self.xmin-X,Y)
			self.count +=1
			self.out_()
		out_thermo = '0t:0a8a097d'
		self.output(out_thermo)

#----------------------------------------------------------------------------------------------------
	def max_(self):
		#remain high for sometime

		for X in range (1,800):
			Y = self.eut_demo.GetReferEntry(Xvalue=self.xmax).GetYvalue()
			self.out += '%04x%04x'%(self.xmax,Y*4096/self.ymax)
			print "max Yvalue is ........",int(Y)
			self.count +=1
			self.out_()

#----------------------------------------------------------------------------------------------------
	def min_(self):
		#remain high for sometime
		for X in range (1,800):
			Y = self.eut_demo.GetReferEntry(Xvalue=self.xmin).GetYvalue()
			self.out += '%04x%04x'%(self.xmin,Y*4096/self.ymax)
			print "min Yvalue is ........",int(Y)
			self.count +=1
			self.out_()


#----------------------------------------------------------------------------------------------------
	def pull_(self):
		#pull out eut and remain high
		for X in range (1,30):
			rand_value_once= random.random()* 4096
			self.out += '%04x%04x'%(self.xmin,rand_value_once)
			self.count +=1
			self.out_()
	
#----------------------------------------------------------------------------------------------------
	def null_(self):
		for X in range (1,1200):
			self.out += '%04x%04x'%(self.xmin,4096)
			self.count += 1
			self.out_()
		

class Device_Serial(threading.Thread):
#----------------------------------------------------------------------------------------------------
	def __init__(self,serial=None,queues = [[],[]],type_=USB):
		threading.Thread.__init__(self)
		self.serial = serial
		self.queues = queues
		self.type_  = type_


#----------------------------------------------------------------------------------------------------
	def Append(self,cmd_queue,data_queue):
		self.queues[_CMD].append(cmd_queue)
		self.queues[_DAT].append(data_queue)

#----------------------------------------------------------------------------------------------------
	def run(self):
		#Serial_Writer(self.serial).start()
		print "device thread start....\n",self.serial
		#start a reader thread to deal with read task	
		reader = Serial_Reader(self.serial[_IN],self.queues[_DAT],dev_type=self.type_)
		reader.setDaemon(True)
		reader.start()
		#start ever loop to deal with write task	
		while True:
			self.deal_cmd()
			time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
	def deal_cmd(self):
		for queue_cmd in self.queues[_CMD]:
			while not queue_cmd.empty():
				cmd = queue_cmd.get()
				print "serial write>>$new cmd: %s"%cmd
				#print self.serial[_OUT]
				self.serial[_OUT].write(cmd)
				time.sleep(0.01)

class Device_PLC(threading.Thread):
#----------------------------------------------------------------------------------------------------
	def __init__(self,up=None,down =None):
		threading.Thread.__init__(self)
		self.up = up
		self.down = down
		self.rangeHL = ''
#----------------------------------------------------------------------------------------------------
	def run(self):
		print "PLC thread start....\n"
		while True:
			self.deal_cmd()
			self.get_data()
			time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
	def deal_cmd(self):
		range_head = "rangeHL:"
		while not self.up[_CMD].empty():
			cmd = self.up[_CMD].get()
			print "PLC new cmd: %s"%cmd
			if cmd.startswith(range_head):
				start = len(range_head)
				self.read_rangeHL(cmd[start:])
				self.write_Xrange()
			else:
				print "PLC unknow command:%s"%cmd
			time.sleep(0.01)

#----------------------------------------------------------------------------------------------------
	def get_data(self):
		while not self.down[_DAT].empty():
			data = self.down[_DAT].get()
			if data.startswith("X?"):
				print "\nnew query of range!!\n"
				self.write_Xrange()
			else:
				print "PLC unknow data:%s"%data

#----------------------------------------------------------------------------------------------------
	def read_rangeHL(self,range_str):
		try:
			ranges = range_str.split(';')
			rangeH = int(ranges[0])
			rangeL = int(ranges[1])
			#to PLC format is as string of 'X:hhhhllll\n'
			self.rangeHL = 'X:%04d%04d\n'%(rangeH,rangeL)
			print self.rangeHL
		except:
			print "Error:unknow range format!!!"
			print "should be 'Xrange:hhhh,llll'!!!"

#----------------------------------------------------------------------------------------------------
	def write_Xrange(self):
		if not self.rangeHL:
			print "Error: range not setup yet!!!"
		self.down[_CMD].put(self.rangeHL)

		

class Motor():
#----------------------------------------------------------------------------------------------------
	def __init__(self,cmd_queue):
		self.cmd_queue = cmd_queue
		self.plc_queues = None

#----------------------------------------------------------------------------------------------------
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
			self.cmd_queue.put(cmd)
			time.sleep(speed)
		time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
	def move(self,move_dir):
		print "motor moving....."
		time.sleep(0.001)
		if move_dir == "plus":
			cmd = "motor:move:x+"
		else:
			cmd = "motor:move:x-"
		self.cmd_queue.put(cmd)
		time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
	def stop(self):
		print "motor stopped....."
		self.cmd_queue.put("adc:stop:")
		time.sleep(0.001)
		self.cmd_queue.put("motor:stop:")
		time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
	def setup(self,command):
		time.sleep(0.001)
		if command[6:].startswith("PLC:"):
			print "plc setup....."
			self.plc(command[10:])
		else:
			print "motor setup....."
			cmd = "motor:%s:" % command
			self.cmd_queue.put(cmd)
			time.sleep(0.001)
#----------------------------------------------------------------------------------------------------
	def plc(self,command):
		if command.startswith("com"):
			serial_queues= gDevices.Open(command)
			self.plc_queues = (Queue(-1),Queue(-1))
			plc_ = Device_PLC(self.plc_queues,serial_queues)
			plc_.setDaemon(True) 
			plc_.start()
			
		elif command.startswith("rangeHL"):
			if not self.plc_queues:
				print "Error:PLC comx not opened,please open PLC comx first!"
				return
			self.plc_queues[_CMD].put(command)


#----------------------------------------------------------------------------------------------------
	def run(self):
		print "motor running....."
		self.cmd_queue.put("adc:cfg:manual:N")
		time.sleep(0.01)
		self.cmd_queue.put("adc:cfg:interval:8000")
		time.sleep(0.01)
		self.cmd_queue.put("adc:cfg:channel:0")
		time.sleep(0.01)
		self.cmd_queue.put("motor:stop:")
		time.sleep(0.01)
		self.cmd_queue.put("adc:run:")
		time.sleep(0.01)
	#	cmd = "motor:move:x>"
	#	self.cmd_queue.put(cmd)
		#time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
	def adc(self,command):
		print "adc cmd %s....."%command
		time.sleep(0.1)
		self.cmd_queue.put(command)


		



class Endpoint(threading.Thread):
#----------------------------------------------------------------------------------------------------
	def __init__(self,CliSock):
		threading.Thread.__init__(self)
		self.CliSock = CliSock
		self.run_flag  = False
		self.quit_flag = False
		self.queue_cmd_in = Queue(-1)
		self.queue_data  = Queue(-1)
		self.buffer_cmd = []
		self.life = 3
		self.device_queue = [Queue(-1),Queue(-1)]
		self.motor = None
		self.count = 0
		self.last_time = time.time()
		self.datas = []
	
#----------------------------------------------------------------------------------------------------
	def FeedDog(self):
		self.life = 3

#----------------------------------------------------------------------------------------------------
	def Watchdog(self):
		if self.run_flag == True:
			self.life -= 1
			#print u"life remain %d sec"%(self.life*5)
		if self.life == 0:
			self.quit_flag = True
		else:
			threading.Timer(5,self.Watchdog).start()
#----------------------------------------------------------------------------------------------------
	def run(self):
		threading.Timer(5,self.Watchdog).start()
		print "endpoint start...\n"
		self.CliSock.setblocking(0)
		out = ''
		while True:
			if self.quit_flag == True:
				print "ep quiting....\n"
				#threading.exit()
				break
			self.get_cmd() 
			while not self.queue_cmd_in.empty():
				self.deal_cmd()
			while  self.run_flag and  (not self.device_queue[_DAT].empty() ) :
			 	# get data from data_queue of device
				out += self.device_queue[_DAT].get()+'\n'
				self.count += 1
				if self.count == 8:
					try:
						self.CliSock.send(out)
					except:
						pass
					self.count = 0
					out = ''
					#~ print count,':___',data,'\n'
			time.sleep(0.001)

#----------------------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------------------
	def deal_cmd(self):
		command = self.queue_cmd_in.get()
		print 'ep received command<<<%s\n' % command
		if command.startswith("open"): #excute once and stop
			dev_name = command[5:]
			queues_ = gDevices.Open(dev_name)
			if not queues_:
				print "open %s failed............."%dev_name
				return
			self.device_queue = queues_
			self.motor  = Motor(cmd_queue=self.device_queue[_CMD])
		elif command.startswith("stop"): #excute once and stop
			#~ self.StopEndpoint()
			self.run_flag =  False
			self.motor.stop()

		elif command.startswith("run"):#excute in loop 
			
			#~ self.StartEndpoint()
			self.run_flag = True
			while not self.queue_data.empty():
				self.queue_data.get()#flush old data 
			self.motor.run()

		elif command.startswith("accl"):#excute in loop 
			pass
			#if command.startswith("accl:plus"):
			#	self.motor.accl(100,"plus")
			#elif command.startswith("accl:minus"):
			#	self.motor.accl(100,"minus")

		elif command.startswith("move"):#excute in loop 
			
			pass
			#~ self.StartEndpoint()
			#if command.startswith("move:plus"):
			#	self.motor.move("plus")
			#elif command.startswith("move:minus"):
			#	self.motor.move("minus")

		elif command.startswith("setup"):#excute in loop 
			pass
			self.motor.setup(command)


		elif command.startswith("feed:dog"):#excute in loop 
			
			#~ self.StartEndpoint()
			self.FeedDog()
		elif command.startswith("adc:"):#
			self.motor.adc(command)
		elif command.startswith("vout:"):#
			self.motor.adc(command)
		elif command.startswith("X?"):#
			self.motor.adc(command+'\n')
		else:
			print "!!!>unkown cmd to ENDPOINT"
			pass
class Device_Proxy():
#----------------------------------------------------------------------------------------------------
	def __init__(self):
		#threading.Thread.__init__(self)
		self.routes = {}
		

#----------------------------------------------------------------------------------------------------
	def Open(self,dev_name_all):#open device Interface
		dev_name = dev_name_all.split(":")[0]
		if not dev_name in self.routes.keys():
			print "dev_name in open()....................",dev_name
			dev_type,ep =  self.OpenDevice(dev_name_all)
			if not ep:
				return None
			print "serial ep:___________________________________________________________________________________________________\n",ep
			cmd_queue = Queue(-1)
			data_queue =Queue(-1)
			cmd_queues = [cmd_queue] 
			data_queues =[data_queue]
			try:
				self.routes[dev_name] = Device_Serial(ep,[cmd_queues,data_queues],dev_type)
				self.routes[dev_name].setDaemon(True) 
				self.routes[dev_name].start() 
				print "routes.keys()",self.routes.keys()
			except:
				pass
		else:
			cmd_queue = Queue(-1)
			data_queue =Queue(-1)
			self.routes[dev_name].Append(cmd_queue,data_queue)
		return [cmd_queue,data_queue]

#----------------------------------------------------------------------------------------------------
	def OpenDevice(self,dev_name):
		if dev_name.startswith("usb"):
			return (USB,self.OpenUSB(dev_name))
		elif dev_name.startswith("com"):
			return (COM,self.OpenCOM(dev_name))
		else:
			pass
			return (SIM,self.OpenSIM(dev_name))


#----------------------------------------------------------------------------------------------------
	def OpenSIM(self,dev_name):
		print "open serial",dev_name
		return (open("sim.txt",'r'),open("out.txt",'w'))

	
#----------------------------------------------------------------------------------------------------
	def OpenCOM(self,dev_name):
		print "open serial",dev_name
		serial_ = dev_name.split(":")
		serial_str   = serial_ [0] 
		baudrate_str = serial_ [1]
		serial_num = string.atoi(serial_str[3:]) - 1
		com = serial.Serial(serial_num)
		com.baudrate = string.atoi(baudrate_str)
		return (com,com)
	
#----------------------------------------------------------------------------------------------------
	def OpenUSB(self,dev_name):
		print "open usb ",dev_name
		try:
			dev = usb.core.find(idVendor=USB_IDVendor, idProduct=USB_IDProduct)
		
			# was it found?
			if dev is None:
				raise ValueError('Device not found')
			print "usb-device 0x%04x/0x%04xfound!!"%(USB_IDVendor,USB_IDProduct)
		
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
			print "open usb device 0x%04x/0x%04x error...,now quit"%(USB_IDVendor,USB_IDProduct)
			return None
		# below two lines for debug only
		return (ep_in,ep_out)

gDevices = Device_Proxy()



class Server_Endpoints(threading.Thread):
#----------------------------------------------------------------------------------------------------
	def __init__(self,host='127.0.0.1',port=20001):
		threading.Thread.__init__(self)
		self.host = host
		self.port = port
		
#----------------------------------------------------------------------------------------------------
	def run(self):
		try:
			tcpSerSock = socket(AF_INET,SOCK_STREAM)
			tcpSerSock.bind((self.host,self.port))
			tcpSerSock.listen(5)
		except:
			return
		while True:
			print 'waiting for connection on %s:%d...'%(self.host,self.port)
			tcpCliSock,addr=tcpSerSock.accept()
			new_endpoint = Endpoint(CliSock=tcpCliSock)
			new_endpoint.start()
			time.sleep(0.1)
		
class Client_Endpoints(threading.Thread):
#----------------------------------------------------------------------------------------------------
	def __init__(self,host='127.0.0.1',port=20001,name=''):
		threading.Thread.__init__(self)
		self.host = host
		self.port = port
		self.CliSock = socket(AF_INET,SOCK_STREAM)
		self.CliSock.connect((self.host,self.port))
		self.CliSock.setblocking(0)
		self.timer = threading.Timer(1,self.FeedDog).start()
		self.buffer_cmd=[]
		self.queue_ep = Queue(0)
		self.name = name
		self.com_str = "com3:115200"
		self.rangeHL = (0,0)
		print "connecting server on port %d OK..."%port

#-----------rangeHL is integer tuple of (H,L)-----------------------------------------------------------------------------------------
	def SetRangeHL(self,rangeHL):
		self.rangeHL = rangeHL

#-----------rangeHL is integer tuple of (H,L)-----------------------------------------------------------------------------------------
	def SetCom(self,com_str):
		self.com_str = com_str

#----------------------------------------------------------------------------------------------------
	def FeedDog(self):
		self.CliSock.send("feed:dog\n")
		self.timer = threading.Timer(1,self.FeedDog).start()

#----------------------------------------------------------------------------------------------------
	def run(self):
		#self.CliSock.send("open:com1:115200\n")
		self.CliSock.send("open:%sim1:115200\n")
		time.sleep(0.1)
		#~ time.sleep(3)
		self.CliSock.send("adc:cfg:manual:Y\n")
		time.sleep(0.01)
		self.CliSock.send("adc:cfg:interval:8000\n")
		time.sleep(0.01)
		self.CliSock.send("adc:cfg:channel:0\n")
		time.sleep(0.01)
		self.CliSock.send("run:\n")
		time.sleep(0.01)
		self.CliSock.send("setup:PLC:%s\n"%self.com_str)
		time.sleep(0.01)
		self.CliSock.send("setup:PLC:rangeHL:%d;%d\n"%(self.rangeHL[0],self.rangeHL[1]))
		time.sleep(0.01)
		self.CliSock.send("X?\n")
		time.sleep(1)
		self.CliSock.send("X?\n")
		time.sleep(1)
		self.CliSock.send("X?\n")
		time.sleep(1)
		self.CliSock.send("X?\n")
		time.sleep(1)
		self.CliSock.send("X?\n")
		time.sleep(1)
		self.CliSock.send("X?\n")
		time.sleep(1)
		while True:
			try:
				recv_segment = self.CliSock.recv(8) #get command from socket_in 
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
				raw_data =  self.queue_ep.get()
				if not raw_data.startswith("0x:"):
					print raw_data
					continue
				try:
					i=0
					data = []
					while(True):
						x = int(raw_data[i*8+4:i*8+8],16)
						y = int(raw_data[i*8+8:i*8+12],16)
						
						if y > 65536:
							y -=65536
							y /=10
						data.append((x,y))
						i += 1
				except:
					pass
						
				print "ep_client %s :%s" % (self.name, data)



if __name__=='__main__':
	server = Server_Endpoints(host=IP_ADDRESS,port=PORT)
	server.start()
	time.sleep(1)
	rangeH = int(sys.argv[1])
	rangeL = int(sys.argv[2])
	client1 = Client_Endpoints(host=IP_ADDRESS,port=PORT,name='c1')
	client1.SetRangeHL((rangeH,rangeL))
	client1.SetCom(sys.argv[3])
	client1.start()
	#client2= Client_Endpoints(host='127.0.0.1',port=PORT,name='c2')
	#time.sleep(1.2)
	#client2.start()


	
	
	
