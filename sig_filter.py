#-*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys 
import wx 
import os 
import string
import threading
import random
import time
from socket import *
import const
from Queue import Queue
import math
from data_point import Data_Point,Data_Real,Data_Validated
from data_validator import Data_Validator_Linear
from signal_control import Thread_Source
import wx.lib.agw.balloontip as btip
import struct 
from thread_sqlite import Thread_Sqlite
import config_db
import sqlite3 as sqlite
import wx.lib.scrolledpanel as scrolledpanel
from dialog_query import Dialog_Query
import wx.lib.newevent
from signal_panel import Signal_Panel

MyEvent, EVT_MY_EVENT = wx.lib.newevent.NewCommandEvent()




############################################################################################################################################
class Filter_Grouping(threading.Thread):
	def __init__(self,queue_cmd_in,queue_cmd_out,queue_data_in,queue_data_out,validator):
		threading.Thread.__init__(self)
		self.queue_cmd_in   = queue_cmd_in
		self.queue_cmd_out  = queue_cmd_out
		self.queue_data_in  = queue_data_in
		self.queue_data_out = queue_data_out
		self.validator      = validator 
		self.buffer_group=[]
		#~ sys.stdout = self
		self.data_count = 0
		self.step_value = 0.05
		self.sleep_count = 800
		self.run_flag =  False
		self.step_flag =  False
		self.loop_flag =  False
		self.trigger_flag =  False
		self.dozing_flag =  False
		self.doze_count = 0 
		self.validate_flag = False
		self.min_count = 100
		self.cur_refer = 0

	def write(self,TE):
		pass

	def set_validator(self,validator):
		self.validator = validator 

	def run(self):#运行一个线程
		while True:
			self.deal_cmd()
			self.filter_data()


	def clear_data(self):
		while not self.queue_data_out.empty(): # 清除输出队列中的过期数据
			self.queue_data_out.get()
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
			data_new = self.queue_data_in.get()
			self.data_count += 1
			try:
				data_last=self.buffer_group[-1]["value"]
				if abs( float(data_last-data_new)/float(data_last) ) > self.step_value:
					if self.buffer_group[-1]["length"] > self.min_count: 
						self.step_flag = True
						self.cur_refer += 1
					self.buffer_group.append( {"length":1,"value":data_new} )
				else:
					self.buffer_group[-1]["length"] += 1
					self.step_flag = False
			except:
				self.buffer_group.append( {"length":1,"value":data_new} )
				pass

	def update_trigger(self):
		try:
			if (self.buffer_group[-2]["length"] > self.sleep_count) and (self.trigger_flag == False):
				self.trigger_flag = True
				self.dozing_flag = False
		except:
			pass

	def update_dozer(self):
		try:
			if (self.buffer_group[-1]["length"] > self.sleep_count) and (self.dozing_flag == False):
				self.trigger_flag = False
				self.dozing_flag = True
				self.doze_count +=1
		except:
			pass
	
	def update_loop(self):
		try:
			if self.doze_count ==2 and self.loop_flag == False :
				self.doze_count =0
				self.loop_flag = True
		except:
			pass

	def validate(self):
		if self.step_flag == True:
			data = self.buffer_group[-2]
			data_value = data["value"] 
			x_value= data_value["x"]
			y_value = data_value["y"]
			data_v  = self.validator.ValidateData_Step(
					position=x_value,
					value=y_value,
					step=self.cur_refer-1)
			self.queue_data_out.put( {"count":data["length"],"data_v":data_v} )

	def filter_data(self):
		self.grouping_data()
		self.update_trigger()
		self.update_dozer()
		self.update_loop()
		self.validate()
				
def create_validator(refer_file_name):
	ref_cfg = open(refer_file_name,'r')
	if  not ref_cfg.readline().startswith("#signal refer table"):
		print "refer file format not right!\nThe first line should be \"#signal refer table\", and \"displacement,value,precision\" each following line"
		quit  
	refer_table=[]
	for line in ref_cfg.readlines():
		#~ print line
		line = line.replace(" ","").replace("\t","").strip('\n')# 
		element = line.split(',')
		key   =  string.atoi(element[0])
		value = string.atof(element[1])
		precision =  string.atof(element[2])
		refer_table.append([key,value,precision])
	return Data_Validator_Linear(parent=None, refer_table=refer_table)


############################################################################################################################################
if __name__=='__main__':
	queue_in = Queue(-1)
	queue_in_1 = Queue(-1)
	queue_data= Queue(-1)
	queue_data_out= Queue(-1)
	source = Thread_Source(window=None,
			url="127.0.0.1:20001/com6",
			queue_in=queue_in,
			queue_out=queue_data)

	validator = create_validator("refer_table.cfg")	
	filtor = Filter_Grouping(queue_cmd_in=queue_in_1,
				queue_cmd_out=None,
				queue_data_in=queue_data,
				queue_data_out=queue_data_out,
				validator=validator)
	source.start()
	filtor.start()
	queue_in.put("run:\n")
	while True:
		try:
			data = queue_data_out.get()
			print data["count"],'\t',data["data_v"].GetValue()
		except:
			pass
