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
class Dialog_Setup(wx.Dialog):
	""" configure the run time parameters """
	def __init__(self,  parent=None, 
		id=-1,caption="signal source & UI setup",
		color_ok="green",color_bad="red",
		url_name="127.0.0.1:20001/ep1",
		refer_file="",
		calib_file="",
		points_number=10000):

		super(Dialog_Setup, self).__init__(parent, id , caption)
		self.color_ok = color_ok
		self.color_bad = color_bad
		self.url_name  = url_name
		self.refer_file = refer_file
		self.calib_file = calib_file
		self.points_number = points_number
		
		self.file = wx.TextCtrl(self,-1,self.refer_file,size=(200,-1))
		self.file.Bind(wx.EVT_LEFT_DCLICK, self.OnFileSelect,self.file)
		self.url = wx.TextCtrl(self,-1,self.url_name,size=(200,-1), style=wx.TE_PROCESS_ENTER)
		self.url.Bind(wx.EVT_TEXT_ENTER, self.OnUrlEnter,self.url)
		
		self.points_ctrl = wx.SpinCtrl(self, -1,"%d"%self.points_number, wx.DefaultPosition, (50,-1), wx.SP_ARROW_KEYS,0, 10000, 1)
		
		self.btn_color_ok = wx.Button(self,-1,"GOOD color")
		self.btn_color_bad = wx.Button(self,-1,"BAD color")
		self.btn_color_ok.SetBackgroundColour(self.color_ok)
		self.btn_color_bad.SetBackgroundColour(self.color_bad)
		self.btn_color_ok.Bind(wx.EVT_BUTTON, self.OnColorSelect_Ok,self.btn_color_ok)
		self.btn_color_bad.Bind(wx.EVT_BUTTON, self.OnColorSelect_Bad,self.btn_color_bad)
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.topsizer.Add(wx.StaticText(self, -1,u"input points number"))
		self.topsizer.Add(self.points_ctrl)
		self.topsizer.Add((200,40))
		self.topsizer.Add(wx.StaticText(self, -1,u"Signal refer "))
		self.topsizer.Add(self.file)
		self.topsizer.Add((200,40))
		self.topsizer.Add(wx.StaticText(self, -1,u"Endpoint URL, IP:port/com{0~100}"))
		self.topsizer.Add(self.url)
		
		self.hsizer= wx.BoxSizer(wx.HORIZONTAL|wx.ALIGN_CENTER)# 创建一个分割窗
		self.hsizer.Add((20,20))
		self.hsizer.Add(self.btn_color_ok)
		self.hsizer.Add((20,20))
		self.hsizer.Add(self.btn_color_bad)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.hsizer)		
		
		btnszr = self.CreateButtonSizer(wx.OK|wx.CANCEL) 
		self.topsizer.Add((40,20))
		self.topsizer.Add(btnszr, 0,wx.EXPAND|wx.ALL, 5) 

		self.SetSizer(self.topsizer)
		self.Fit()
		

	def OnUrlEnter(self,evt):
		self.url_name = self.url.GetValue()
		self.Close()


	
	def OnFileSelect(self,evt):
		 
		dlg = wx.FileDialog(None,"select a file ")
		if dlg.ShowModal() == wx.ID_OK:
			self.refer_file = dlg.GetPath()
			self.file.SetValue(self.refer_file)
		dlg.Destroy()             

	def OnColorSelect_Ok(self,evt):
		dlg = wx.ColourDialog(self)
		dlg.GetColourData().SetChooseFull(True)
		if dlg.ShowModal() == wx.ID_OK:
			self.color_ok = dlg.GetColourData().GetColour()
			self.btn_color_ok.SetBackgroundColour(self.color_ok)
		dlg.Destroy()
		
	def OnColorSelect_Bad(self,evt):
		dlg = wx.ColourDialog(self)
		dlg.GetColourData().SetChooseFull(True)
		if dlg.ShowModal() == wx.ID_OK:
			self.color_bad = dlg.GetColourData().GetColour()
			self.btn_color_bad.SetBackgroundColour(self.color_bad)
		dlg.Destroy()
				
	def GetOkColor(self):
		return self.color_ok
	
	def GetBadColor(self):
		return self.color_bad
	
	def GetReferFile(self):
		return self.refer_file

	def GetPointsNumber(self):
		return self.points_number

	def GetUrlName(self):
		return self.url.GetValue()

class Endpoint():
	def __init__(self, url="127.0.0.1:8088/ep1"):
		self.ip=self.SetUrlIP(url) # example string "127.0.0.1"
		self.port =self.SetUrlPort(url) # example integer 8088
		self.ep_index =self.SetUrlEpIndex(url)# example string "ep1" , "ep2" ...
		
	def SetUrlIP(self,url):
		parts = url.split(':')
		return parts[0]
		

	def SetUrlPort(self,url):
		__parts = url.split(':')
		parts = __parts[1].split('/')
		return string.atoi(parts[0])

	def SetUrlEpIndex(self,url):
		__parts = url.split(':')
		parts = __parts[1].split('/')
		return parts[1]


	def GetIP(self):# example string "127.0.0.1"
		return self.ip
		

	def GetPort(self):# example integer 8088
		return self.port

	def GetEpIndex(self):# example string "com1" , "com2" ...
		return self.ep_index



############################################################################################################################################
class Thread_Source(threading.Thread):
	def __init__(self,window,url,queue_in,queue_out):
		threading.Thread.__init__(self)
		self.window = window
		self.url = url 
		self.queue_cmd_in   = queue_in
		self.queue_out = queue_out
		self.endpoint = Endpoint(url)
		self.run_flag =  False
		self.tcpCliSock = socket(AF_INET,SOCK_STREAM)
		self.buffer_recv=[]
		#~ sys.stdout = self
		self.feed_flag = True

	def write(self,TE):
		pass

	def FeedDog(self):
		self.tcpCliSock.send('feed:dog\n') #
		threading.Timer(5,self.FeedDog).start()

	def run(self):#运行一个线程
		threading.Timer(5,self.FeedDog).start()
		self.tcpCliSock.connect( ( self.endpoint.GetIP(), self.endpoint.GetPort() ) )
		self.tcpCliSock.setblocking(0)
		while True:
			self.deal_cmd()
			if self.run_flag == True : # get data  from endpoint by socket, and upload to UI
				self.GetData()
			else: #!!!~~~~~~~~~~~~~~~~~~~~继续接收数据, 以避免程序运行异常~~~~~~~~~~~~~~~~~~~~~~~~~!!!
				try:
					recv_segment = self.tcpCliSock.recv(1024)
				except:
					pass

	def SetEndpoint(self,url):
		self.endpoint.SetUrlIP(url)
		self.endpoint.SetUrlPort(url)
		self.endpoint.SetUrlEpIndex(url)
	def run_adc(self):
		self.tcpCliSock.send("adc:cfg:manual:Y\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:cfg:interval:20\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:cfg:channel:0\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:run:\n")
		time.sleep(0.01)
	
	def sample(self):
		self.tcpCliSock.send("adc:cfg:channel:0\n")
		time.sleep(0.01)
		self.tcpCliSock.send("adc:sample:\n") # request sample
		time.sleep(0.01)		# wait for data from source
		self.GetData()   # data is in self.queue_out 
		return self.queue_out.get() # fetch value from self.queue_out[pos,value),....]

	def calibrate_append(self,value):
		real_value = float(value)
		sample_value = self.sample()[1]  #  return (pos,value)
		self.cailbrate_table.append((real_value,sample_value))
		self.cailbrate_table.sort()
		wx.PostEvent(self.window,MyEvent(60001)) #tell front to update

	def calibrate_delete(self,index):
		del self.cailbrate_table[int(index)]
		self.cailbrate_table.sort()
		wx.PostEvent(self.window,MyEvent(60001)) #tell front to update

	def calibrate_save(self,filename):
		self.cailbrate_table.sort()
		calib_file = open(filename,'w')
		for x in self.cailbrate_table:
			calib_file.write('%5.3f \t %5.3f\n' %(x[0],x[1]))
		calib_file.close()

	def calibrate_load(self,filename):
		self.cailbrate_table=[]
		calib_file = open(filename,'r')
		for line in calib_file.readlines():
			real_value = float(line[:line.find('\t')])
			sample_value = float(line[line.find('\t')+1:])
			self.cailbrate_table.append((real_value,sample_value))
		self.cailbrate_table.sort()
		wx.PostEvent(self.window,MyEvent(60001)) #tell front to update
		calib_file.close()

	def calibrate(self,command):
		if command.startswith("append:"):
			self.calibrate_append(command[len("append:"):])
		elif command.startswith("delete:"):
			self.calibrate_delete(command[len("delete:"):])
		elif command.startswith("save:"):
			self.calibrate_save(command[len("save:"):])
		elif command.startswith("load:"):
			self.calibrate_load(command[len("load:"):])




	def deal_cmd(self):
		if self.queue_cmd_in.empty():
			return
		command = self.queue_cmd_in.get() #get command (from self.queue_cmd_in), then process it and response(to  self.queue_out)
		print "thread_source command: %s" % command
		if command.startswith("stop"): #excute
			self.run_flag =  False
			while not self.queue_out.empty(): # 清除输出队列中的过期数据
				self.queue_out.get()
		#	self.queue_out.put("endpoint stopped by command.\n")
		elif command.startswith("run"):# 
			self.run_flag = True 
			while not self.queue_out.empty(): # 清除输出队列中的过期数据
				self.queue_out.get()
			#~ time.sleep(3)
			self.run_adc()
		elif  command.startswith("get_status"): #excute 
			self.queue_out.put(self.run_flag)
		elif  command.startswith("calibrate:") and self.run_flag==False: #excute 
			self.calibrate(command[len("calibrate:"):])
		#print command + '\n' 
		self.tcpCliSock.send(command + '\n') #

	def GetData(self):
		try:
			recv_segment = self.tcpCliSock.recv(1024)
			#~ print "seg:%s\n"%recv_segment
			while '\n' in recv_segment:
				pos_newline = recv_segment.find('\n')
				self.buffer_recv.append(recv_segment[:pos_newline] )
				raw_data = ''.join(self.buffer_recv)
				if raw_data.startswith("0x:"):
					data_str = raw_data[3:]
					len_data = data_str.find('\0')/8 
					for i in range(0,len_data):
						data_x = int(data_str[i*8:i*8+4],16)
						data_y = int(data_str[i*8+4:i*8+8],16)
						self.queue_out.put((data_x,data_y))
					event = MyEvent(60000) # id is 60000 or any number great than 20000 here
					wx.PostEvent(self.window, event)
				
				self.buffer_recv = []
				try:
					recv_segment = recv_segment[pos_newline+1:]
				except:
					pass
			self.buffer_recv.append(recv_segment)
		
		except:
			pass


############################################################################################################################################
class Signal_Control(wx.Panel):   #3
	def __init__(self,  parent=None,
		     size=(-1,-1),
		     id=-1,
		     color_ok=wx.Color(0,250,0,200),
		     color_bad=wx.Color(250,0,250,200),
		     url_name="127.0.0.1:20001/com6",
		     refer_file = "",
		     calib_file = "",
		     eut_name="qw32edrt44s",
		     eut_serial="10p8-082wj490",
		     points=255,
		     persist=None):
		super(Signal_Control, self).__init__(parent=parent, id=id,size=size)
		#panel 创建
		self.parent__ = parent
		self.color_ok = color_ok  #persist~~~~~~~~~~~~~~~~~~
		self.color_bad = color_bad #persist~~~~~~~~~~~~~~~~~~ 
		self.url_name = url_name #persist~~~~~~~~~~~~~~~~~~
		self.eut_name = eut_name #persist~~~~~~~~~~~~~~~~~~
		self.eut_serial = eut_serial #persist~~~~~~~~~~~~~~~~~~
		self.points = points
		self.persist = persist
		self.refer_table = {}
		self.data_validator =  Data_Validator_Linear()
		self.refer_file = refer_file
		self.calib_file = calib_file
		if refer_file:
			self.SetupRefer(refer_file)
		self.mincircle = 0

		#~ self.tip =btip.BalloonTip(message=u"双右击->>Setup Dialog\n双左击->>run/pause\n")
		#~ self.tip.SetStartDelay(1000)
		#~ self.tip.SetTarget(self)
		


		self.queue_cmd =  Queue(-1) # 创建一个无限长队列,用于输入命令
		self.queue_data=  Queue(-1)# 创建一个无限长队列,用于输出结果
		self.thread_source = Thread_Source(self,self.url_name,self.queue_cmd,self.queue_data)
		self.started_flag = False
		self.running_flag = False
		self.move_flag = False
		self.acc_flag = False
		self.response = ""
		self.cmd_line = ""
		self.init_data()


		self.topsizer = wx.BoxSizer(wx.HORIZONTAL)


		self.data_window = wx.SplitterWindow(self)# 创建一个分割窗
		self.data_window.SetMinimumPaneSize(1)  #创建一个分割窗
		#创建信息栏
		self.info_lane  = wx.ScrolledWindow(self.data_window,-1)
		self.sizer_debug  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.info_lane.SetSizer(self.sizer_debug)
		self.debug_out   = wx.TextCtrl(self.info_lane,-1,style=(wx.TE_MULTILINE|wx.TE_RICH2|wx.HSCROLL) )
		self.sizer_debug.Add(self.debug_out,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		
		#创建信号栏
		self.signal_lane  = wx.ScrolledWindow(self.data_window,-1)
		self.signal_sizer  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.signal_lane.SetSizer(self.signal_sizer)
		self.signal   = Signal_Panel(parent=self.signal_lane,id=-1,size=(1100,800))
		self.signal_sizer.Add(self.signal,1,wx.EXPAND|wx.LEFT|wx.RIGHT)

		#创建信号栏/信息栏 分割窗, 并纳入到窗口管理器
		self.info_lane.Hide()
		self.signal_lane.Hide()
		self.data_window.SplitVertically(self.signal_lane,self.info_lane,-1)
		self.sizer_data_window = wx.BoxSizer(wx.VERTICAL)
		self.sizer_data_window.Add(self.data_window)
		
		self.text_name = wx.TextCtrl(self,-1,eut_name,style=(wx.TE_READONLY))
		self.text_name.SetBackgroundColour( self.GetBackgroundColour())
		self.text_name.SetForegroundColour("purple")
		self.text_serial = wx.TextCtrl(self,-1,eut_serial,style=(wx.TE_READONLY))
		self.text_name1= wx.TextCtrl(self,-1,"eut_name1",style=(wx.TE_READONLY))
		self.text_name2= wx.TextCtrl(self,-1,"eut_name2",style=(wx.TE_READONLY))

		self.sizer_info = wx.BoxSizer(wx.VERTICAL)
		self.sizer_info.Add(wx.StaticText(self,-1,u"型号/名称"))
		self.sizer_info.Add(self.text_name,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer_info.Add((100,20))
		self.sizer_info.Add(wx.StaticText(self,-1,u"ID编号"))
		self.sizer_info.Add(self.text_serial,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer_info.Add((100,20))
		self.sizer_info.Add(wx.StaticText(self,-1,u"温度"))
		self.sizer_info.Add(self.text_name1,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer_info.Add((100,20))
		self.sizer_info.Add(wx.StaticText(self,-1,u"速度"))
		self.sizer_info.Add(self.text_name2,1,wx.EXPAND|wx.LEFT|wx.RIGHT)

		
		self.topsizer.Add(self.sizer_data_window,9)
		self.topsizer.Add(self.sizer_info,1)
		self.SetSizer(self.topsizer)



		#下面进行行为动作绑定
		self.text_name.Bind(wx.EVT_LEFT_DCLICK, self.OnDclick_name,self.text_name)
		self.text_name.Bind(wx.EVT_KEY_DOWN, self.OnKeyRun,self.text_name)
		self.debug_out.Bind(wx.EVT_KEY_DOWN, self.OnClearDebug,self.debug_out)
		self.text_serial.Bind(wx.EVT_LEFT_DCLICK, self.OnDclick_serial,self.text_serial)
		self.text_serial.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown,self.text_serial)
		self.text_serial.Bind(wx.EVT_KEY_UP, self.OnKeyUp,self.text_serial)
		
		#self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowCurrent)
		self.Bind(wx.EVT_RIGHT_DCLICK, self.OnSetup)
		self.Bind(EVT_MY_EVENT, self.OnNewData)

		

		

		#弹出菜单创建
		self.popmenu1 = wx.Menu()
		self.menu_save = self.popmenu1.Append(wx.NewId(), u"保存数据", u"保存数据到数据库" )
		self.menu_run = self.popmenu1.Append(wx.NewId(), u"运行.当前点", u"运行与暂停", kind=wx.ITEM_CHECK)
		self.popmenu1.AppendSeparator()
		self.menu_query_ui = self.popmenu1.Append(wx.NewId(), u"数据库查询", u"组合查询已存储数据")
		self.menu_query_current = self.popmenu1.Append(wx.NewId(), u"当前数据查询", u"查询正在测试的数据")
		self.popmenu1.AppendSeparator()
		self.menu_setup = self.popmenu1.Append(wx.NewId(), u"配置", u"测试参数配置")
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightDown)
		self.Bind(wx.EVT_MENU, self.OnRunStop,self.menu_run)
		self.Bind(wx.EVT_MENU, self.OnShowCurrent,self.menu_query_current)
		self.Bind(wx.EVT_MENU, self.OnQuery_UI,self.menu_query_ui)
		self.Bind(wx.EVT_MENU, self.OnSetup,self.menu_setup)
		self.Bind(wx.EVT_MENU, self.OnSave,self.menu_save)


		self.populate_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnPopulateTimer,self.populate_timer)
		self.toggle_clear = True

		#指定 DEBUG 窗口
		sys.stdout = self.debug_out
		sys.stderr = self.debug_out

	def OnPopulateTimer(self,event):
		#print "repopulate timer"
		self.toggle_clear = not self.toggle_clear
		if self.toggle_clear == True:
			self.signal.InitValue()
		else:
			self.populate_data()	
		#print self.signal.data_store[1].GetValue()
		self.signal.Refresh(True)



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
		last_pos = len(self.signal.data_store)-1
		copy_count = 1
		last_data= self.signal.data_store[0]
		for data in self.signal.data_store[1:]:
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
		self.Data_Persist(self.signal.data_store)

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
		while not self.queue_data.empty():
			raw_data = self.queue_data.get()
			#print raw_data,'\n'
			pos = raw_data[0]
			value = raw_data[1]
			print pos,value,'....\n'
#			self.data_buffer.append(Data_Real(pos,value))
#			#self.data_buffer_size +=1
#
#			if len(self.data_buffer) == 3:
#				
#				pos0 = self.data_buffer[0].GetPos() 
#				pos1 = self.data_buffer[1].GetPos() 
#				pos2 = self.data_buffer[2].GetPos() 
#				pos_delta1 = pos1-pos0
#				pos_delta2 = pos2-pos1
#				if pos_delta1 > 0 and pos_delta2 > 0:  #上行
#					self.data_point_current += 1
#					
#				elif  pos_delta1 < 0 and pos_delta2 < 0:# 下行
#					self.data_point_current  -= 1
#					
#					
#				elif  pos_delta1 > 0 and pos_delta2 < 0: # 上行转下行
#					#先填入空白数据
#					self.direction='down'
#					for data_panel in self.data_store:
#						data_panel.data.append(Data_Validated())
#						data_panel.Refresh(True)
#					self.data_store[self.data_point_current].data[-1]=self.data_store[self.data_point_current].data[-2]
#					self.data_point_current  -= 1  # 转下行
#					
#					
#				elif  pos_delta1 < 0 and pos_delta2 > 0:# 下行转上行, 已完成一个器件测试, 新器件开始测试
#					self.direction='up'
#					data_block=[]
#					self.SetBackgroundColour(self.bgcolor)
#					self.Refresh(True)
#					for data_panel in self.data_store:
#						data_v = data_panel.data[-2]
#						if data_v.GetValue() !=-100:
#							data_block.append(data_v)
#						data_panel.data.append(Data_Validated())
#						data_panel.Refresh(True)
#					for index_ in range(1, len(self.data_store)+1 ):
#						if len(self.data_store[-index_].data) > 1: #重要,边界测试, 未用数据点跳过保存,避免抛出异常.
#							data_v = self.data_store[-index_].data[-2]
#							if data_v.GetValue() != -100:
#								data_block.append(data_v)
#
#					self.Data_Persist(data_block) #保存已完成测试器件的测试数据
#					self.AdjustSerial( +1 ) #更新测试器件的序列流水号, 新器件开始测试
#					self.data_point_current  += 1  # 转上行
#				else:
#					pass
#				self.data_buffer.pop(0)
#				#self.data_buffer_size -= 1
#			else: # 初
#				self.data_point_current += 1
				
			#~ print self.data_point_current
#			data_v = self.data_validator.ValidateData(pos,value)
#			current_data = self.data_store[self.data_point_current]
#			current_data.data[-1]=data_v
#			#~ current_data.SetTip()
#			current_data.Refresh(True)
#			
#			if data_v.GetValid() == False:
#				self.set_fault_color()

	def set_fault_color(self):
		self.signal.SetBackgroundColour(self.color_bad)
				
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


		

		
###########################################################		
		
#	def OnShowCurrent(self, evt):
#		print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#		print self.eut_name , '\t' , self.eut_serial , '\t' , u' 数据清单如下:'
#		print u"位置\t数值\t参考值\t参考精度\t实际精度\t结果"
#		data = []
#		if self.direction=='up':
#			for data_point in self.data_store:
#				data.append( data_point.data[-1] )
#		else:
#			for data_point in self.data_store:
#				data.append( data_point.data[-2] )
#			for index_ in range(1,len(self.data_store) + 1):
#				data.append( self.data_store[-(index_)].data[-1] )
#		for curent_data in data:
#			valid = curent_data.GetValid()
#			pos   = curent_data.GetPos()
#			value= curent_data.GetValue()
#			value_refer= curent_data.GetValue_refer()
#			precision_refer= curent_data.GetPrecision_refer()
#			precision= curent_data.GetPrecision()
#			if value!= -100:
#				print "%d\t%5.2f\t%5.2f\t%5.4f\t%5.4f\t"%(pos, value,value_refer, precision_refer, precision),valid
#	
#		
#		
#		#~ Dialog_Show(data_store=self.data_store, direction=self.direction).ShowModal()
		

		
	def OnRunStop(self, evt):
		if self.running_flag != True:
			self.Run()
			
		else:
			self.Pause()
			
			
	def Run(self):
		print "run.....\n"
		if self.started_flag != True:
			self.thread_source.setDaemon(True)
			self.thread_source.start() #启动后台线程, 与endpoint server进行连接与通信
			self.started_flag = True
			self.menu_setup.Enable(False)#已运行，再不能设置
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

		self.populate_timer.Start(2000)

	def Pause(self):
		print "pause.....\n"
		self.queue_cmd.put("stop:")
		while not self.queue_data.empty(): # 消除输出队列中的过期数据
			self.queue_data.get()
		self.running_flag = False	
		self.text_name.SetBackgroundColour( self.GetBackgroundColour())
		self.text_name.Refresh(True)
		self.init_data()

		self.populate_timer.Stop()

	def OnSetup(self,evt):
		if self.started_flag == True:
			return
		dlg = Dialog_Setup(None,-1,u"请选择配置文件 & 颜色",
					color_ok=self.color_ok,
					color_bad=self.color_bad,
					url_name = self.url_name,
					refer_file=self.refer_file,
					calib_file=self.calib_file,
					)
		if dlg.ShowModal()==wx.ID_OK:
			#~ self.color_ok = dlg.GetOkColor()
			#~ self.color_bad = dlg.GetBadColor()
			self.url_name = dlg.GetUrlName()
			self.thread_source.SetEndpoint(self.url_name)
			new_refer_file = dlg.GetReferFile()

			if self.refer_file != new_refer_file:   	#setup refer first
				self.refer_file = new_refer_file
				self.SetupRefer(self.refer_file)
			if self.color_ok != dlg.GetOkColor():
				self.color_ok = dlg.GetOkColor()
				self.signal.SetOKColour(self.color_ok)
			if self.color_bad != dlg.GetBadColor():
				self.color_bad = dlg.GetBadColor()
				self.signal.SetBadColour(self.color_bad)

		
		print self.data_validator.GetMaxValue()
		dlg.Destroy() #释放资源
			

	def SetupRefer(self,refer_file): # format as "D,V,e",  202,44.8,1
		ref_cfg = open(refer_file,'r')
		if  not ref_cfg.readline().startswith("#signal refer table"):
			print "refer file format not right!\
			\nThe first line should be \"#signal refer table\", and \"displacement,value,error\" each following line"
			return 
			
		refer_table = {}
		for line in ref_cfg.readlines():
			line = line.replace(" ","").replace("\t","")# 
			element = line.split(',')
			key   = string.atoi(element[0])
			value = string.atof(element[1])
			error = string.atof(element[2])
			refer_table[key] = (key,value,error)
		self.data_validator.SetupTable(refer_table=refer_table)
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

	def OnDclick_serial(self, evt):
		dlg =  wx.TextEntryDialog(None,u"请输入序列号",u"序列号输入",self.text_serial.GetValue(),style=wx.OK|wx.CANCEL)
		if dlg.ShowModal() == wx.ID_OK :
			self.Set_Serial(dlg.GetValue())
		dlg.Destroy()

	def Set_Name(self, name):
		self.eut_name = name 
		self.text_name.SetValue(name)


	def Set_Serial(self, serial):
		self.eut_serial = serial
		self.text_serial.SetValue(serial)


	def populate_data(self):
		rand_value_all = 0 
		value_ = 0
		for pos in range (1,1200):
			base = (int(pos)/int(100)*100) + 50
			if pos%100 < 10: 
				rand_value_once= random.random()* base / 99.99
				value= rand_value_once + base 
			else:
				if pos%100 ==10:
					rand_value_all = random.random() * base /99.90
					value_= rand_value_all + base 
				value = value_
			precision = float(value)/float(base) 
			if precision > 0.99 and precision < 1.01:
				valid = True
				self.signal.SetBackgroundColour("black")
			else:
				valid = False
				self.signal.SetBackgroundColour("red")

			data_v = Data_Validated(valid= valid,
					pos=pos,
					value= value,
					value_refer=0.0,
					precision_refer=0.0,
					precision=precision,
					)
			self.signal.SetValue(pos,data_v)
		self.signal.SetMaxValue(1400)


############################################################################################################################################
if __name__=='__main__':
	app = wx.App()
	frm = wx.Frame(None)
	frm.SetSize((1400,800))
	queue_in_ = Queue(-1)
	queue_out_= Queue(-1)
	
	sql = Thread_Sqlite(db_name="sqlite3_all.db",queue_in=queue_in_, queue_out=queue_out_) 
	sql.setDaemon(True)
	sql.start()
	
	
	panel = Signal_Control(parent=frm,
					size = (1400,800),
					url_name="127.0.0.1:20001/com6",
					eut_name="Eawdfr2s3WEE",
					eut_serial="10p8-082wj490",
					refer_file="./refer_table.cfg",
					calib_file="",
					points = 290,
					persist =(queue_in_, queue_out_)
					)
	populate_data(panel.signal)
	frm.Show()
	app.SetTopWindow(frm)
	
	app.MainLoop()

