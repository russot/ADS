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

from data_source import Data_Source 
from data_source import MyEvent, EVT_MY_EVENT


class Refer_Entry():
	def __init__(self,Xvalue,Yvalue,precision):
		self.Xvalue = Xvalue
		self.Yvalue = Yvalue
		self.precision= precision

	def GetReferValue(self):
		return self.Yvalue

	def SetReferValue(self,value):
		self.Yvalue= value

class Signal(wx.Object):
	def __init__(self,ok_colour="green",bad_colour="red",data=[], url="127.0.0.1:8088"):
		self.ok_colour = ok_colour
		self.bad_colour= bad_colour
		self.url = url
		self.data = data

	def GetData(self):
		return self.data

	def SetOkColour(self,color):
		self.ok_colour = color

	def GetOkColour(self):
		return self.ok_colour

		
	def SetBadColour(self,color):
		self.bad_colour = color 

	def GetBadColour(self):
		return self.bad_colour

	def SetUrl(self,url):
		self.url = url

	def GetUrl(self):
		return self.url


class signal_cfgUI(wx.Panel):
	def __init__(self,  parent=None, id=-1, signal=None) :

		super(signal_cfgUI, self).__init__(parent, id)
		self.signal= signal

		self.url= wx.TextCtrl(self,-1,self.signal.GetUrl(),size=(200,-1), style=wx.TE_PROCESS_ENTER)
		
		
		self.url_btn = wx.Button(self,-1,"set URL")
		self.ok_color_btn = wx.Button(self,-1,"GOOD color")
		self.bad_color_btn = wx.Button(self,-1,"BAD color")
		self.ok_color_btn.SetBackgroundColour(self.signal.GetOkColour())
		self.bad_color_btn.SetBackgroundColour(self.signal.GetBadColour())
		self.ok_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.bad_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.topsizer.Add((200,40))
		self.topsizer.Add(wx.StaticText(self, -1,u"Endpoint URL, 127.0.0.1:8088/usb1"))
		self.topsizer.Add(self.url)
		self.topsizer.Add(self.url_btn)
		self.url_btn.Bind(wx.EVT_BUTTON, self.OnSetUrl)
		
		self.hsizer= wx.BoxSizer(wx.HORIZONTAL|wx.ALIGN_CENTER)# 创建一个分割窗
		self.hsizer.Add((20,20))
		self.hsizer.Add(self.ok_color_btn)
		self.hsizer.Add((20,20))
		self.hsizer.Add(self.bad_color_btn)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.hsizer)		
		
		self.SetSizer(self.topsizer)
		self.Fit()

	def SelectColor(self,event):
		dlg = wx.ColourDialog(self)
		dlg.GetColourData().SetChooseFull(True)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		color= dlg.GetColourData().GetColour()
		if event.GetId() == self.ok_color_btn.GetId():
			print "set ok color"
			self.ok_color_btn.SetBackgroundColour(color)
			self.signal.SetOkColour(color)
		else:
			print "set bad color"
			self.bad_color_btn.SetBackgroundColour(color)
			self.signal.SetBadColour(color)
		dlg.Destroy()

	def GetOkColor(self):
		return self.ok_color_btn.GetBackgroundColour()

	def GetBadColor(self):
		return self.bad_color_btn.GetBackgroundColour()

	def GetUrl(self):
		return self.url.GetValue()

	def OnSetUrl(self,event):
		self.signal.SetUrl(self.url.GetValue())



############################################################################################################################################
class Dialog_Setup(wx.Dialog):
	""" configure the run time parameters """
	def __init__(self,  parent=None, 
		id=-1,caption=u"signal URL&UI setup", signals=[]) :

		super(Dialog_Setup, self).__init__(parent,id,caption,size=(800,600))
		
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.sig_sizer= wx.BoxSizer(wx.HORIZONTAL)
		self.cfg_panels = []
		print len(signals)
		self.signals = signals
		for signal in self.signals:
			cfg_panel = signal_cfgUI(self,-1,signal)
			self.cfg_panels.append(cfg_panel )
			self.sig_sizer.Add((20,20))
			self.sig_sizer.Add(cfg_panel,0,wx.EXPAND|wx.ALL,5)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.sig_sizer)		

		btnszr = self.CreateButtonSizer(wx.OK|wx.CANCEL) 
		self.topsizer.Add((40,20))
		self.topsizer.Add(btnszr, 0,wx.EXPAND|wx.ALL, 5) 

		self.SetSizer(self.topsizer)
		self.Fit()


############################################################################################################################################
class Signal_Panel(wx.lib.scrolledpanel.ScrolledPanel):   #3
	def __init__(self,  parent=None,
			size=(-1,-1),
			id=-1,
	 		signals=[],
			back_color="Black"):
		super(Signal_Panel, self).__init__(parent, id,size=size)
		#panel 创建
		self.SetupScrolling(scroll_x=True, scroll_y=True, rate_x=20, rate_y=20)
		self.SetupScrolling() 
		self.signals = signals #persist~~~~~~~~~~~~~~~~~~ 
		self.SetBackgroundColour(back_color)
		self.grid_colour= wx.Colour(250,0,250,200)
		self.ok_colour= wx.Colour(0,0,250,200)
		self.bad_colour= wx.Colour(250,0,0,200)
		self.refer_table = None

		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowCurrent)
		self.Bind(wx.EVT_MIDDLE_DCLICK, self.OnSetup)

	def OnSetup(self,evt):
		dlg = Dialog_Setup(None,-1,"signal UI&CFG",self.signals)
		if dlg.ShowModal()==wx.ID_OK:
			print "setup OK!"
		else:
			print "setup cancelled!"
		
		dlg.Destroy() #释放资源

	def SetRefer(self,refer_table):
		self.refer_table = refer_table
		self.refer_table.sort(key=lambda x:x.GetReferValue()) 


	def SetGridColour(self,colour):
		self.grid_colour= colour

	def SetOkColour(self,colour):
		self.ok_colour= colour


	def SetBadColour(self,colour):
		self.bad_colour= colour

	def OnPaint(self,evt):
		#print "redaw"
		self.ReDraw()

	def ReDraw(self):
		dc = wx.PaintDC(self)
		dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
		dc.Clear()
		self.DrawGrid()
		self.DrawData()

		
	def DrawGrid(self):
		dc = wx.ClientDC(self)
		clientRect = self.GetRect()
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		if  self.refer_table == None:
			return
		dc.SetPen(wx.Pen(self.grid_colour,1,style = wx.DOT))
		dc.SetTextForeground(self.grid_colour)
		count = 0
		refer_num = len(self.refer_table)
		if refer_num < 40:
			sparse = 2
		else:
			sparse = refer_num / 20
		for x in self.refer_table:
			count +=1
		
			if refer_num > 20 and count%sparse!=0:
				continue
			y = clientRect.height - clientRect.height*x.GetReferValue()/self.refer_table[-1].GetReferValue() 
			dc.DrawLine(0,y,clientRect.width,y)
			dc.DrawText("%.2f"%(float(x.GetReferValue())),0,y-15)

	def DrawData(self):
		dc = wx.ClientDC(self)
		clientRect = self.GetRect()
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		for signal in self.signals:
			try:
				self.RenderData(signal,dc,clientRect)
			except:
				pass

	def RenderData(self,signal,dc,clientRect):
		#print "render data....."
		x0 = 1
		x1 = 1
		last_Y0= 1
		#try:
		for data_ in signal.data:
			if data_.GetValue() > 0:
				x1 = x0 + data_.GetLength()
				if data_.GetValid() == True:
					dc.SetPen(wx.Pen(signal.ok_colour,2,style = wx.SOLID))
				else:
					dc.SetPen(wx.Pen(signal.bad_colour,2,style = wx.SOLID))
				Y0=int((1.0-data_.GetValue()/self.max_value)*clientRect.height )
				dc.DrawLine(x0,Y0,x0,last_Y0)
				dc.DrawLine(x0,Y0,x1,Y0)
				last_Y0 =  Y0
				x0 = x1
		#print "rendered one curve...."
		#except:
			#pass
	

	def SetMaxValue(self,value):
		self.max_value = float(value)

	def GetMaxValue(self,value):
		return self.max_value

	def SetPointValue(self,point,data_v_obj,sig_num=0):
		try:
			self.signals[sig_num].data[point]=data_v_obj
		except:
			pass

	def AppendValue(self,data_v_obj,sig_num=0):
		try:
			self.signals[sig_num].data.append(data_v_obj)
		except:
			pass

	
	def SetValue(self,index,data_v_obj,sig_num=0):
		try:
			self.signals[sig_num].data[index] = data_v_obj
		except:
			self.signals[sig_num].data.append(data_v_obj)
	
	def InitValue(self):
		for signal in self.signals:
			del signal.data
			signal.data = []

	def OnShowCurrent(self, event):
		pos = event.GetPosition()
		data_g =  []
		for blk_data in self.signals:
			data_g.append(blk_data[pos.x])
		for data in data_g:
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
		data_panel.AppendValue(data_v,0)
		data_v = Data_Validated(valid= valid,
				pos=pos,
				value=pos+200,
				value_refer=0.0,
				precision_refer=0.0,
				precision=0.0,
				)
		data_panel.AppendValue(data_v,1)
	data_panel.SetMaxValue(1400)
	
def pupulate_refer_table():
	refer_table = []
	for x in range(8,203):
		refer_table.append(Refer_Entry(x,205-x+0.2,0.001))
	return refer_table

	
if __name__=='__main__':
	app = wx.App()
	frm = wx.Frame(None)
	frm.SetSize((1400,600))

	panel = Signal_Panel(parent=frm,id=-1,size=(1400,600))
	panel.SetRefer(pupulate_refer_table())
	panel.SetGridColour(wx.Colour(0,250,250,200))
	panel.SetBackgroundColour(wx.Colour(150,50,90,200))
	panel.SetBadColour(wx.Colour(200,0,200))
	populate_data(panel)
	frm.Show()
	app.SetTopWindow(frm)
	app.MainLoop()

