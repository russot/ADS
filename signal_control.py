#-*- coding: utf-8 -*-
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

import wx.lib.agw.balloontip as btip
import struct 
from thread_sqlite import Thread_Sqlite
import config_db
import sqlite3 as sqlite
import wx.lib.scrolledpanel as scrolledpanel
import wx.lib.imagebrowser as imagebrowser
import wx.lib.newevent

import server_endpoints

from refer_sheet import Refer_Sheet 
from refer_table import * 
from data_source import Data_Source 
from data_source import MyEvent, EVT_MY_EVENT
import util


class Result_Ctrl(wx.Control):
	def __init__(self,parent=None,id=-1,size=(100,100),image_fn=None):
		super(Result_Ctrl, self).__init__(parent, id,size=size,style=wx.NO_BORDER)
		self.back_color = parent.GetBackgroundColour()
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.ok_status = None
		#self.ok_status = True
		self.timer = wx.Timer(self,-1)
		self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
		self.Bind(wx.EVT_LEFT_DCLICK,self.OnToggle)
		self.timer.Start(1000,False)
		self.vout = 0.001
		self.data_rates = 0

	def OnPaint(self,event):
		self.redraw()
	
	def OnTimer(self,event):
		self.Refresh(True)
	
	def OnToggle(self,event):
		if self.ok_status == True:
			self.ok_status = False
		elif self.ok_status == False:
			self.ok_status = None 
		elif self.ok_status == None:
			self.ok_status = True 
		self.Refresh(True)
	
	def redraw(self):
		dc = wx.PaintDC(self)
		brush = wx.Brush(self.back_color)
		dc.SetBackground(brush)
		if self.ok_status == True:
			result_str = u"PASS"
			dc.SetTextForeground(wx.Colour(0,200,0,200))
		elif self.ok_status == False:
			result_str= u" N G "
			dc.SetTextForeground(wx.Colour(255,0,0,200))
		else:
			result_str= u"□□□□"
			dc.SetTextForeground(wx.Colour(0,0,200,200))
		font =self.GetFont()
		font.SetPointSize(35)
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		dc.SetFont(font)
		dc.DrawText(result_str,0,-5)
		#now,show Time & Vout
		font.SetPointSize(13)
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		dc.SetFont(font)
		dc.SetTextForeground(wx.Colour(20,90,90,200))
		time_str = time.strftime('%Y-%m-%d',time.localtime(time.time()))
		dc.DrawText(time_str,0,45)
		time_str = time.strftime('%H:%M:%S',time.localtime(time.time()))
		dc.DrawText(time_str,0,65)
		data_rates_str = '%d pts./sec.'%self.data_rates
		dc.DrawText(data_rates_str,0,85)
		dc.SetTextForeground(wx.Colour(200,90,200,200))
		vout_str = 'Vout:%02.3fV'%self.vout
		dc.DrawText(vout_str,0,105)
		
	def SetUnknown(self):
		self.ok_status = None

	def SetPass(self):
		self.ok_status = True

	def SetFail(self):
		self.ok_status = False

	def SetVout(self,vout):
		self.vout = vout

	def SetDataRates(self,data_rates):
		self.data_rates = data_rates


############################################################################################################################################
class Signal_Control(wx.Panel):   #3
	def __init__(self,  parent=None, size=wx.DefaultSize, id=-1,
		     url = "",
		     eut_name="demo",
		     eut_serial="demo",
		     ):
		super(Signal_Control, self).__init__(parent=parent, id=id,size=size)
		#panel 创建
		self.eut_serial = eut_serial #persist~~~~~~~~~~~~~~~~~~
		self.parent = parent
		self.url_name = url
		self.mincircle = 0
		self.data_count = 0
		self.move_flag = False
		self.acc_flag = False

		
		Dx,Dy = wx.DisplaySize()
		# 创建主分割窗
		self.sizer_info = wx.BoxSizer(wx.VERTICAL)
		#self.sp_window = wx.SplitterWindow(parent=self,size=(Dx-130,Dy-20))
		#创建上分割窗
		self.sp_window = wx.SplitterWindow(parent=self,size=(Dx-130,Dy-20),style=wx.wx.SP_LIVE_UPDATE)
		self.data_window = wx.SplitterWindow(parent=self.sp_window,style=wx.SP_LIVE_UPDATE)
		self.data_window.SetMinimumPaneSize(1)
		self.sp_window.SetMinimumPaneSize(1)
		self.debug_window  = wx.ScrolledWindow(self.sp_window) #创建debug窗口栏
		self.debug_window.SetScrollbars(1,1,100,100)
		self.sizer_debug  = wx.BoxSizer(wx.VERTICAL)
		self.debug_window.SetSizer(self.sizer_debug)
		self.debug_out   = wx.TextCtrl(self.debug_window,-1,style=(wx.TE_MULTILINE|wx.TE_RICH2|wx.HSCROLL) )
		self.debug_out.SetEditable(False)
		self.sizer_debug.Add(self.debug_out,1,wx.EXPAND|wx.ALL)

		#指定 DEBUG 窗口
		#sys.stdout = self.debug_out
		#sys.stderr = self.debug_out
		print "\nsignal window size: ",size
		#创建信息栏
		#print "sig ctrl init3"
		self.info_lane  = wx.ScrolledWindow(self.data_window,-1)
		self.info_lane.SetScrollbars(1,1,100,100)
		self.sizer_sheet  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.info_lane.SetSizer(self.sizer_sheet)
		self.info_sheet   = Refer_Sheet(self.info_lane,None)
		self.info_sheet.AutoSizeColumns(True)
		self.sizer_sheet.Add(self.info_sheet,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		
	
		#创建信号栏
		font = self.GetFont()
		font.SetPointSize(11)
		self.text_name = wx.TextCtrl(self,-1,eut_name,style=(wx.TE_READONLY))
		self.text_serial = wx.TextCtrl(self,-1,eut_serial,style=(wx.TE_READONLY))
		self.text_thermo = wx.TextCtrl(self,-1,"N/A",style=(wx.TE_READONLY))
		self.text_NTC_ref= wx.TextCtrl(self,-1,"N/A",style=(wx.TE_READONLY))
		self.text_NTC_measured = wx.TextCtrl(self,-1,"N/A",style=(wx.TE_READONLY))
		self.labels= []
		for label_name,txt in ((u"料号/PN",self.text_name),
				(u"编号/SN",self.text_serial),
				(u"温度/TEMP",self.text_thermo),
				(u"热敏电阻参考\nNTC refer value",self.text_NTC_ref),
				(u"热敏电阻实测\nNTC measured",self.text_NTC_measured),):
			label=wx.StaticText(self,-1,label_name)
			self.labels.append(label)
			label.SetFont(font)
			txt.SetFont(font)
			self.sizer_info.Add(label)
			self.sizer_info.Add(txt,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
			self.sizer_info.Add((10,20))
		self.signal_window  = wx.ScrolledWindow(self.data_window,-1)
		self.signal_window.SetScrollbars(1,1,100,100)
		self.signal_panel_sizer  = wx.BoxSizer(wx.VERTICAL)# 创建一个窗口管理器
		self.signal_window.SetSizer(self.signal_panel_sizer)
		signals=[]
		s1 =Signal(url="127.0.0.1:8088/usb1/1")
		s2 = None
		print "\nset record init"
		self.info_sheet.SetEut(s1.record)
		self.signal_panel   = Signal_Panel(parent=self.signal_window,id=-1,size=(Dx,Dy),signals=[s1,s2],window=self)
		self.signal_panel_sizer.Add(self.signal_panel,1,wx.EXPAND|wx.LEFT|wx.RIGHT)

		#加入信号栏/信息栏 分割窗
		#self.data_window.SplitVertically(self.signal_window,self.info_lane,Dx-500)
		#self.sp_window.SplitHorizontally(self.data_window,self.debug_window,Dy-20)
		self.data_window.SplitVertically(self.signal_window,self.info_lane,-100)
		self.sp_window.SplitHorizontally(self.data_window,self.debug_window,-100)
		self.out_window_height = 0
		self.sheet_window_height = 400 
		self.FixSplit__()

		self.text_name.SetBackgroundColour( self.GetBackgroundColour())
		self.text_name.SetForegroundColour("purple")

		# 创建字体改善UI

		self.sizer_info.Add((10,180))
		self.result = Result_Ctrl(parent=self,id=-1)
		self.sizer_info.Add(self.result,10,wx.EXPAND|wx.LEFT|wx.RIGHT)

		
		self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.SetSizer(self.topsizer)
		self.topsizer.Add(self.sp_window,10,wx.EXPAND|wx.DOWN)
		self.topsizer.Add(self.sizer_info,2)



		#下面进行行为动作绑定
		self.Bind(EVT_MY_EVENT, self.OnNewInfo)
		self.text_serial.Bind(wx.EVT_LEFT_DCLICK, self.OnSetSerial)
		self.text_serial.Bind(wx.EVT_KEY_DOWN, self.OnSerialKey)
		self.sp_window.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSplit)
		self.data_window.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSplit)
		self.SetAutoLayout(True)
		self.sp_window.SetAutoLayout(True)
		self.data_window.SetAutoLayout(True)
		# 设置控制焦点
		self.focus_timer = wx.Timer(self,-1)
		self.Bind(wx.EVT_TIMER, self.SetFocus,self.focus_timer)
		self.focus_timer.Start(1000)
		self.signal_panel.SetFocus()

	def FixSplit__(self):
		Dx,Dy = wx.DisplaySize()
		self.data_window.SetSashPosition(-1-self.sheet_window_height,True)
		self.sp_window.SetSashPosition(-1-self.out_window_height,True)
		self.signal_panel.Refresh(True)

	def SetFocus(self,event):
		self.signal_panel.SetFocus()

	def ShowNTC(self,show=True):
		if show == False:
			self.text_NTC_ref.Show(False)
			self.text_NTC_measured.Show(False)
			self.labels[3].Show(False)
			self.labels[4].Show(False)
		else:
			self.text_NTC_ref.Show(True)
			self.text_NTC_measured.Show(True)
			self.labels[3].Show(True)
			self.labels[4].Show(True)

	def SelectComponent(self):
		self.signal_panel.SelectEut()

	def ToggleRun(self):
		self.parent.Refresh(True)
		self.signal_panel.ToggleRun()
		self.info_sheet.UpdateCell()
		if util.gRunning:
			self.ShowFullScreen(True)
		else:
			self.ShowFullScreen(False)

	def ShowFullScreen(self,full=True):
		self.parent.ShowFullScreen(full)


	def FixSplit(self,fix=True):
		print "\nSplit fixed, not changable.....\n"
		self.FixSplit__()
		#self.data_window.SetSashInvisible(fix)
		#self.sp_window.SetSashInvisible(fix)

	def OnSplit(self,event):
		#print "splitter changed!  ))))))))))))))))))))))))"
		threading.Timer(0.1,self.FixSplit__).start()

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

	def UpdateRecord(self):
		record = self.signal_panel.GetRecord()
		self.info_sheet.SetEut(record)
		return

	def UpdateRecordOnce(self):
		self.info_sheet.UpdateRecordOnce()
		return


	def clear_out(self):
		self.debug_out.SetValue("")
		
	def OnSetDebug(self,event):
		self.SetDebug()

	def SetDebug(self):
		if self.out_window_height != 200:
			self.out_window_height = 200
		else:
			self.out_window_height = 0
		threading.Timer(0.1,self.FixSplit__).start()

	def HideSheetField(self):
		if util.gHideField != True:
			util.gHideField = True
		else:
			util.gHideField = False
		self.info_sheet.UpdateCell()

	def SetSheet(self):
		if self.sheet_window_height != 400:
			self.sheet_window_height = 400
		else:
			self.sheet_window_height = 800
		threading.Timer(0.1,self.FixSplit__).start()
		print "set sheet"

	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)

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
		eut_serial = self.text_serial.GetValue()
		count = len(eut_serial)
		while  eut_serial[index:].isdigit() and digits < count:
			index -= 1
			digits +=1
		serial_prefix = eut_serial[:index+1]
		serial_num = string. atoi(eut_serial[index+1:])
		serial_num += int(x)
		SN = serial_prefix + '%0*d'%(digits, serial_num)
		self.SetSN(SN)
		self.signal_panel.SetSN(SN)


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

	def OnSerialKey(self, event):
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




	def OnNewInfo(self, evt):
		PN,SN,thermo,NTC_refer,NTC_value,NTCresult,result = self.signal_panel.GetInfo()
		self.SetPN(PN)
		self.SetSN(SN)
		self.SetThermo(thermo)
		self.SetNTCrefer(NTC_refer)
		self.SetNTCvalue(NTC_value)
		if result == None or result == '':
			self.result.SetUnknown()
		elif result == False or result == 'Fail':
			self.result.SetFail()
		elif result == True or result == 'Pass':
			self.result.SetPass()
		self.result.Refresh(True)


	def SetupOptions(self):
		self.signal_panel.Setup()

	def OnSetSerial(self, evt):
		if not util.gAuthen.Authenticate(util.USER):
			return
		dlg =  wx.TextEntryDialog(None,u"请输入序列号",u"序列号输入",self.text_serial.GetValue(),style=wx.OK|wx.CANCEL)
		if dlg.ShowModal() == wx.ID_OK :
			SN = dlg.GetValue()
			self.SetSN(SN)
			self.signal_panel.SetSN(SN)
		dlg.Destroy()

	def UploadSN(self,SN):
		self.SetSN(SN)
		self.Refresh(True)

	def SetPN(self, name):
		self.text_name.SetValue(name)


	def SetSN(self,SN):
		self.text_serial.SetValue(SN)
		self.info_sheet.UpdateCell()

	def SetThermo(self,thermo):
		if not thermo:
			return False
		thermo_ = round(float(thermo),2)
		self.text_thermo.SetValue(str(thermo_))
		return True

	def SetNTCrefer(self,refer):
		if not refer:
			return False
		refer_=round(float(refer),2)
		self.text_NTC_ref.SetValue(str(refer_))
		return True

	def SetNTCvalue(self,value):
		if not value:
			return False
		value_ = round(float(value),2)
		self.text_NTC_measured.SetValue(str(value_))
		return True
					
	def ShowVout(self,Vout):
		self.result.SetVout(Vout)
		self.result.Refresh(True)
		#print "show vout%.3f"%Vout

	def ShowDataRates(self,data_rates):
		self.result.SetDataRates(data_rates)
		self.result.Refresh(True)

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
	
#	sql = Thread_Sqlite(db_name="sqlite3_all.db",queue_in=persist[0], queue_out=persist[1]) 
#	sql.setDaemon(True)
#	sql.start()
#
	port = '%d'%(server_endpoints.PORT)
	ip = '%s'%(server_endpoints.IP_ADDRESS)
	URL = ip+':'+port+'/'+'usb1'
	#print URL
	
	
	x,y = wx.DisplaySize()
	panel = Signal_Control(parent=frm,
				#size = (1200,700),
				size = (x*5,y),
				id=-1,
				url = URL,
				eut_name="",
				eut_serial="10p8-082wj490",)
	#panel.populate_data()
	#panel.signal.SetRefer(signal_panel.pupulate_refer_table())
	panel.signal_panel.SetGridColour(wx.Colour(0,250,250,200))
	#panel.signal_panel.SetBackColour(wx.Colour(150,50,90,200))
	panel.signal_panel.SetBadColour(wx.Colour(200,0,200))
	frm.Show()
	app.SetTopWindow(frm)
	
	app.MainLoop()

