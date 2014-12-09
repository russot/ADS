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
import wx.lib.imagebrowser as imagebrowser
from dialog_query import Dialog_Query
import wx.lib.newevent
from signal_panel import Signal_Panel,Signal
import signal_panel

import server_endpoints_usb

from refer_table import *
from data_source import Data_Source 
from data_source import MyEvent, EVT_MY_EVENT


class Result_Ctrl(wx.Control):
	def __init__(self,parent=None,id=-1,size=(400,400),image_fn=None):
		super(Result_Ctrl, self).__init__(parent, id,size=size,style=wx.NO_BORDER)
		self.back_color = parent.GetBackgroundColour()
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.ok_status = True
		self.timer = wx.Timer(self,-1)
		self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
		self.timer.Start(1000,False)

	def OnPaint(self,event):
		self.redraw()
	
	def OnTimer(self,event):
		self.Refresh(True)
	
	def redraw(self):
		dc = wx.PaintDC(self)
		brush = wx.Brush(self.back_color)
		dc.SetBackground(brush)
		if self.ok_status:
			result_str = "PASS"
			dc.SetTextForeground(wx.Colour(0,200,0,200))
		else:
			result_str= "FAIL"
			dc.SetTextForeground(wx.Colour(255,0,0,200))
		font =self.GetFont()
		font.SetPointSize(30)
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		dc.SetFont(font)
		dc.DrawText(result_str,0,0)
		#now,show time 
		font.SetPointSize(12)
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		dc.SetFont(font)
		dc.SetTextForeground(wx.Colour(20,90,90,200))
		time_str = time.strftime('%Y-%m-%d',time.localtime(time.time()))
		dc.DrawText(time_str,0,42)
		time_str = time.strftime('%H:%M:%S',time.localtime(time.time()))
		dc.DrawText(time_str,0,62)
		
	def SetPass(self):
		self.ok_status = True

	def SetFail(self):
		self.ok_status = False

		




############################################################################################################################################
class Signal_Control(wx.Panel):   #3
	def __init__(self,  parent=None, size=wx.DefaultSize, id=-1,
		     url = "",
		     eut_name="demo",
		     eut_serial="demo",
		     persist=None):
		super(Signal_Control, self).__init__(parent=parent, id=id,size=size)
		#panel 创建
		self.eut_name = eut_name #persist~~~~~~~~~~~~~~~~~~
		self.eut_serial = eut_serial #persist~~~~~~~~~~~~~~~~~~
		self.url_name = url
		self.persist = persist
		self.mincircle = 0
		self.data_count = 0

		#~ self.tip =btip.BalloonTip(message=u"双右击->>Setup Dialog\n双左击->>run/pause\n")
		#~ self.tip.SetStartDelay(1000)
		#~ self.tip.SetTarget(self)
		


		print "sig ctrl init1"
		self.queue_cmd =  Queue(-1) # 创建一个无限长队列,用于输入命令
		self.queue_data=  Queue(-1)# 创建一个无限长队列,用于输出结果
		self.thread_source = Data_Source(self,self.url_name,self.queue_cmd,self.queue_data)
		self.started_flag = False
		self.running_flag = False
		self.move_flag = False
		self.acc_flag = False
		self.response = ""
		self.cmd_line = ""
		self.init_data()


		# 创建字体改善UI
		font = self.GetFont()
		font.SetPointSize(13)
		
		print "sig ctrl init2"
		self.topsizer = wx.BoxSizer(wx.HORIZONTAL)

		# 创建主分割窗
		self.sp_window = wx.SplitterWindow(self)
		self.sp_window.SetMinimumPaneSize(1)  
		#创建上分割窗
		self.data_window = wx.SplitterWindow(self.sp_window)#创建一个分割窗
		self.data_window.SetMinimumPaneSize(1)  #创建一个分割窗
		#创建debug窗口栏
		self.debug_lane  = wx.ScrolledWindow(self.sp_window)
		#self.debug_lane.SetScrollbars(1,1,100,100)
		self.sizer_debug  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.debug_lane.SetSizer(self.sizer_debug)
		self.debug_out   = wx.TextCtrl(self.debug_lane,-1,style=(wx.TE_MULTILINE|wx.TE_RICH2|wx.HSCROLL) )
		self.sizer_debug.Add(self.debug_out,1,wx.EXPAND|wx.ALL)

		#创建信息栏
		print "sig ctrl init3"
		self.info_lane  = wx.ScrolledWindow(self.data_window,-1)
		self.info_lane.SetScrollbars(1,1,100,100)
		self.sizer_sheet  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.info_lane.SetSizer(self.sizer_sheet)
		self.info_sheet   = Refer_Sheet(self.info_lane,None)
		self.sizer_sheet.Add(self.info_sheet,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		
	
		#创建信号栏
		self.signal_panel_lane  = wx.ScrolledWindow(self.data_window,-1)
		self.signal_panel_lane.SetScrollbars(1,1,100,100)
		self.signal_panel_sizer  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.signal_panel_lane.SetSizer(self.signal_panel_sizer)
		signals=[]
		signals.append(Signal())
		signals.append(Signal())
		self.signal_panel   = Signal_Panel(parent=self.signal_panel_lane,id=-1,size=wx.DefaultSize,signals=signals)
		self.signal_panel_sizer.Add(self.signal_panel,1,wx.EXPAND|wx.LEFT|wx.RIGHT)

		#加入信号栏/信息栏 分割窗
		self.data_window.SplitVertically(self.signal_panel_lane,self.info_lane,-10)
		self.sp_window.SplitHorizontally(self.data_window,self.debug_lane,-100)

		self.text_name = wx.TextCtrl(self,-1,eut_name,style=(wx.TE_READONLY))
		self.text_name.SetBackgroundColour( self.GetBackgroundColour())
		self.text_name.SetForegroundColour("purple")
		self.text_serial = wx.TextCtrl(self,-1,eut_serial,style=(wx.TE_READONLY))
		self.text_therm= wx.TextCtrl(self,-1,"eut_name1",style=(wx.TE_READONLY))
		self.text_NTC= wx.TextCtrl(self,-1,"eut_name2",style=(wx.TE_READONLY))
		self.text_NTC.Bind(wx.EVT_KEY_UP, self.OnPass)

		self.sizer_info = wx.BoxSizer(wx.VERTICAL)
		for label_name,txt in ((u"型号/PN",self.text_name),
				(u"编号/SN",self.text_serial),
				(u"温度/Temprature.",self.text_therm),
				(u"热敏电阻/NTC Resistor",self.text_NTC),):
			label = wx.StaticText(self,-1,label_name)
			label.SetFont(font)
			txt.SetFont(font)
			self.sizer_info.Add(label)
			self.sizer_info.Add(txt,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
			self.sizer_info.Add((100,20))

		self.sizer_info.Add((100,300))
		self.result = Result_Ctrl(parent=self,id=-1)
		self.sizer_info.Add(self.result,2,wx.EXPAND|wx.LEFT|wx.RIGHT)

		
		self.SetSizer(self.topsizer)
		self.topsizer.Add(self.sp_window,15,wx.EXPAND|wx.ALL)
		self.topsizer.Add(self.sizer_info,2)

		self.Eut_editor = Refer_Editor()



		#下面进行行为动作绑定
		self.text_name.Bind(wx.EVT_LEFT_DCLICK, self.OnDclick_name)
		self.text_name.Bind(wx.EVT_KEY_DOWN, self.OnKeyRun)
		self.debug_out.Bind(wx.EVT_KEY_DOWN, self.OnClearDebug)
		self.text_serial.Bind(wx.EVT_LEFT_DCLICK, self.OnDclick_serial)
		self.text_serial.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.text_serial.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		
		#self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowCurrent)
		self.Bind(EVT_MY_EVENT, self.OnNewData)

		

		

		print "sig ctrl init4"
		#弹出菜单创建
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
		self.Bind(wx.EVT_MENU, self.OnQuery_UI,self.menu_query_ui)
		self.Bind(wx.EVT_MENU, self.OnSetup,self.menu_setup)
		self.Bind(wx.EVT_MENU, self.OnSelectEut,self.menu_eut)
		self.Bind(wx.EVT_MENU, self.OnSave,self.menu_save)


		print "sig ctrl init5"
		#self.Bind(wx.EVT_TIMER, self.OnPopulateTimer,self.populate_timer)
		#self.Bind(wx.EVT_TIMER, self.OnNewData,self.populate_timer)

		#指定 DEBUG 窗口
		sys.stdout = self.debug_out
		sys.stderr = self.debug_out

	def OnPopulateTimer(self,event):
		#print "repopulate timer"
		self.toggle_clear = not self.toggle_clear
		if self.toggle_clear == True:
			self.signal_panel.InitValue()
		else:
			self.populate_data()	
		self.signal_panel.Refresh(True)


	def OnPass(self,event):
		try:
			self._result = not (self._result)
			if self._result:
				self.result.SetPass()
			else:
				self.result.SetFail()

			self.result.Refresh(True)
		except:
			pass


	def OnQuery_UI(self,event):
		try:
			print os.startfile('dialog_query.py') 
		except:
			pass

	def OnClearDebug(self,event):
		"""KeyDown event is sent first"""
		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		if raw_code == 75 and modifiers==2: # ctrl+k to clear Debug text
			self.debug_out.SetValue("")

	def OnShowCurrent(self,event):
		print "************************************************************\n"
		print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		print u"位置\t数值\t参考值\t参考精度\t  实际精度\t结果"
		out = ''
		x_pos = 0
		last_pos = len(self.signal_panel.data_store)-1
		copy_count = 1
		last_data= self.signal_panel.data_store[0]
		for data in self.signal_panel.data_store[1:]:
			x_pos += 1
			if data.GetValue() == last_data.GetValue() and x_pos!=last_pos:
				copy_count += 1
			elif last_data.GetValue() > 0:
				valid = last_data.GetValid()
				value = last_data.GetValue()
				position   = last_data.GetPos()
				value_refer= last_data.GetValue_refer()
				precision_refer= last_data.GetPrecision_refer()
				precision= last_data.GetPrecision()
				#输出到控制台
				if valid:
					valid_view = u"Pass"

				else:
					valid_view = u"Fail"
					self.debug_out.SetStyle( self.debug_out.GetNumberOfLines(),
							-1,
							wx.TextAttr("yellow","red"))
				line_cur  =  "%4d\t"   % position
				line_cur +=  "%5.2f\t" % value
				line_cur +=  "%5.2f\t" % value_refer
				line_cur +=  "%5.4f\t    " % precision_refer
				line_cur +=  "%5.4f \t"% precision
				line_cur +=  "%s\n"   % valid_view
				print line_cur 
				self.debug_out.SetStyle( self.debug_out.GetNumberOfLines(),
						-1,
						wx.TextAttr("black","white"))

				copy_count = 1
			last_data = data

		
	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)

	def init_data(self):
		self.data_buffer = []
		self.data_buffer_size = 0
		self.data_point_current = -1

	def OnKeyRun(self, event):
		"""KeyDown event is sent first"""

		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		if raw_code == 65 and modifiers==2:
			self.OnRunStop(event)
		elif raw_code == 82 and modifiers==2:
			self.Run()
		elif raw_code == 83 and modifiers==2:
			self.Pause()
		elif raw_code == 65 and modifiers==6:  # ctrl+shift+A , Add by one
			self.AdjustMincircle( +2 )
		elif raw_code == 83 and modifiers==6:  # ctrl+shift+S , Sub by one
			self.AdjustMincircle( -2 )

	def AdjustMincircle(self,value):
		self.mincircle += value
		if self.mincircle < 20:
			self.mincircle = 20
		cmd_mincircle="setup:%d" % self.mincircle
		self.queue_cmd.put(cmd_mincircle)
		print cmd_mincircle

	def AdjustSerial(self,x):
		index = -1
		digits =  0
		while  self.eut_serial[index:].isdigit():
			index -= 1
			digits +=1
		serial_prefix = self.eut_serial[:index+1]
		serial_num = string. atoi(self.eut_serial[index+1:])
		serial_num += int(x)
		self.eut_serial = serial_prefix + '%0*d'%(digits, serial_num)
		self.text_serial.SetValue(self.eut_serial)


	def MoveX(self,direction):
		if direction == "+" :
			print "move_x +"
			self.queue_cmd.put("move:plus")
		else:
			print "move_x -"
			self.queue_cmd.put("move:minus")
		self.move_flag = True
		self.acc_flag = True

	def OnKeyUp(self, event):
		"""KeyDown event is sent first"""

		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()
		print raw_code,"<-->",modifiers

		if raw_code == 187 or raw_code == 189:  # ctrl+alt+A , Add by one
			self.acc_flag = False
		if (raw_code == 187 or raw_code == 189) and (self.move_flag == True):  # ctrl+alt+A , Add by one
			self.move_flag = False
			self.acc_flag = False
			print "move_x stopped..."
			self.queue_cmd.put("stop:")
	def OnSave(self, event):
		"""KeyDown event is sent first"""
		print "save data"
		self.Data_Persist(self.signal_panel.data_store)

	def OnKeyDown(self, event):
		"""KeyDown event is sent first"""

		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		if raw_code == 65 and modifiers==3:  # ctrl+alt+A , Add by one
			self.AdjustSerial( +1 )
		elif raw_code == 83 and modifiers==3:  # ctrl+alt+S , Sub by one
			self.AdjustSerial( -1 )
		elif raw_code == 187 and modifiers==3 and self.move_flag != True:  # ctrl+alt+= , move forward
			self.MoveX("+")
		elif raw_code == 189 and modifiers==3 and self.move_flag != True:  # ctrl+alt+- , move backward
			self.MoveX("-")
		elif raw_code == 187 and modifiers==3 and self.acc_flag != True:  # ctrl+alt+= , move forward
			self.acc_flag = True
		elif raw_code == 189 and modifiers==3 and self.acc_flag != True:  # ctrl+alt+- , move backward
			self.acc_flag = True
		#~ elif raw_code == 65 and modifiers==6:  # ctrl+shift+A , Add by ten
			#~ self.AdjustSerial( +10 )
		#~ elif raw_code == 83 and modifiers==6:  # ctrl+shift+S , Sub by ten
			#~ self.AdjustSerial( -10 )
		#~ elif raw_code == 65 and modifiers==7:  # ctrl+alt+shift+A , Add by hundred
			#~ self.AdjustSerial( +100 )
		#~ elif raw_code == 83 and modifiers==7:  # ctrl+alt+shift+S , Sub by hundred
			#~ self.AdjustSerial( -100 )


	def OnNewData(self, event):
		out = ''
		pos = 0
		value = 0
		while not self.queue_data.empty():
			item = self.queue_data.get()
			if isinstance(item,str):
				if item.startswith("trigger"):
					self.data_count = 0
					self.signal_panel.InitValue()
					self.signal_panel.Refresh()
			if isinstance(item,dict):
				self.data_count += 1
				valueX,valueY = item["value"]
				length = item["length"]
				if length > 1000:
					length = 50
				data_v = Data_Validated(valid= True,
					pos=valueX,
					value= valueY,
					value_refer=0.0,
					precision_refer=0.0,
					precision=0.0,
					)
				data_v.SetLength(length)
				self.signal_panel.SetValue(self.data_count,data_v)
				self.signal_panel.DrawData()
				#self.signal_panel.Refresh()
	

	def set_fault_color(self):
		self.signal_panel.SetBackgroundColour(self.color_bad)
				
	def Data_Persist(self,data_block):
		bytes_block = ''
		data_valid = True
		for data in data_block:
			bytes_block += struct.pack('I5f',
								data.GetValid(),
								data.GetPos(),
								data.GetValue(),
								data.GetValue_refer(),
								data.GetPrecision_refer(),
								data.GetPrecision()
								)
			if  data.GetValid()==0:
				data_valid = False
			
		cmd =  ("data:",("save:",(self.eut_name,self.eut_serial,data_valid, bytes_block))) 
		self.persist[0].put( cmd)


		

		
	def OnRunStop(self, evt):
		if self.running_flag != True:
			self.Run()
			
		else:
			self.Pause()
			
			
	def Run(self):
		print "run.....\n"
		if self.started_flag != True:
			self.thread_source = Data_Source(self,self.url_name,self.queue_cmd,self.queue_data)
			self.thread_source.setDaemon(True)
			self.thread_source.start() #启动后台线程, 与endpoint server进行连接与通信
			self.started_flag = True
			#self.menu_setup.Enable(False)#已运行，再不能设置
			pos_slash = self.url_name.find('/')
			serial_name = self.url_name[pos_slash+1:]
			open_cmd = "open:%s:%s"%(serial_name,'115200')
			print open_cmd
			self.queue_cmd.put(open_cmd)
		while not self.queue_data.empty(): # 消除输出队列中的过期数据
			self.queue_data.get()
		self.queue_cmd.put("run:")
		self.running_flag = True
		self.text_name.SetBackgroundColour("green")
		self.text_name.Refresh(True)

		#self.populate_timer.Start(20)

	def Pause(self):
		print "pause.....\n"
		self.queue_cmd.put("stop:")
		while not self.queue_data.empty(): # 消除输出队列中的过期数据
			self.queue_data.get()
		self.running_flag = False	
		self.text_name.SetBackgroundColour( self.GetBackgroundColour())
		self.text_name.Refresh(True)
		self.init_data()


	def OnSetup(self,evt):
		self.signal_panel.Setup()

	def OnSelectEut(self,evt):
		self.Eut_editor.Show()

	def OnOptions(self,event):

		self.signal_panel.SetReferColour(wx.Colour(0,250,250,200))
		self.signal_panel.SetBackgroundColour(wx.Colour(150,50,90,200))
		self.signal_panel.SetRefer(signal_panel.pupulate_refer_table())

		self.signal_panel.SetMaxValue(1200)

	def SetupRefer(self,refer_file): # format as "D,V,e",  202,44.8,1
		ref_cfg = open(refer_file,'r')
		if  not ref_cfg.readline().startswith("#signal refer table"):
			print "refer file format not right!\
			\nThe first line should be \"#signal refer table\", and \"displacement,value,error\" each following line"
			return 
			
		refer_table = []
		for line in ref_cfg.readlines():
			line = line.replace(" ","").replace("\t","")# 
			element = line.split(',')
			key   = string.atoi(element[0])
			value = string.atof(element[1])
			precision = string.atof(element[2])
			refer_table.append ([key,value,precision])
		#self.data_validator.SetupTable(refer_table=refer_table)
		#~ for x in self.refer_table.values():
			#~ print x.GetValue(),'\n'
			#~ self.data_1 = Data_Point(parent=self,id =-1,size=(5,45), data=x[1],pos=x[0],max_value=100,ok_color=self.color_ok,bad_color=self.color_bad)
			#~ self.data_store.append(self.data_1 )
			#~ self.sizer_data.Add(self.data_1 ,2,wx.EXPAND|wx.RIGHT,2)


	def OnDclick_name(self, evt):
		dlg =  wx.TextEntryDialog(None,u"请输入产品名称",u"名称输入",self.text_name.GetValue(),style=wx.OK|wx.CANCEL)
		if dlg.ShowModal() == wx.ID_OK :
			self.Set_Name(dlg.GetValue())
		dlg.Destroy()
		self.result.Refresh()

	def OnDclick_serial(self, evt):
		dlg =  wx.TextEntryDialog(None,u"请输入序列号",u"序列号输入",self.text_serial.GetValue(),style=wx.OK|wx.CANCEL)
		if dlg.ShowModal() == wx.ID_OK :
			self.Set_Serial(dlg.GetValue())
		dlg.Destroy()
		self.result.SetFail()
		self.result.Refresh()

	def Set_Name(self, name):
		self.eut_name = name 
		self.text_name.SetValue(name)


	def Set_Serial(self, serial):
		self.eut_serial = serial
		self.text_serial.SetValue(serial)


#	def populate_data(self):
#		rand_value_all = 0 
#		value_ = 0
#		for pos in range (1,1200):
#			base = (int(pos)/int(100)*100) + 50
#			if pos%100 < 10: 
#				rand_value_once= random.random()* base / 99.99
#				value= rand_value_once + base 
#			else:
#				if pos%100 ==10:
#					rand_value_all = random.random() * base /99.90
#					value_= rand_value_all + base 
#				value = value_
#			precision = float(value)/float(base) 
#			if precision > 0.99 and precision < 1.01:
#				valid = True
#				self.signal.SetBackgroundColour("black")
#			else:
#				valid = False
#				self.signal.SetBackgroundColour("red")
#
#			data_v = Data_Validated(valid= valid,
#					pos=pos,
#					value= value,
#					value_refer=0.0,
#					precision_refer=0.0,
#					precision=precision,
#					)
#			self.signal.SetValue(pos,data_v,0)
#			data_v_ = Data_Validated(valid= valid,
#					pos=pos,
#					value= value+50,
#					value_refer=0.0,
#					precision_refer=0.0,
#					precision=precision,
#					)
#			self.signal.SetValue(pos,data_v_,1)
#		self.signal.SetMaxValue(1400)
#

############################################################################################################################################
if __name__=='__main__':
	app = wx.App()
	frm = wx.Frame(None)
	frm.SetSize((1400,800))
	persist =(Queue(-1),Queue(-1))
	
	sql = Thread_Sqlite(db_name="sqlite3_all.db",queue_in=persist[0], queue_out=persist[1]) 
	sql.setDaemon(True)
	sql.start()

	port = '%d'%(server_endpoints_usb.PORT)
	ip = '%s'%(server_endpoints_usb.IP_ADDRESS)
	URL = ip+':'+port+'/'+'usb1'
	print URL
	
	
	panel = Signal_Control(parent=frm,
				size = (1200,700),
				id=-1,
				url = URL,
				eut_name="Eawdfr2s3WEE",
				eut_serial="10p8-082wj490",
				persist =persist)
	#panel.populate_data()
	#panel.signal.SetRefer(signal_panel.pupulate_refer_table())
	panel.signal_panel.SetGridColour(wx.Colour(0,250,250,200))
	panel.signal_panel.SetBackgroundColour(wx.Colour(150,50,90,200))
	panel.signal_panel.SetBadColour(wx.Colour(200,0,200))
	frm.Show()
	app.SetTopWindow(frm)
	
	app.MainLoop()

