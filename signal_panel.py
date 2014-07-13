#-*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys 
import wx 
import compiler
import os 
import string
import threading
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
import data_point


MyEvent, EVT_MY_EVENT = wx.lib.newevent.NewCommandEvent()





############################################################################################################################################
class Signal_Panel(wx.Panel):   #3
	def __init__(self,  parent=None,
		     size=(-1,-1),
		     id=-1,
		     ok_colour=wx.Color(0,250,0,200),
		     bad_colour=wx.Color(250,0,0,200),
		     ):
		super(Signal_Panel, self).__init__(parent, id,size=size)
		#panel 创建
		self.parent__ = parent
		self.ok_colour = ok_colour  #persist~~~~~~~~~~~~~~~~~~
		self.bad_colour = bad_colour #persist~~~~~~~~~~~~~~~~~~ 
		self.data_store = []
		self.SetBackgroundColour("Black")

		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowCurrent)
		

	def SetOKColour(self,colour):
		self.ok_colour = colour

	def SetBadColour(self,colour):
		self.bad_colour= colour

	def OnPaint(self,evt):
		#print "redaw"
		self.ReDraw()

	def ReDraw(self):
		clientRect = self.GetRect()
		#dc=wx.BufferedPaintDC(self)
		dc = wx.PaintDC(self)
		dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
		dc.Clear()
		#self.DrawBackground(dc,clientRect)
		self.DrawGrig(dc,clientRect)
		self.DrawData(dc,clientRect)

	def DrawBackground(self,dc,clientRect):
		dc.SetPen(wx.Pen(self.GetBackgroundColour(),2,wx.SOLID))
		dc.SetBrush(wx.Brush(self.GetBackgroundColour(),wx.SOLID) )
		dc.DrawRectangle(0, 0,clientRect.width, clientRect.height)
		
	def DrawGrig(self,dc,clientRect):
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.DOT))
		for x in range(1,16):
			y = clientRect.height*x/16
			dc.DrawLine(0,y,clientRect.width,y)

	def DrawData(self,dc,clientRect):
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		x_pos = 0
		last_pos = len(self.data_store)-1
		last_pos_y = 1
		copy_count = 1
		try:
			last_data= self.data_store[0]
			for data_ in self.data_store[1:]:
				x_pos += 1
				if data_.GetValue() > 0:
					if data_.GetValue() == last_data.GetValue() and x_pos!=last_pos:
						copy_count += 1
					else:
						if last_data.GetValid() == True:
							dc.SetPen(wx.Pen(self.ok_colour,2,style = wx.SOLID))
						else:
							dc.SetPen(wx.Pen(self.bad_colour,2,style = wx.SOLID))
						y_pos=clientRect.height-int((last_data.GetValue()/self.max_value)*clientRect.height) 
						dc.DrawLine(x_pos-copy_count,y_pos,x_pos,y_pos )
						if x_pos!=0:
							dc.DrawLine(x_pos-copy_count,last_pos_y,x_pos-copy_count,y_pos )
						copy_count = 1
						last_pos_y =  y_pos
				last_data = data_
		except:
			pass
	

	def SetMaxValue(self,value):
		self.max_value = float(value)

	def GetMaxValue(self,value):
		return self.max_value

	def SetPointValue(self,point,data_v_obj):
		self.data_store[point]=data_v_obj

	def AppendValue(self,data_v_obj):
		self.data_store.append(data_v_obj)
	
	def SetValue(self,index,data_v_obj):
		try:
			self.data_store[index] = data_v_obj
		except:
			self.data_store.append(data_v_obj)
	
	def InitValue(self):
		data_v = Data_Validated(valid= True,
					pos=0,
					value= -100,
					value_refer=0.0,
					precision_refer=0.0,
					precision=0,
					)	
		for x in range(0,len(self.data_store)):
			self.data_store[x] = data_v 
		#print self.data_store[1].GetValue()

	def OnShowCurrent(self, event):
		pos = event.GetPosition()
		data= self.data_store[pos.x]
		valid = data.GetValid()
		value = data.GetValue()
		position   = data.GetPos()
		value_refer= data.GetValue_refer()
		precision_refer= data.GetPrecision_refer()
		precision= data.GetPrecision()
		#输出到控制台
		print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		print u"位置\t数值\t参考值\t参考精度\t实际精度\t结果"
		if value!= -100:
			print "%d\t%5.2f\t%5.2f\t%5.4f\t%5.4f\t"%(position, value,value_refer, precision_refer, precision),valid

############################################################################################################################################
def populate_data(data_panel):
	for pos in range (1,1200):
		if pos > 500:
			valid = True
		else:
			valid = False
		data_v = Data_Validated(valid= valid,
				pos=pos,
				value=pos+100,
				value_refer=0.0,
				precision_refer=0.0,
				precision=0.0,
				)
		data_panel.AppendValue(data_v)
	data_panel.SetMaxValue(1400)

if __name__=='__main__':
	app = wx.App()
	frm = wx.Frame(None)
	frm.SetSize((1400,900))

	panel = Signal_Panel(parent=frm,id=-1,size=(1400,900))
	populate_data(panel)
	frm.Show()
	app.SetTopWindow(frm)
	app.MainLoop()
	time.sleep(3)
	panel.SetBackgroundColour("Purple")

