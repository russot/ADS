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

from refer_entry import *
from refer_table import *

class Signal(wx.Dialog):
	def __init__(self,window=None,ok_colour="green",bad_colour="red",data=[], url="127.0.0.1:8088"):
		super(Signal, self).__init__(parent=None)
		self.window = window
		self.ok_colour = ok_colour
		self.old_ok_colour = ok_colour
		self.bad_colour= bad_colour
		self.old_bad_colour = bad_colour
		self.url = url
		self.data = data
		self.cmd_queue=Queue(-1)
		self.data_queue=Queue(-1)
		self.started_flag = False
		self.thread_source = None
		self.data_count = 0
		self.Bind(EVT_MY_EVENT, self.OnNewData)

	def SetWindow(self,window):
		self.window = window

	def GetData(self):
		return self.data

	def SetOkColour(self,colour):
		self.ok_colour = colour

	def GetOkColour(self):
		return self.ok_colour

		
	def SetBadColour(self,colour):
		self.bad_colour = colour 

	def GetBadColour(self):
		return self.bad_colour

	def SetUrl(self,url):
		self.url = url

	def GetUrl(self):
		return self.url

	def SetRefers(self,table):
		try:
			self.Refers = table
			self.Refers.sort(key=lambda x:x.GetYvalue())
			#print "signal max value",self.Refers[-1].GetYvalue()
			self.SetMaxValue(self.Refers[-1].GetYvalue())
		except Exception,e:
			print e
			pass

	def SetMaxValue(self,value):
		self.max_value = float(value)

	def GetMaxValue(self,value):
		return self.max_value

	def Run(self):
		print "signal running.....\n"
		if self.started_flag != True:
			self.thread_source = Data_Source(self,self.url,self.cmd_queue,self.data_queue)
			self.thread_source.setDaemon(True)
			self.thread_source.start() #启动后台线程, 与endpoint server进行连接与通信
			self.started_flag = True
			#self.menu_setup.Enable(False)#已运行，再不能设置
			serial_name = self.url.split("/")[1]
			open_cmd = "open:%s:%s"%(serial_name,'115200')
			print open_cmd
			self.cmd_queue.put(open_cmd)
		while not self.data_queue.empty(): # 消除输出队列中的过期数据
			self.data_queue.get()
		self.cmd_queue.put("run:")

	def Init_Data(self):
		self.data_count = 0
		del self.data
		self.data = []
		self.window.Refresh()

	def Pause(self):
		print "signal pause.....\n"
		self.cmd_queue.put("stop:")
		while not self.data_queue.empty(): # 消除输出队列中的过期数据
			self.data_queue.get()
		self.Init_Data()

	def OnNewData(self, event):
		out = ''
		pos = 0
		value = 0
		while not self.data_queue.empty():
			item = self.data_queue.get()
			if isinstance(item,str):
				if item.startswith("trigger"):
					self.Init_Data()
			if isinstance(item,dict):
				self.data_count += 1
				Xvalue,Yvalue = item["value"]
				length = item["length"]
				print "new data .............",Xvalue,Yvalue,length
				if length > 1000:
					length = 50
				refer_entry  = self.GetReferEntry(Xvalue,Yvalue)
				record_entry = Refer_Entry()
				Xprecision,Yprecision,xstatus,ystatus = refer_entry.Validate(Xvalue,Yvalue)
				if xstatus==True and ystatus==True:
					status = True
				else:
					status = False
				record_entry = Refer_Entry(
						Xvalue=Xvalue,
						Yvalue=Yvalue,
						Xprecision=Xprecision,
						Yprecision=Yprecision,
						valid_status=status)
				record_entry.SetLength(length)
				self.data.append(record_entry)
				self.window.DrawData()
				self.window.Refresh()
				#self.signal_panel.Refresh()

	def GetRefer_X(self,Xvalue=0,Yvalue=0):
		refer_entry= None
		self.Refers.sort(key=lambda x:x.GetXvalue())
		if Xvalue > self.Refers[-1].GetXvalue():
			refer_entry = self.Refers[-1]
		elif Xvalue < self.Refers[0].GetXvalue():
			refer_entry = self.Refers[0]
		else:
			p0 = self.Refers[0]
			for p1 in self.Refers:
				x0 = p0.GetXvalue()
				x1 = p1.GetXvalue()
				delta0 = abs(Xvalue - x0)
				delta1 = abs(Xvalue - x1)
				#judge being within by comparing delta_sum 
				if (delta0 + delta1) > abs(x1 - x0):
					p0 = p1
					continue
				#use nearby Yvalue
				y0 = p0.GetYvalue()
				y1 = p1.GetYvalue()
				delta0 = abs(Yvalue - y0)
				delta1 = abs(Yvalue - y1)
				if abs(delta0) < abs(delta1): 
					refer_entry =  p0
				else:
					refer_entry =  p1
				break
		return refer_entry

	def GetRefer_Y(self,Xvalue=0,Yvalue=0):
		refer_entry= None
		self.Refers.sort(key=lambda x:x.GetYvalue())
		if Yvalue <= self.Refers[0].GetYvalue():#outof range
				refer_entry =  self.Refers[0].GetYvalue()
				self.Refers[0].SetValidStatus(True)
		elif Yvalue >= self.Refers[-1].GetYvalue():#outof range
				refer_entry =  self.Refers[-1].GetYvalue()
				self.Refers[-1].SetValidStatus(True)
		else:
			p0 = self.Refers[0]
			for p1 in self.Refers:
				if p1.GetValidStatus == True:
					p0 = p1
					continue
				y0 = p0.GetYvalue()
				y1 = p1.GetYvalue()
				delta0 = Yvalue - y0
				delta1 = Yvalue - y1
				#judge being within by comparing delta_sum 
				if (delta0 + delta1) > abs(y1 - y0):
					p0 = p1
					continue
				#use nearby Yvalue
				if abs(delta0) < abs(delta1): 
					refer_entry =  p0
					p0.SetValidStatus(True)
				else:
					refer_entry =  p1
					p1.SetValidStatus(True)
				break

		return refer_entry # if not found, return None object

	def GetReferEntry(self,Xvalue=0,Yvalue=0):
		'''Xvalue should be None for using Yvalue as index,
		or integer for using itself as index '''
		refer_entry =None
		if Xvalue != None:# use Xvalue as index
			refer_entry = self.GetRefer_X(Xvalue,Yvalue)
		else:# use Yvalue as index, and table is sorted by Yvalue
			refer_entry = self.GetRefer_Y(Xvalue,Yvalue)
		return refer_entry # if not found, return None object

class signal_cfgUI(wx.Panel):
	def __init__(self,  parent=None, id=-1, signal=None) :

		super(signal_cfgUI, self).__init__(parent, id)
		self.signal= signal

		self.url= wx.TextCtrl(self,-1,self.signal.GetUrl(),size=(200,-1), style=wx.TE_PROCESS_ENTER)
		
		
		#self.url_btn = wx.Button(self,-1,"set URL")
		self.ok_color_btn = wx.Button(self,-1,"Ok color")
		self.bad_color_btn = wx.Button(self,-1,"Bad color")
		self.ok_color_btn.SetBackgroundColour(self.signal.GetOkColour())
		self.bad_color_btn.SetBackgroundColour(self.signal.GetBadColour())
		self.ok_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.bad_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.topsizer.Add((200,40))
		self.topsizer.Add(wx.StaticText(self, -1,u"URL,如 127.0.0.1:8088/usb1"))
		self.topsizer.Add(self.url)
		#self.topsizer.Add(self.url_btn)
		#self.url_btn.Bind(wx.EVT_BUTTON, self.OnSetUrl)
		
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
			#self.signal.SetOkColour(color)
		else:
			print "set bad color"
			self.bad_color_btn.SetBackgroundColour(color)
			#self.signal.SetBadColour(color)
		dlg.Destroy()

	def GetOkColour(self):
		return self.ok_color_btn.GetBackgroundColour()

	def GetBadColour(self):
		return self.bad_color_btn.GetBackgroundColour()

	def GetUrl(self):
		return self.url.GetValue()

	#def OnSetUrl(self,event):
		#self.signal.SetUrl(self.url.GetValue())



############################################################################################################################################
class Dialog_Setup(wx.Dialog):
	""" configure the run time parameters """
	def __init__(self,  parent=None, 
		id=-1,caption=u"signal URL&UI setup", signals=[]) :

		super(Dialog_Setup, self).__init__(parent,id,caption,size=(800,600))
		
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.sig_sizer= wx.BoxSizer(wx.HORIZONTAL)
		self.cfg_panels = []
		self.ui_map = []
		print len(signals)
		self.signals = signals
		for signal in self.signals:
			cfg_panel = signal_cfgUI(self,-1,signal)
			self.cfg_panels.append(cfg_panel )
			self.ui_map.append([signal,cfg_panel])
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
		if signals:
			self.SetSignals(signals)
		self.SetBackgroundColour(back_color)
		self.grid_colour= wx.Colour(250,0,250,200)
		self.ok_colour= wx.Colour(0,0,250,200)
		self.bad_colour= wx.Colour(250,0,0,200)
		self.refer_tables = None
		self.eut = None
		self.running_flag = False

		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowCurrent)
		self.Bind(wx.EVT_MIDDLE_DCLICK, self.OnSetup)

		self.popmenu1 = wx.Menu()
		self.menu_save = self.popmenu1.Append(wx.NewId(), u"保存数据", u"保存数据到数据库" )
		self.menu_run = self.popmenu1.Append(wx.NewId(), u"运行.当前点", u"运行与暂停", kind=wx.ITEM_CHECK)
		self.popmenu1.AppendSeparator()
		self.menu_query_ui = self.popmenu1.Append(wx.NewId(), u"数据库查询", u"组合查询已存储数据")
		self.menu_query_current = self.popmenu1.Append(wx.NewId(), u"当前数据查询", u"查询正在测试的数据")
		self.popmenu1.AppendSeparator()
		self.menu_eut = self.popmenu1.Append(wx.NewId(), u"Sensor选择", u"被测件选择")
		self.menu_setup = self.popmenu1.Append(wx.NewId(), u"配置", u"测试参数配置")
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightDown)
		self.Bind(wx.EVT_MENU, self.OnRunStop,self.menu_run)
		self.Bind(wx.EVT_MENU, self.OnShowCurrent,self.menu_query_current)
		#self.Bind(wx.EVT_MENU, self.OnQuery_UI,self.menu_query_ui)
		self.Bind(wx.EVT_MENU, self.OnSetup,self.menu_setup)
		self.Bind(wx.EVT_MENU, self.OnSelectEut,self.menu_eut)
		#self.Bind(wx.EVT_MENU, self.OnSave,self.menu_save)

	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)

	def OnRunStop(self, evt):
		if self.running_flag != True:
			self.running_flag = True
			print "running..........."
			self.Run()
		else:
			print "pausing..........."
			self.running_flag = False
			self.Pause()
	def Run(self):
		for signal in self.signals:
			signal.Run()
			
	def Pause(self):
		for signal in self.signals:
			signal.Pause()
			

	def SetSignals(self,signals):
		self.signals = signals 
		for signal in signals:
			if isinstance(signal,Signal):
				signal.SetWindow(self)
	
	def OnSetup(self,evt):
		self.Setup()
	
	def Setup(self):
		dlg = Dialog_Setup(None,-1,"signal UI&CFG",self.signals)
		if dlg.ShowModal()==wx.ID_OK:
			print "setup OK!"
			for (signal,cfg_panel) in dlg.ui_map:
				signal.SetUrl(cfg_panel.GetUrl())
				signal.SetOkColour(cfg_panel.GetOkColour())
				signal.SetBadColour(cfg_panel.GetBadColour())
		else:
			print "setup cancelled!"
		
		dlg.Destroy() #释放资源

	def SetEut(self,eut):
		self.eut = eut
		self.SetRefer(self.eut.GetReferTable())

	def SetRefer(self,refer_tables):
		self.refer_tables = refer_tables
		for table in self.refer_tables:
			table.sort(key=lambda x:x.GetYvalue())
			for refer_entry in table:
				print ">>>>>>>>>>>>>>>>>>>>>>>>>",refer_entry.ShowSensor()
		i=0
		for signal in self.signals:#map refer_tables to signals as 1:1
			signal.SetRefers(self.refer_tables[i])
			i += 1

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
		if  self.refer_tables == None:
			return
		#return
		dc.SetPen(wx.Pen(self.grid_colour,1,style = wx.DOT))
		dc.SetTextForeground(self.grid_colour)
		refer_num = len(self.refer_tables[0])
		if refer_num < 40:
			sparse = 2
		else:
			sparse = refer_num / 20
		max_value = self.refer_tables[0][-1].GetYvalue() 
		max_height= clientRect.height
		count = 0
		for refer_entry in self.refer_tables[0]:
			count +=1
			if refer_num > 20 and count%sparse!=0:
				continue
			y = int((1.0- refer_entry.GetYvalue()/max_value)*max_height)
			dc.DrawLine(0,y,clientRect.width,y)
			dc.DrawText("%.2f"%(float(refer_entry.GetYvalue())),0,y-15)

	def DrawData(self):
		dc = wx.ClientDC(self)
		clientRect = self.GetRect()
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		for signal in self.signals:
			try:
				self.DrawSignal(signal,dc,clientRect)
			except:
				pass

	def DrawSignal(self,signal,dc,clientRect):
		#print "render data....."
		x0 = 1
		x1 = 1
		last_Y0= 1
		max_value = signal.GetMaxValue() 
		max_height= clientRect.height
		for data_ in signal.data:
			if data_.GetYvalue() > 0:
				x1 = x0 + data_.GetLength()
				if data_.GetValid() == True:
					dc.SetPen(wx.Pen(signal.ok_colour,2,style = wx.SOLID))
				else:
					dc.SetPen(wx.Pen(signal.bad_colour,2,style = wx.SOLID))
				Y0=int((1.0-data_.GetYValue()/max_value)*max_height)
				dc.DrawLine(x0,Y0,x0,last_Y0)
				dc.DrawLine(x0,Y0,x1,Y0)
				last_Y0 =  Y0
				x0 = x1
	
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

	def OnSelectEut(self,evt):
		Eut_editor = Eut_Editor(self)
		Eut_editor.ShowModal()
		eut = Eut_editor.GetEut()

		print "start eut show refer...................................................................................................."
		print eut.ShowRefer()
		print "end eut show refer...................................................................................................."
		self.SetEut(eut)
		self.Refresh(True)

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
	#data_panel.SetMaxValue(1400)
	
def pupulate_refer_table():
	refer_table = []
	for x in range(8,203):
		refer_table.append(Refer_Entry(x,205-x+0.2,0.001))
	return refer_table

	
if __name__=='__main__':
	app = wx.App()
	frm = wx.Frame(None)
	frm.SetSize((1400,600))

	signals=[]
	s1 = Signal()
	s2 = Signal()
	signals.append(s1)
	signals.append(s2)
	panel = Signal_Panel(parent=frm,id=-1,size=(1400,600),signals=signals)
	#panel.SetRefer([pupulate_refer_table(),pupulate_refer_table()])
	panel.SetGridColour(wx.Colour(0,250,250,200))
	panel.SetBackgroundColour(wx.Colour(150,50,90,200))
	panel.SetBadColour(wx.Colour(200,0,200))
	populate_data(panel)
	frm.Show()
	app.SetTopWindow(frm)
	app.MainLoop()

