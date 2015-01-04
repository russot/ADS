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

from eut import * 
from test_record import * 
from data_source import Data_Source 
from data_source import MyEvent, EVT_MY_EVENT

from refer_entry import Refer_Entry
from refer_table import Eut_Editor
from pga import gPGA

class Signal(wx.Dialog):
	def __init__(self,window=None,ok_colour="green",bad_colour="red",url=None,table=None):
		super(Signal, self).__init__(parent=None)
		self.window = window
		self.ok_colour = ok_colour
		self.old_ok_colour = ok_colour
		self.bad_colour= bad_colour
		self.old_bad_colour = bad_colour
		self.data = []
		self.cmd_queue=Queue(-1)
		self.data_queue=Queue(-1)
		self.started_flag = False
		self.thread_source = None
		self.data_count = 0
		self.xmax= 0.0
		self.ymax= 0.0
		self.SetRefer_entries(table)
		self.SetUrl(url)
		self.Bind(EVT_MY_EVENT, self.OnNewData)
		self.trig_status = False
		self.record = Test_Record()
		self.status = None
		self.thermo = Thermo()

	def SetPN(self,eut):#extract PN from eut object
		if not isinstance(eut,Eut):
			print "Error: invalid type, should be Eut!"
			return None
		self.record.SetPN(eut.GetPN())
	def SetSN(self,SN):
		self.record.SetSN(SN)

	def UploadSN(self,SN):
		self.window.UploadSN(SN)

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
		if not url:
			return
		self.url = url
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

	def GetUrl(self):
		return self.url

	def SetRefer_entries(self,table):
		if table and isinstance(table,list):
			self.refer_entries = table
			self.refer_entries.sort(key=lambda x:x.GetYvalue())
			#print "signal max value",self.refer_entries[-1].GetYvalue()
			x0 = self.refer_entries[ 0].GetXvalue()
			xn = self.refer_entries[-1].GetXvalue()
			if x0 > xn:
				xmax = x0
			else:
				xmax = xn

			ymin = self.refer_entries[ 0].GetYvalue()
			ymax = self.refer_entries[-1].GetYvalue()
			self.SetMaxValue(xmax,ymax)
			gPGA.find_solution(range_=(ymin,ymax),unit="Ohm")
			for x in self.refer_entries:
				print "signal refers value X,Y",x.GetXvalue(),x.GetYvalue()
		else:
			self.refer_entries = None


	def SetMaxValue(self,xmax,ymax):
		self.xmax= float(xmax)
		self.ymax= float(ymax)

	def GetMaxY(self):
		return self.ymax

	def GetMaxX(self):
		return self.xmax

	def Run(self):
		print "signal running.....\n"
		self.cmd_queue.put("run:")
		while not self.data_queue.empty(): # flush outdated data
			self.data_queue.get()

	def Init_Data(self):
		self.data_count = 0
		self.data = []
		self.window.SetUnknown()
		self.window.Refresh(True)

	def Pause(self):
		print "signal pause.....\n"
		self.cmd_queue.put("stop:")
		while not self.data_queue.empty(): # flush outdated data
			self.data_queue.get()
		#self.Init_Data()

	def OnNewData(self, event):
		if not self.refer_entries:
			return
		out = ''
		pos = 0
		value = 0
		while not self.data_queue.empty():
			item = self.data_queue.get()
			if isinstance(item,str):
				if item.startswith("trigger"):
					print "signal triggering.........."
					self.trig_status = True
					self.Init_Data()
				elif item.startswith("sleep"):
					print "signal sleeping.........."
					if  self.trig_status == True:
						if self.status != False:
							self.window.SetPass()
						self.trig_status = False
						print "saving.........."
						self.record.Save2DBZ()
						self.record.SetDefault()
						SN = self.record.AdjustSN(1)
						self.UploadSN(SN)
						self.Init_Data()
						time.sleep(0.5)
						print "saving ok.........."
				elif item.startswith("0t:"):
					hex_NTC = int(item[3:7],16)
					hex_PT  = int(item[7:11],16)
					(result,temprature,Rntc,Rref)=self.record.SetupThermo(hex_NTC,hex_PT)
					self.window.window.SetThermo(str(round(temprature,3)))
					self.window.window.SetThermoValue(str(round(Rntc,3)))
					self.window.window.SetThermoRefer(str(round(Rref,3)))


			elif isinstance(item,dict):
				self.data_count += 1
				Xvalue,Yvalue_ = item["value"]
				Yvalue = gPGA.find_result4R(Yvalue_)
				#print "Yvalue of R:",Yvalue
				length = item["length"]
				if length > 200:
					length = 50
				refer_entry  = self.GetReferEntry(Xvalue,Yvalue)
				print "new data .............",Xvalue,Yvalue,length
				print "searched refer_entry X,Y:",refer_entry.GetXvalue(),refer_entry.GetYvalue()
				Xprecision,Yprecision,xstatus,ystatus = refer_entry.Validate(Xvalue,Yvalue)
				if xstatus==True and ystatus==True:
					status = True
				else:
					status = False
					self.status = False
					self.window.SetFail()
				record_= Refer_Entry(
						Xvalue=Xvalue,
						Yvalue=Yvalue,
						Xprecision=Xprecision,
						Yprecision=Yprecision,
						valid_status=status)
				record_.SetLength(length)
				self.data.append(record_)
				self.record.AppendRecord(
					Record_Entry(
						refer	= refer_entry,
						record	= record_
						)
					)
				#self.window.DrawData()
				self.window.Refresh(True)


	def GetRefer_X(self,Xvalue=0,Yvalue=0):
		refer_entry =None

		#print len(self.refer_entries),self.refer_entries
		x0 = self.refer_entries[0].GetXvalue()
		xn = self.refer_entries[-1].GetXvalue()
		if x0 > xn:
			Xmax =self.refer_entries[0]
			Xmin =self.refer_entries[-1]
		else:
			Xmax =self.refer_entries[-1]
			Xmin =self.refer_entries[0]
		#print "Xmin,Xmax,X--------------------",Xmin.GetXvalue(),Xmax.GetXvalue(),Xvalue
		if Xvalue >=   Xmax.GetXvalue():
			refer_entry = Xmax
		elif Xvalue <= Xmin.GetXvalue():
			refer_entry = Xmin
		else:
			p0 = self.refer_entries[0]
			for p1 in self.refer_entries:
				x0_ = p0.GetXvalue()
				x1  = p1.GetXvalue()
				delta0 = abs(Xvalue - x0_)
				delta1 = abs(Xvalue - x1)
				#judge being within by comparing delta_sum 
				if (delta0 + delta1) > abs(x1 - x0_):
					p0 = p1
					continue
				#use nearby Yvalue
				y0 = p0.GetYvalue()
				y1 = p1.GetYvalue()
				delta0 = Yvalue - y0
				delta1 = Yvalue - y1
				if abs(delta0) < abs(delta1): 
					refer_entry =  p0
				else:
					refer_entry =  p1
				break
		return refer_entry

	def GetRefer_Y(self,Xvalue=0,Yvalue=0):
		refer_entry= None
		if Yvalue <= self.refer_entries[0].GetYvalue():#outof range
				refer_entry =  self.refer_entries[0]
		elif Yvalue >= self.refer_entries[-1].GetYvalue():#outof range
				refer_entry =  self.refer_entries[-1]
		else:
			p0 = self.refer_entries[0]
			for p1 in self.refer_entries:
				y0 = p0.GetYvalue()
				y1 = p1.GetYvalue()
				delta0 = abs(Yvalue - y0)
				delta1 = abs(Yvalue - y1)
				#judge being within by comparing delta_sum 
				if (delta0 + delta1) > abs(y1 - y0):
					p0 = p1
					continue
				#use nearby Yvalue
				if abs(delta0) < abs(delta1): 
					refer_entry =  p0
				else:
					refer_entry =  p1
				break

		return refer_entry # if not found, return None object

	def GetReferEntry(self,Xvalue=0,Yvalue=0):
		'''Xvalue should be None for using Yvalue as index,
		or integer for using itself as index '''
		refer_entry =None
		if Xvalue != None:# use Xvalue as index
			refer_entry = self.GetRefer_X(Xvalue,Yvalue)
		else:# use Yvalue as index, and table is sorted by Yvalue
			refer_entry = self.GetRefer_Y(None,Yvalue)
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
			if not signal:
				continue
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
			back_color="Black",
			window=None):
		super(Signal_Panel, self).__init__(parent, id,size=size)
		#panel 创建
		self.window = window
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
		#self.Bind(wx.EVT_WHEEL, self.OnZoom)
		#self.Bind(wx.EVT_MENU, self.OnSave,self.menu_save)
		self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

		self.SetScreenXsize(Xsize=1200)

	def OnKeyDown(self, event):
		"""KeyDown event is sent first"""
		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()
		print "raw_code=",raw_code,";modifiers=",modifiers

		if raw_code == 39 or raw_code == 73 :  # <I> = zoom in 
			self.screenXsize += 100 
			print "X zoom in"
		elif raw_code == 37 or raw_code ==79 :# <O> = zomm out
			self.screenXsize -= 100 
			print "X zoom out"
		elif raw_code == 32 or raw_code ==19 :# <O> = zomm out
			self.OnRunStop(event)
		self.Refresh(True)

	def SetScreenXsize(self,Xsize):
		self.screenXsize = Xsize
		print "self.screenXsize",self.screenXsize

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
		self.running_flag = True
		for signal in self.signals:
			if not signal:
				continue
			signal.Run()
			
	def Pause(self):
		self.running_flag = False
		for signal in self.signals:
			if not signal:
				continue
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

	def SetSN(self,SN):
		for signal in self.signals:
			if not signal:
				continue
			signal.SetSN(SN)

	def UploadSN(self,SN):
		self.window.UploadSN(SN)

	def SetEut(self,eut):
		self.eut = eut
		#self.SetRefer(self.eut.GetReferTable())

		refer_tables = self.eut.GetReferTable()
		i=0
		for signal in self.signals:#map refer_tables to signals as 1:1
			try:
				signal.SetRefer_entries(refer_tables[i]) #first
				self.SetScreenXsize(signal.GetMaxX())    #second
				signal.SetPN(eut)
				i += 1
			except Exception,e:
				print "map signal%d's refers failed.."%i
				print e
				pass

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
		if not  self.eut:
			return
		dc = wx.ClientDC(self)
		clientRect = self.GetRect()
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		#return
		dc.SetPen(wx.Pen(self.grid_colour,1,style = wx.DOT))
		dc.SetTextForeground(self.grid_colour)
		refer_num = len(self.eut.GetReferTable()[0])
		if refer_num < 40:
			sparse = 2
		else:
			sparse = refer_num / 20
		max_value = self.eut.GetMaxY()
		max_height= clientRect.height
		count = 0
		for refer_entry in self.eut.GetReferTable()[0]:
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
			if not signal:
				continue
			self.DrawSignal(signal,dc,clientRect)

	def DrawSignal(self,signal,dc,clientRect):
		if not signal.refer_entries:
			return
		x0_ = 1
		x1_ = 1
		maxY= signal.GetMaxY() 
		maxX= signal.GetMaxX() 
		max_height = clientRect.height
		last_Y0    = max_height
		#print "max @ height .....",max_value,max_height
		for data_ in signal.GetData():
			if not data_:
				continue
			if data_.GetYvalue() >= 0:
				x1_ = x0_ + data_.GetLength()
				x0  = x0_ *self.screenXsize/maxX
				x1  = x1_ *self.screenXsize/maxX
				if data_.GetValid() == True:
					dc.SetPen(wx.Pen(signal.ok_colour,2,style = wx.SOLID))
				else:
					dc.SetPen(wx.Pen(signal.bad_colour,2,style = wx.SOLID))
				Y0=int((1.0-data_.GetYvalue()/maxY)*max_height)
				dc.DrawLine(x0,Y0,x0,last_Y0)
				dc.DrawLine(x0,Y0,x1,Y0)
				#print "x0,x1,Y0,last_Y0>>>>>>>>>>>>", x0,x1,Y0,last_Y0
				last_Y0 =  Y0
				x0_ = x1_
	
	def InitValue(self):
		for signal in self.signals:
			signal.data = []

	def OnShowCurrent(self, event):
		x,y = event.GetPosition()
		x0_ = 1
		x1_ = 1
		for signal in self.signals:
			if not signal:
				continue
			maxX= signal.GetMaxX() 
			for data_ in signal.GetData():
				if not data_:
					continue
				if data_.GetYvalue() >= 0:
					x1_ = x0_ + data_.GetLength()
					x0  = x0_ *self.screenXsize/maxX
					x1  = x1_ *self.screenXsize/maxX
					if x >= x0 and x < x1:
						print data_.ShowSensor()
						break
					x0_ = x1_
	
	def OnSelectEut(self,evt):
		Eut_editor = Eut_Editor(self)
		Eut_editor.ShowModal()
		eut = Eut_editor.GetEut()
		if not isinstance(eut,Eut) or not eut.GetPN():
			print u"错误：无效的Sensor!"
			wx.MessageBox(u"错误：无效的Sensor!",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
			return False

		print "start eut show refer...................................................................................................."
		print eut.ShowRefer()
		print "end eut show refer...................................................................................................."
		self.SetEut(eut)
		self.window.SetName(eut.GetPN())
		self.window.SetThermoModel(eut.GetThermoModel())
		self.Refresh(True)
		return True

	def SetUnknown(self):
		self.window.SetUnknown()

	def SetPass(self):
		self.window.SetPass()

	def SetFail(self):
		self.window.SetFail()

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

