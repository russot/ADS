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
	def __init__(self,url,queue_cmd_in,queue_data_in,queue_data_out):
		threading.Thread.__init__(self)
		self.queue_cmd_in = queue_cmd_in
		self.queue_cmd_out = queue_cmd_out
		self.queue_data_in = queue_data_in
		self.queue_data_out = queue_data_out
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
		if (self.buffer_group[-1]["length"] > self.sleep_count) and (self.dozing_flag == False):
			self.trigger_flag = False
			self.dozing_flag = True
			self.doze_count +=1

	def update_loop(self):
		if self.doze_count ==2 and self.loop_flag == False :
			self.doze_count =0
			self.loop_flag = True

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
				



############################################################################################################################################
if __name__=='__main__':
	queue_in_ = Queue(-1)
	queue_out_= Queue(-1)
	
	

