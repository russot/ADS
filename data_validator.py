# -*- coding: utf-8 -*-
#!python
"""Create a Frame instance and display image.""" 
import sys 
import wx 
import os 
import string
import threading
import time
from socket import *
import const
from Queue import Queue
import math
from data_point import Data_Point,Data_Validated,Data_Real


import wx.lib.agw.balloontip as btip

LINEAR  = 1
SQUARE = 2

class Data_Validator(wx.Object):
	global LINEAR
	def __init__(self,  parent=None, refer_table={},relation=LINEAR):
		if not refer_table:
			refer_table={}
		self.relation = relation
		self.table_validate = {}
		self.refer_table = refer_table
		self.SetupTable(refer_table,self.relation)

	def SetupTable(self,refer_table,relation):
		self.refer_table = refer_table
		pass
		

class Data_Validator_Linear(Data_Validator):
	global LINEAR
	def __init__(self,  parent=None, refer_table={}):
		super(Data_Validator_Linear, self).__init__(parent, refer_table=refer_table,relation=LINEAR)
		self.table_validate ={}
		self.max_value = 0
		if self.refer_table:
			self.SetupTable(self.refer_table)

	def SetupTable(self,refer_table, append=False):
		self.refer_table = refer_table
		#~ print refer_table
		if not append:
			self.table_validate = {}
		#~ list_table = sorted(refer_table,key=lambda x:x[0])) # x[0]为自变量
		list_table = sorted(refer_table)
		
		#~ print list_table
		left = ()
		for item in range(0,len(list_table)):
			right = refer_table[item]
			if not left:
				left = refer_table[item]#next iteration
				continue
			#~ print left,'\n',right
			precision= float(right[2])
			x1 = int(left[0])
			y1 = float(left[1])
			x2 = int(right[0])
			y2=  float(right[1])
			for x in range(x1,x2+1): # linearized  by increment of 1 
				k = float(y2 - y1)  / float(x2 - x1)
				y = y1+k * float(x - x1)
				self.table_validate[x] = (x, y, k, precision)

			self.max_value = y
			left = refer_table[item]#next iteration


	def ValidateData_v(self,data_real=Data_Real(0,0.0)):
		return self.ValidateData( data_real.GetPos(),data_real.GetValue() )

	def ValidateData_Step(self,position,value,step):
		#~ if (not data[0]) or  (not data[1]):
			#~ raise ValueError
		refer_value = self.refer_table[step][1]
		precision_refer = self.refer_table[step][2]
		
		precision_ = (value - refer_value) / refer_value
		
		if abs(precision_) < abs(precision_refer):
			valid = True 
		else:
			valid = False
		return  Data_Validated( valid , position, value ,  refer_value, precision_refer , precision_   )
		
	
	def ValidateData(self,pos,value):
		#~ if (not data[0]) or  (not data[1]):
			#~ raise ValueError
		x_  = float(pos)
		y_  = float(value)
		
		x1 = int(pos)
		#~ print x1
		y1 = float(self.table_validate[x1][1])
		k   = self.table_validate[x1][2]
		precision = self.table_validate[x1][3]		
		
		y = y1 + k * (x_ -float(x1)) 
		
		precision_ = (y_ - y) / y
		
		if abs(precision_) < abs(precision):
			valid = True 
		else:
			valid = False
		return  Data_Validated( valid , x_ , y_ ,  y, precision , precision_   )
		
	def GetTable(self):
		return self.table_validate
	
	def GetTable_Step(self):
		return self.refer_table

	def SetMaxValue(self,value):
		self.max_value = float(value)

	def GetMaxValue(self):
		return self.max_value


############################################################################################################################################
if __name__=='__main__':

	ref_cfg = open("refer_table.cfg",'r')
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
	print refer_table[13][1] 
		#~ self.refer_table = self.refer_table.items(), key=lambda d: d[0])
	#~ print refer_table.values()
	DV_demo = Data_Validator_Linear(parent=None, refer_table=refer_table)
	#~ print DV_demo.GetTable().values()
	data_v = DV_demo.ValidateData_v(Data_Real(307,77))
	print data_v.GetValid(),data_v.GetPrecision()
	data_v = DV_demo.ValidateData_Step(307,75,13)
	print data_v.GetValid(),data_v.GetPrecision()

	os.system("pause")

