#-*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys 
import wx 
import os 
import string
import traceback
import threading
import random
import time
from socket import *
import const
from Queue import Queue
import math
import struct 




############################################################################################################################################
class Grouping_Filter(threading.Thread):
	x10_magic = 0x10000# 0x1000, means data x10 in mcu
	A1_to_A2 = 10
	sleep_trig_level = 500
	step_trig_level = 10
	err= -999999
	def __init__(self,queue_cmd_in,queue_cmd_out,queue_data_in,queue_out):
		threading.Thread.__init__(self)
		self.queue_cmd_in   = queue_cmd_in
		self.queue_cmd_out  = queue_cmd_out
		self.queue_data_in  = queue_data_in
		self.queue_out = queue_out
		self.buffer_group=[]
		#~ sys.stdout = self

		self.count = 0
		self.data_count = 0
		self.new_value = 0.02

		self.run_flag =  False
		self.step_flag =  False
		self.running_flag= False
		self.loop_flag =  False
		self.new_flag =  False
		self.trigger_flag =  False
		self.cur_refer = 0
		self.last_refer = 0
		#below is x10 constants , depending on circuits OP part

		self.time_now = time.time()
		self.last_time = time.time()

	def write(self,TE):
		pass



	def run(self):#运行一个线程
		while True:
			self.deal_cmd()
			self.filter_data()


	def clear_data(self):
		while not self.queue_out.empty(): # 清除输出队列中的过期数据
			self.queue_out.get()
		while not self.queue_data_in.empty(): # 清除输入队列中的过期数据
			self.queue_data_in.get()


	def deal_cmd(self):
		if self.queue_cmd_in.empty():
			return
		command = self.queue_cmd_in.get() #get command (from self.queue_cmd_in), then process it and response(to  self.queue_out)
		if command.startswith("stop"): #excute
			self.run_flag =  False
			self.clear_data()
		elif command.startswith("run"):# 
			self.run_flag = True 
			self.clear_data()
		elif command.startswith("get_status"):# 
			if self.run_flag == True :
				self.queue_cmd_out.put("running")
			else:
				self.queue_cmd_out.put("stopped")

	def grouping_data(self):
		while not self.queue_data_in.empty():
			#print  self.queue_data_in.get()
			try:
				#!!!!input data must be (pos_,value) tuple or list
				Xvalue,Yvalue = self.queue_data_in.get() 
				#print Xvalue,Yvalue
				if Yvalue == 0:# avoid error of devide_by_zero
					Yvalue = 0.0001
				if float(Yvalue) >= float(self.x10_magic) :
					data_new = (float(Yvalue)-self.x10_magic )/self.A1_to_A2
				else:
					data_new = float(Yvalue)
				data_last=self.buffer_group[-1]["value"][-1]
				diff_ =   (data_last-data_new)/data_last  
				if  abs(diff_) > self.new_value:
					self.new_flag =  True
					self.buffer_group.append( {"length":int(1),"value":(Xvalue,data_new),"flag":"new"} )
				else:
					self.buffer_group[-1]["length"] += 1

			except Exception,e:
				pass
				#print  e
				self.new_flag =  True
				self.buffer_group.append( {"length":int(1),"value":(Xvalue,data_new),"flag":"new"} )


	def get_last_step(self):
		buf_len = len(self.buffer_group) 
		for i in range(0,buf_len-1):
			last = -2-i
			if self.buffer_group[last]["length"] > self.step_trig_level :
				return  last
		return self.err

	def get_last_sleep(self):
		buf_len = len(self.buffer_group) 
		for i in range(0,buf_len-1):
			last = -2-i
			if self.buffer_group[last]["length"] > self.sleep_trig_level :
				return  last
		return self.err

	def update_filter(self):
		try:
			if self.buffer_group[-1]["length"] >= self.sleep_trig_level and self.buffer_group[-1]["flag"] == "step":
				self.trigger_flag = False
				#print "sleeping........."
				self.queue_out.put( "sleep")
				self.buffer_group[-1]["flag"] = "sleep"
				last_step = self.get_last_step()
				if self.buffer_group[last_step]["flag"]=="step":
					cur_value = self.buffer_group[-1]["value"][-1]
					last_step_value = self.buffer_group[last_step]["value"][-1]
					# going back to start point again,it circled once!
					if (cur_value < last_step_value) and (self.running_flag == True):
						#print "circled once ..........\n"
						#self.queue_out.put( "circle")
						self.running_flag =  False
						del self.buffer_group
						self.buffer_group = []
	
			if self.buffer_group[-1]["length"] >= self.step_trig_level and self.buffer_group[-1]["flag"] == "new":
				self.buffer_group[-1]["flag"] = "step"
				try:
					print "step value<<<<<<<<<<<<<<<<<<<<",self.buffer_group[-1]["value"][-1]
				except:
					pass
				#print "stepping........."
				

				#two consequent steps generates a trigger, for bypassing noises
				last_step = self.get_last_step()
				if self.buffer_group[last_step]["flag"]=="step" and self.trigger_flag == False :
					print "triggering ........."
					self.trigger_flag = True
					self.queue_out.put( "trigger")
					cur_value = self.buffer_group[-1]["value"][-1]
					last_step_value = self.buffer_group[last_step]["value"][-1]
					if (cur_value > last_step_value) and (self.running_flag == False):
						#print "started ..........\n"
						#self.queue_out.put( "start")
						self.running_flag =  True
						self.last_refer = 0
						self.cur_refer = 1
						#reserve last_step_-1 and conseqence, remove noises
						#print len(self.buffer_group)
					last_step = self.get_last_sleep()
					#for item in self.buffer_group[last_sleep:-1]:
						#self.queue_out.put(item)
			
				if self.trigger_flag == True:
					for item in self.buffer_group[last_step:-1]:
						self.queue_out.put(item)
		except Exception,e:
			pass
			#print  e


	def filter_data(self):
		self.grouping_data()
		self.update_filter()
		#self.validate()
				
####################################################################################################

############################################################################################################################################
class Eut_Source(threading.Thread):
	def __init__(self,queue_out):
		threading.Thread.__init__(self)
		self.queue_out = queue_out


	def run(self):
		while(True):
			self.populate_data()

	def populate_data(self):
		rand_value_all = 0 
		value_ = 0
		#step up
		for valueX in range (1,1200):
			base = (int(valueX)/int(100)*100) + 50
			if valueX%100 < 10: 
				rand_value_once= random.random()* base / 99.99
				valueY= rand_value_once + base 
			else:
				if valueX%100 ==10:
					rand_value_all = random.random() * base /99.90
					value_= rand_value_all + base 
				valueY = value_
			self.queue_out.put((valueX,valueY))
			time.sleep(0.001)
		#remain high for sometime
		for valueX in range (1,1200):
			self.queue_out.put((1200,4095))
			time.sleep(0.001)
		#step down
		for valueX in range (1,1200):
			base = (int(valueX)/int(100)*100) + 50
			if valueX%100 < 10: 
				rand_value_once= random.random()* base / 99.99
				valueY= 1200-(rand_value_once + base)
			else:
				if valueX%100 ==10:
					rand_value_all = random.random() * base /99.90
					value_= rand_value_all + base 
				valueY = 1200-value_
			self.queue_out.put((valueX,valueY))
			time.sleep(0.001)
		#remain low for sometime
		for valueX in range (1,1200):
			self.queue_out.put((0,0.001))
			time.sleep(0.001)
		#pull out eut and remain high
		for valueX in range (1,100):
			rand_value_once= random.random()* 1299
			self.queue_out.put((0,rand_value_once))
			time.sleep(0.001)
		for valueX in range (1,1200):
			self.queue_out.put((0,4095))
			time.sleep(0.001)
		#pull in eut and remain low
		for valueX in range (1,100):
			rand_value_once= random.random()* 1299
			self.queue_out.put((0,rand_value_once))
			time.sleep(0.001)
		for valueX in range (1,1200):
			self.queue_out.put((0,0.001))
			time.sleep(0.001)
############################################################################################################################################
if __name__=='__main__':
	queue_cmd_i= Queue(-10)
	queue_in_1 = Queue(-10)
	queue_data_i= Queue(-10)
	queue_data_o= Queue(-10)

	filtor = Grouping_Filter(queue_cmd_in=queue_cmd_i,
				queue_cmd_out=None,
				queue_data_in=queue_data_i,
				queue_out=queue_data_o)
	source = Eut_Source(queue_data_i)
	source.start()

	while True:
		filtor.deal_cmd()
		filtor.filter_data()
		while not queue_data_o.empty():
			data = queue_data_o.get()
			print "data................",data

		time.sleep(0.001)
