# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys
import glob
import wx 
import wx.grid 
import wx.lib.sheet 
import os 
import string
import threading
import time
from socket import *
import const
from Queue import Queue
import math
import csv
import minidb
from data_point import Data_Point,Data_Real,Data_Validated
from data_validator import Data_Validator_Linear
import wx.lib.buttons as buttons 
import re
import wx.lib.agw.balloontip as btip
import struct 
from thread_sqlite import Thread_Sql
import config_db
import sqlite3 as sqlite
import wx.lib.scrolledpanel as scrolledpanel
import codecs
from data_point import Data_Point,Signal_Control_Basic
from util import gAuthen,gZip,gZpickle 
from eut import Eut
from thermo_sensor import Thermo_Sensor
from test_record import Test_Record 
#from signal_control import Signal_Control
from refer_sheet import Refer_Sheet 
#for zip function
#from signal_panel import Signal_Panel,Signal

#index for persist Queue
_CMD = 0
_DATA = 1

gModule = False




#index for refer_entry status

#index for named cells
_VALUE	= int(0)
_RC	= int(1)

#index for refer table RC
REF_ROW = 6
REF_COL = 6



class Eut_Editor(wx.Dialog):
	def __init__(self, 
			parent=None, 
			id=-1,
			size=(1024,768),
			pos=wx.DefaultPosition,
			title='model editor',
			entries=None):
		super(Eut_Editor, self).__init__(parent, id, title,size=size)
		self.db_name = Eut.db_name 
		#self.SetBackgroundColour("light grey")
		self.entries = entries





		#筛选器控件部分控件
#		box_valid=wx.StaticBox(self,label=u"结果")
#		sizer_valid = wx.StaticBoxSizer(box_valid,wx.VERTICAL)
#		self.filter_valid = wx.ComboBox(self,-1,"Fail",(20,20),(60,20),("All","Pass","Fail"),wx.CB_DROPDOWN)
#		sizer_valid.Add(self.filter_valid, 0, wx.ALL, 0)

		self.box_name=wx.StaticBox(self,label=u"Model/型号")
		sizer_name = wx.StaticBoxSizer(self.box_name,wx.VERTICAL)
		self.filter_name = wx.TextCtrl(self,-1, size=(200,20))
		sizer_name.Add(self.filter_name, 0, wx.ALL, 0)

		self.box_PN=wx.StaticBox(self,label=u"PN/料号")
		sizer_PN = wx.StaticBoxSizer(self.box_PN,wx.VERTICAL)
		self.filter_PN = wx.TextCtrl(self,-1, size=(200,20))
		sizer_PN.Add(self.filter_PN, 0, wx.ALL, 0)

#		box_time=wx.StaticBox(self,label=u"时间",style=wx.ALIGN_CENTER)
#		sizer_time = wx.StaticBoxSizer(box_time,wx.VERTICAL)
#		self.filter_time  = wx.TextCtrl(self,-1, size=(200,20))
#		sizer_time.Add(self.filter_time, 0, wx.ALL, 0)

		self.sizer_btn_1  = wx.BoxSizer(wx.HORIZONTAL) 
		self.btn_import = wx.Button(self,-1,u"import/导入...")
		self.btn_new = wx.Button(self,-1,u"new/新建")
		self.btn_save = wx.Button(self,-1,u"save/保存")
		self.btn_select = wx.Button(self,-1,u"select/选择")
		self.btn_edit = buttons.GenToggleButton(self,-1,u"edit/编辑")
		self.btn_edit.SetToggle(True)
		self.sizer_btn_1.Add(self.btn_import)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_new)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_save)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_select)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_edit)

		self.sizer_btn  = wx.BoxSizer(wx.VERTICAL) 
		self.btn_filter = wx.Button(self,-1,u"筛选")
		#self.btn_selectType = buttons.GenToggleButton(self,-1,u"Sensor")

		self.btn_selectType = wx.Choice(self, -1,
				(20, 20),
				(120, 20),
				#[u"Record",u"Thermo",u"Sensor"])
				[u"Record",u"Thermo",u"Sensor"])

		self.btn_selectType.SetSelection(2)


		self.btn_selectDB = wx.Button(self,-1,u"DB/选择数据库")
		self.sizer_btn.Add(self.btn_filter)
		self.sizer_btn.Add(self.btn_selectType)
		self.sizer_btn.Add(self.btn_selectDB)
		self.sizer_filter = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer_filter.Add(self.sizer_btn_1)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_name)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_PN)
		self.sizer_filter.Add((10,20),1)
		#self.sizer_filter.Add(sizer_time)
		#self.sizer_filter.Add((10,20),1)
		#self.sizer_filter.Add(sizer_valid)


		self.sizer_filter.Add(self.sizer_btn)
		self.btn_filter.Bind(wx.EVT_BUTTON, self.OnFilter)
		self.btn_selectType.Bind(wx.EVT_CHOICE, self.OnSelectType)
		self.btn_selectDB.Bind(wx.EVT_BUTTON, self.OnSelectDb)
		self.btn_import.Bind(wx.EVT_BUTTON, self.OnImport)
		self.btn_new.Bind(wx.EVT_BUTTON, self.OnNew)
		self.btn_save.Bind(wx.EVT_BUTTON, self.OnSave)
		self.btn_select.Bind(wx.EVT_BUTTON, self.OnSelect)
		self.btn_edit.Bind(wx.EVT_BUTTON, self.OnToggleEdit)

		self.splitter = wx.SplitterWindow(self)
		self.splitter.SetMinimumPaneSize(1)
		#列表输出窗口部分
		self.scroller = wx.SplitterWindow(self.splitter)
		self.scroller.SetMinimumPaneSize(1)
		#左边列表
		self.sensors_panel = wx.ScrolledWindow(self.scroller,-1)
		self.sensors_panel.SetScrollbars(1,1,100,100)
		self.sizer_sensors = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.sensors_panel.SetSizer(self.sizer_sensors)
		self.eut_list =wx.ListCtrl(parent=self.sensors_panel,
				id=-1,
				style=wx.LC_REPORT,)
		self.eut_list.Bind(wx.EVT_LEFT_DCLICK, self.OnViewOne,self.eut_list)
		#~ pos=wx.DefaultPosition,
							#~ size=wx.DefaultSize,
							#~ style=wx.LC_REPORT,
							#~ validator=wx.DefaultValidator,
							#~ name="")
		#~ self.il=wx.ImageList(16,16,True)
		#~ for name in glob.glob("smicon??.png"):
			#~ self.il_max = self.il.Add(wx.Bitmap(name, wx.BITMAP_TYPE_PNG))
		#~ self.eut_list.AssignImageList(self.il,wx.IMAGE_LIST_SMALL)

		self.sizer_sensors.Add(self.eut_list,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN)

		self.sheet_panel = wx.ScrolledWindow(self.scroller,-1)
		self.sheet_panel.SetScrollbars(1,1,100,100)
		self.sheet_sizer = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.sheet_panel.SetSizer(self.sheet_sizer)
		self.refer_sheet = Refer_Sheet(self.sheet_panel)
		self.refer_sheet.SetEut(Eut())
	

		self.sheet_sizer.Add(self.refer_sheet,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN)
		#右边输出
		self.debug_out   = wx.TextCtrl(self.splitter,-1,style=(wx.TE_MULTILINE|wx.TE_RICH2|wx.HSCROLL))
		self.sizer_info  = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.sizer_info.Add(self.debug_out,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN)
		self.debug_out.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.mode = ""



		#self.sheet_panel.Hide()
		self.scroller.SplitVertically(self.sensors_panel,self.sheet_panel,-500)
		self.Bind(wx.EVT_SIZE,self.OnResize)		

		self.splitter.SplitHorizontally(self.scroller,self.debug_out,-50)

		self.sizer_top = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.SetSizer(self.sizer_top)
		self.sizer_top.Add(self.sizer_filter,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer_top.Add((20,20),1)
		self.sizer_top.Add(self.splitter,20,wx.EXPAND|wx.LEFT|wx.RIGHT)


#		self.status_bar = self.CreateStatusBar()
#
#		self.gauge = wx.Gauge(self.status_bar, -1, 100000, (100, 60), (250, 25), style = wx.GA_PROGRESSBAR)
#		self.gauge.SetBezelFace(3)
#		self.gauge.SetShadowWidth(3)
#

		self.popmenu1 = wx.Menu()
		self.menu_export = self.popmenu1.Append(wx.NewId(), u"导出", u"导出到文本框")
		self.menu_export2file = self.popmenu1.Append(wx.NewId(), u"导出到文件", u"")
		self.menu_view = self.popmenu1.Append(wx.NewId(), u"显示到图形", u"")
		self.Bind(wx.EVT_MENU, self.OnExport,self.menu_export)
		self.Bind(wx.EVT_MENU, self.OnExport,self.menu_export2file)
		self.Bind(wx.EVT_MENU, self.OnViewGUI,self.menu_view)
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnPopup)
		#self.Bind(wx.EVT_CONTEXT_MENU, self.OnPopup,self.refer_sheet)

		self.Relayout()
		if gModule == True:
			sys.stdout = self.debug_out
			sys.stderr = self.debug_out
			self.btn_select.Show(False)
		self.UpdateToggle()
		#print "sheet init ok...."

	def Init_Persist(self):#启动数据库持久化线程,通过队列进行保存与取出数据
		self.persist = (Queue(0),Queue(0))
		sql = Thread_Sql(db_name=self.db_name,
				table_name=self.refer_sheet.table_name,
				queue_in=self.persist[_CMD],
				queue_out=self.persist[_DATA]) 
		#sql.setDaemon(True)
		sql.start()

	def OnImport(self, event):
		self.refer_sheet.Import()
		self.refer_sheet.SetEditable(True)

	def OnNew(self, event):
		"""clear sheet and create new eut"""
		self.eut_list.ClearAll()         
		self.refer_sheet.NewEut()


	def GetEut(self):
		return self.refer_sheet.GetEut()

	def OnSave(self, event):
		if isinstance(self.GetEut(),Test_Record):
			if not gAuthen.Authenticate("Admin"):
				return False
		elif not gAuthen.Authenticate("User"):
			return False
		self.refer_sheet.SaveEut()
		self.btn_edit.SetToggle(True)
		self.UpdateToggle()
		print "saving ok!"
		return True

	def OnSelect(self, event):
		"""KeyDown event is sent first"""
		if not isinstance(self.refer_sheet.GetEut(),Eut) and not  isinstance(self.refer_sheet.GetEut(),Test_Record) :
			wx.MessageBox(u"所选不是传感器\n  请选择传感器!!!",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
			return 
		if wx.NO == wx.MessageBox(u"确认要使用此料？",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
			return
		else:
			self.Show(False)

	def OnToggleEdit(self, event):
		"""KeyDown event is sent first"""
		toggle = self.btn_edit.GetToggle()
		if not toggle:
			if not gAuthen.Authenticate("Admin"):
				self.btn_edit.SetToggle(not toggle)
		self.UpdateToggle()
	
	def UpdateToggle(self):
		toggle = self.btn_edit.GetToggle()
		if not toggle:
			self.btn_edit.SetBackgroundColour("green")
			self.refer_sheet.SetEditable(False)
		else:
			self.btn_edit.SetBackgroundColour("red")
			self.refer_sheet.SetEditable(True)

		self.btn_edit.Refresh()

	def OnPopup(self, event):
		"""KeyDown event is sent first"""
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)

	def OnModeOn(self, event):
		"""KeyDown event is sent first"""

		#~ raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		#~ if raw_code == 75 and modifiers==3:
			#~ self.Close()
		if  modifiers==2:
			self.mode = "ctrl"
		print "ctrl down....\n"

	def OnModeOff(self, event):
		"""KeyDown event is sent first"""

		#~ raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		#~ if raw_code == 75 and modifiers==3:
			#~ self.Close()
		if modifiers==2:
			self.mode = ""
		print "ctrl up....\n"

	def OnSelectType(self,event):
		"""select table file to query"""
		self.eut_list.ClearAll()         
		if self.btn_selectType.GetSelection() == 2:
			if wx.NO ==	wx.MessageBox(u"确认更换到Sensor!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"Sensor")
			self.refer_sheet.SetEut(Eut())
			self.btn_select.Show(True)
		elif self.btn_selectType.GetSelection() == 0:
			if wx.NO ==	wx.MessageBox(u"确认更换到Record!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return
			self.box_name.SetLabel(u"时间/Time &&&& (结果/result)")
			self.box_PN.SetLabel(u"料号/PN")
			self.btn_selectType.SetLabel(u"Record")
			self.refer_sheet.SetEut(Test_Record())
			self.btn_select.Show(False)
		elif self.btn_selectType.GetSelection() == 1:
			if wx.NO ==	wx.MessageBox(u"确认更换到Thermo!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"Thermo")
			self.refer_sheet.SetEut(Thermo_Sensor())
			self.btn_select.Show(False)
		self.refer_sheet.SetDefault( )
		self.btn_selectType.Refresh()
		print "set DB table to  >>>> ",self.refer_sheet.eut.table_name

	def OnSelectDb(self,event):
		"""select db file to query"""
		dlg = wx.FileDialog(None,u"选择数据库文件",wildcard="*.db")
		if dlg.ShowModal() != wx.ID_OK:
			return
		db_name = dlg.GetPath()
		if db_name: 
			self.refer_sheet.SetDbName(db_name)

	def OnKeyDown(self,event):
		"""KeyDown event is sent first"""

		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		#~ if raw_code == 75 and modifiers==3:
			#~ self.Close()
		if raw_code == 75 and modifiers==2:
			self.debug_out.SetValue("")

	def OnResize(self,evt):
		self.Relayout()

	def Relayout(self):
		self.Layout()
		self.sheet_panel.Refresh(True)
		self.Refresh(True)		

	def OnViewGUI(self,event):
		print u"导出到图形!"
		item = self.eut_list.GetFirstSelected()
		SN =  self.eut_list.GetItem(item,2).GetText()
		#time  =  self.eut_list.GetItem(item,4).GetText()
		record = self.refer_sheet.GetEut()
		record.RestoreFromDBZ(SN)
		print "%s read from DB OK!"%(SN)
		PN  = record.GetPN()
		eut = Eut()
		eut.RestoreFromDBZ(PN)
		x,y = wx.DisplaySize()
		frame= wx.Frame(parent=None,size=(x*5,y/2))
		signals=[]
		s1 = Signal()
		s2 = Signal()
		signals.append(s1)
		signals.append(s2)
		panel = Signal_Panel(parent=frame,id=-1,size=(x*5,y/2),signals=signals)
		panel.SetEut(eut)
		panel.SetRecord(record)
		frame.Show(True)


	def OnViewOne(self,event):
		item = self.eut_list.GetFocusedItem()
		PN =  self.eut_list.GetItem(item,2).GetText()
		print "view one",PN
		self.refer_sheet.show(PN)
		self.UpdateToggle()

	def OnFilter(self,event):
		self.UpdateToggle()
		self.eut_list.ClearAll()         

		entries,columns = self.refer_sheet.QueryDB(
				model_pattern = self.filter_name.GetValue(),
				PN_pattern = self.filter_PN.GetValue())
		if not entries:
			return
		#show headers 
		for  column in  columns:
			self.eut_list.InsertColumn(column[0],column[1],width=column[2])
		#show entries 
		count = 1 
		for  entry in entries:
			row = self.eut_list.InsertStringItem(
					sys.maxint,
					"%10d"%count)
			self.eut_list.SetStringItem(row,0,str(count))
			col = 1
			for field in entry:
				self.eut_list.SetStringItem(row,col,field)
				if field.startswith("Fail"):
					self.eut_list.SetItemBackgroundColour(row,'red')
				else:
					self.eut_list.SetItemBackgroundColour(row,'green')
				col += 1
			count += 1

		#self.PushStatusText(u"共 %d 数据条目找到!"%count)

	def OnExport(self,event):
		export_name = ""
		item = self.popmenu1.FindItemById(event.GetId())
		
		if item.GetText() == u"导出":
			tofile = sys.stdout
		elif item.GetText() == u"导出到文件":
			dlg = wx.FileDialog(None,"select a file ")
			if dlg.ShowModal() != wx.ID_OK:
				return
			export_name = dlg.GetPath()
			tofile = codecs.open(export_name,'w+','gb2312')

		self.export_detail(tofile)
		if not tofile is sys.stdout:
			tofile.close()

	def export_detail(self,tofile):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

	#	tmp_str = self.filter_valid.GetValue()
	#	if tmp_str == "Pass":
	#		filter_valid = 1
	#	elif tmp_str == "Fail":
	#		filter_valid = 0 
	#	else:
	#		filter_valid = "ALL" 

		item = self.eut_list.GetFirstSelected()
		out = '#####################################################################################################\n'
		while item !=-1:
			SN =  self.eut_list.GetItem(item,2).GetText()
			#time  =  self.eut_list.GetItem(item,4).GetText()
			eut = self.refer_sheet.GetEut()
			eut.RestoreFromDBZ(SN)
			out += eut.Show()
			out += '#####################################################################################################\n'
			item = self.eut_list.GetNextSelected(item)
		print >>tofile, out
		#print  out



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
from util import * 
from test_record import * 
from data_source import Data_Source 
from data_source import MyEvent, EVT_MY_EVENT

from refer_entry import Refer_Entry
#from refer_table import Eut_Editor
from pga import gPGA,gVdd,gVout_Full,gVout_Amp



class Signal(wx.Dialog):
	def __init__(self,window=None,ok_colour="green",bad_colour="red",url=None,table=None):
		super(Signal, self).__init__(parent=None)
		self.window = window
		self.ok_colour = ok_colour
		self.old_ok_colour = ok_colour
		self.bad_colour= bad_colour
		self.old_bad_colour = bad_colour
		self.data = []
		self.cmd_queue=Queue(-10)
		self.data_queue=Queue(-10)
		self.started_flag = False
		self.thread_source = None
		self.count = 0
		self.xmax= 0.0
		self.ymax= 0.0
		self.SetRefer_entries(table)
		self.SetUrl(url)
		self.Bind(EVT_MY_EVENT, self.OnNewData)
		self.trig_status = False
		self.record = Test_Record()
		#self.NewRecordSN = ''
		self.status = True
		self.eut = None
		self.thermo = Thermo()
		self.filter_option = True
		self.Vout = 0.001
		self.Vout_req = 0.001
		self.temprature  = 20.001
		self.Vout_adj_count = 5
		self.Charge_time = 0.8 

		self.step_count = 0
		self.single_count = 0

	def SetRecord(self,record):
		if not isinstance(record,Test_Record):
			return
		self.record = record

	def GetRecord(self):
		return self.record

	def SetVout(self,value_float):
		self.Vout_req = value_float
		self.Vout_adj_count = 8
		threading.Timer(0.8,self.SetVout_).start()

	def SetVout_(self):
		self.Vout_adj_count -= 1
		if self.Vout_adj_count != 0: 
			threading.Timer(1,self.SetVout_).start()
		deltaV = self.Vout_req - self.Vout
		deltaHex = abs(deltaV)/(gVdd*gVout_Amp)*gVout_Full*self.Charge_time 
		if deltaV > 0:
			vout_cmd = "vout:inc:%d"%deltaHex
		else:
			vout_cmd = "vout:dec:%d"%deltaHex
		self.cmd_queue.put(vout_cmd)

	def DecreaseVout(self,value):
		vout_cmd = "vout:dec:%d"%value
		print vout_cmd
		self.cmd_queue.put(vout_cmd)

	def IncreaseVout(self,value):
		vout_cmd = "vout:inc:%d"%value
		print vout_cmd
		self.cmd_queue.put(vout_cmd)

	def SetRangHL(self):
		rangeHL_cmd = "setup:PLC:com3:9600"
		self.cmd_queue.put(rangeHL_cmd)
		print "signal cmd>>>%s"%rangeHL_cmd 
		time.sleep(0.1)
		rangeH,rangeL = self.eut.GetXrange()
		rangeHL_cmd = "setup:PLC:rangeHL:%d;%d"%(rangeH,rangeL)
		print "signal cmd>>>%s"%rangeHL_cmd 
		self.cmd_queue.put(rangeHL_cmd)

	def SetPN(self,eut):#extract PN from eut object
		if not isinstance(eut,Eut):
			print "Error: invalid type, should be Eut!"
			return None
		self.eut = eut
		self.record.SetPN(eut.GetPN())
		self.window.UpdateRecord()

	def SetSN(self,SN):
		self.record.SetSN(SN)
		self.window.UpdateRecord()

	def UploadSN(self,SN):
		self.window.UploadSN(SN)

	def SetWindow(self,window):
		self.window = window

	def GetData(self):
		return self.record.GetRecord()

	def SetOkColour(self,colour):
		self.ok_colour = colour

	def GetOkColour(self):
		return self.ok_colour

	def GetBackColour(self):
		return self.window.GetBackColour()

	def GetGridColour(self):
		return self.window.GetGridColour()

	def GetFilterOption(self):
		return self.filter_option
		
	def SetFilterOption(self,option):
		self.filter_option = option
		if option == True:
			self.cmd_queue.put("Filter:On")
		else:
			self.cmd_queue.put("Filter:Off")

	def SetBadColour(self,colour):
		self.bad_colour = colour 

	def GetBadColour(self):
		return self.bad_colour

	def SetUrl(self,url):
		if not url:
			return
		self.url = url

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
			#gPGA.find_solution(range_=(ymin,ymax),unit="Ohm")
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

	def SetupHW(self):
		cmd_map     =   {'Ohm':'R','ohm':'R',
				'Vol':'U','vol':'U',
				'Amp':'I','amp':'I',
				}

		#根据单位设置RUI
		unit = self.eut.GetYunit()
		sw_cmd = "adc:swt:%s:"%(cmd_map[unit[:3]])
		print sw_cmd
		self.cmd_queue.put(sw_cmd)
		time.sleep(0.1)

		#根据range_设置PGA
		range_ = self.eut.GetRange()
		r_code,a_code =  gPGA.find_solution(range_,unit)
		pga_cmd = "adc:pga:r:%d:a:%d"%(r_code,a_code)
		print pga_cmd
		self.cmd_queue.put(pga_cmd)
		time.sleep(0.1)
		self.SetRangHL()

		


	def Run(self):
		if self.started_flag != True:
			self.thread_source = Data_Source(self,self.url,self.cmd_queue,self.data_queue)
			self.thread_source.setDaemon(True)
			self.thread_source.start() #启动后台线程, 与endpoint server进行连接与通信
			self.started_flag = True
			serial_name = self.url.split("/")[1]
			open_cmd = "open:%s:%s"%(serial_name,'115200')
			print open_cmd
			self.cmd_queue.put(open_cmd)
			time.sleep(0.1)
			#set hard ware below
			self.SetupHW()

		 # flush outdated data
		while not self.data_queue.empty():
			self.data_queue.get()
		self.cmd_queue.put("run:")

	def Init_Data(self):
		self.data = []
		self.step_count = 0
		self.window.SetUnknown()
		self.window.Refresh(True)

	def OnQueryDB(self,event):
		QueryUI = Server_("python refer_table.py")
		QueryUI.start()

	def Pause(self):
		print "signal pause.....\n"
		self.cmd_queue.put("stop:")
		while not self.data_queue.empty(): # flush outdated data
			self.data_queue.get()
		#self.Init_Data()

	def Configure(self,command):
		self.cmd_queue.put(command)
	
	def SampleThermo(self):
		if not self.eut.HasNTC():
			return
		thermo_cmd = "adc:temp:"
		print thermo_cmd
		self.cmd_queue.put(thermo_cmd)


	def SetDataRates(self,data_rates):
		self.window.window.ShowDataRates(data_rates)

	def OnNewData(self, event):
		if not self.refer_entries:
			return
		out = ''
		pos = 0
		value = 0
		while not self.data_queue.empty():
			item = self.data_queue.get()
			if isinstance(item,dict):
				if self.trig_status == False:
					continue
				Xvalue,Yvalue_ = item["value"]
				#print "Xvalue,Yvalue:",Xvalue,';',Yvalue_
				Yvalue = gPGA.Get_Hex2Float(Yvalue_)
				length = item["length"]
				if length > 100 or item['flag'] == 'step':
					length = 100
				if item['flag'] != 'new':
					self.step_count += 1
					self.single_count = 0
				else:
					self.single_count += 1


				refer_entry  = self.GetReferEntry(Xvalue,Yvalue)
				if not refer_entry:
					return
				#print "new data .............",Xvalue,Yvalue,length
				#print "searched refer_entry X,Y:",refer_entry.GetXvalue(),refer_entry.GetYvalue()
				Xprecision,Yprecision,xstatus,ystatus = refer_entry.Validate(Xvalue,Yvalue)
				#if xstatus==True and ystatus==True:
				if (ystatus== False and item['flag'] != 'new') or self.single_count > 3:
					status = False
					self.status = False
					self.window.SetFail()
				else:
					status = True
				record= Refer_Entry(
						Xvalue=Xvalue,
						Yvalue=Yvalue,
						Xprecision=Xprecision,
						Yprecision=Yprecision,
						valid_status=status)
				record.SetLength(length)
				self.data.append(record)
				self.record.AppendRecord(
					Record_Entry(
						refer	= refer_entry,
						record	= record
						)
					)
				self.window.window.UpdateRecordOnce() # signal_control.UpdateRecord()
				self.window.Refresh(True)
			else:
				if item.startswith("trigger"):
					print "'signal' triggering.........."
					self.trig_status = True
					self.status = True
					self.Init_Data()
					self.record.InitRecord()
					self.window.UpdateRecord()
					self.window.SetUnknown()
					NewRecordSN = self.record.AdjustSN(1)
					self.UploadSN(NewRecordSN) 
					#收到触发信号，可以采集温度信号了!
					self.SampleThermo()
					self.window.Refresh(True)
				elif item.startswith("sleep"):
					print "'signal' sleeping.........."
					if  self.trig_status == True:
						self.trig_status = False
						print "saving.........."
						if (self.status == False)\
								or (self.record.GetResult4NTC() == "Fail") \
								or (self.step_count != len(self.refer_entries) ) :
							self.record.SetResultFail()
							self.window.SetFail()
							print "test fail.........."
						else:
							self.record.SetResultPass()
							self.window.SetPass()
							print "test pass!!!!!!!!!!!"
						self.record.Save2DBZ()
						print "step count ___%d ; \trefer entries__%d"%(self.step_count,len(self.refer_entries) )
						print "saving ok.........."
					self.window.Refresh(True)
				elif item.startswith("0t:"):
					if not self.eut.HasNTC():
						continue
					hex_NTC = int(item[3:7],16)
					hex_PT  = int(item[7:11],16)
					(result,temprature,Rntc,Rref)=self.record.SetupThermo(hex_NTC,hex_PT)
					self.window.window.SetThermo(str(round(temprature,3)))
					self.window.window.SetThermoValue(str(round(Rntc,3)))
					self.window.window.SetThermoRefer(str(round(Rref,3)))
					#self.window.window.UpdateRecord()
					self.window.Refresh(True)
				elif item.startswith("0v:"):
					hex_Vout = int(item[3:7],16)
					hex_PT = int(item[7:11],16)
					self.Vout = gPGA.Get_Hex2Vout(hex_Vout)
					self.temprature  = gThermo.GetTemprature(hex_PT)
					self.window.window.SetThermo(str(round(self.temprature,3)))
					self.window.window.ShowVout(round(self.Vout,3))


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
		self.back_color_btn = wx.Button(self,-1,"Back color")
		self.grid_color_btn = wx.Button(self,-1,"Grid color")
		self.filter_option = wx.CheckBox(self,-1,u"Using Filter/\n使用滤波器",(20,20),(160,-1))
		self.filter_option.SetValue(self.signal.GetFilterOption())
		self.ok_color_btn.SetBackgroundColour(self.signal.GetOkColour())
		self.bad_color_btn.SetBackgroundColour(self.signal.GetBadColour())
		self.back_color_btn.SetBackgroundColour(self.signal.GetBackColour())
		self.grid_color_btn.SetBackgroundColour(self.signal.GetGridColour())
		self.ok_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.bad_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.back_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.grid_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
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
		self.hsizer2= wx.BoxSizer(wx.HORIZONTAL|wx.ALIGN_CENTER)# 创建一个分割窗
		self.hsizer2.Add((20,20))
		self.hsizer2.Add(self.back_color_btn)
		self.hsizer2.Add((20,20))
		self.hsizer2.Add(self.grid_color_btn)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.hsizer)		
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.hsizer2)		
		self.topsizer.Add(self.filter_option)
		
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
		elif event.GetId() == self.ok_color_btn.GetId():
			print "set bad color"
			self.bad_color_btn.SetBackgroundColour(color)
			#self.signal.SetBadColour(color)
		elif event.GetId() == self.back_color_btn.GetId():
			print "set back color"
			self.back_color_btn.SetBackgroundColour(color)
			#self.signal.SetBadColour(color)
		elif event.GetId() == self.grid_color_btn.GetId():
			print "set grid color"
			self.grid_color_btn.SetBackgroundColour(color)
			#self.signal.SetBadColour(color)
		dlg.Destroy()

	def GetOkColour(self):
		return self.ok_color_btn.GetBackgroundColour()

	def GetBadColour(self):
		return self.bad_color_btn.GetBackgroundColour()

	def GetBackgroundColour(self):
		return self.back_color_btn.GetBackgroundColour()

	def GetGridColour(self):
		return self.grid_color_btn.GetBackgroundColour()

	def GetUrl(self):
		return self.url.GetValue()

	def GetFilterOption(self):
		return self.filter_option.IsChecked()

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
		self.SetupScrolling(scroll_x=True, scroll_y=False, rate_x=20, rate_y=20)
		self.SetupScrolling() 
		if signals:
			self.SetSignals(signals)
		self.SetBackColour(back_color)
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
		#self.menu_save = self.popmenu1.Append(wx.NewId(), u"保存数据", u"保存数据到数据库" )
		self.menu_run = self.popmenu1.Append(wx.NewId(), u"运行.当前点", u"运行与暂停", kind=wx.ITEM_CHECK)
		self.popmenu1.AppendSeparator()
		#self.menu_query_ui = self.popmenu1.Append(wx.NewId(), u"数据库查询", u"组合查询已存储数据")
		#self.menu_query_current = self.popmenu1.Append(wx.NewId(), u"当前数据查询", u"查询正在测试的数据")
		#self.popmenu1.AppendSeparator()
		self.menu_eut = self.popmenu1.Append(wx.NewId(), u"Sensor/Record选择", u"被测件选择")
		self.menu_setup = self.popmenu1.Append(wx.NewId(), u"配置", u"测试参数配置")
		self.popmenu1.AppendSeparator()
		self.menu_log = self.popmenu1.Append(wx.NewId(), u"log10", u"Y轴log10换算", kind=wx.ITEM_CHECK)
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightDown)
		self.Bind(wx.EVT_MENU, self.OnRunStop,self.menu_run)
		#self.Bind(wx.EVT_MENU, self.OnShowCurrent,self.menu_query_current)
		self.Bind(wx.EVT_MENU, self.OnSetup,self.menu_setup)
		#self.Bind(wx.EVT_MENU, self.OnQueryDB,self.menu_query_ui)
		self.Bind(wx.EVT_MENU, self.OnSelectEut,self.menu_eut)
		self.Bind(wx.EVT_MENU, self.OnLogSetup,self.menu_log)
		#self.Bind(wx.EVT_WHEEL, self.OnZoom)
		#self.Bind(wx.EVT_MENU, self.OnSave,self.menu_save)
		self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.SetRenderDefault()
	
	def SetRenderDefault(self):
		self.log10_toggle = False
		self.factorY    = 1.0
		self.offsetY = 100 
		self.screenXsize = 120

	def GetRecord(self):
		return self.signals[0].GetRecord()

	def SetRecord(self,record):
		if not isinstance(record,Test_Record):
			return
		PN = record.GetPN()
		eut = Eut()
		eut.RestoreFromDBZ(PN)
		self.SetEut(eut)
		self.signals[0].SetRecord(record)
		self.UpdateRecord()
		return True

	def UpdateRecord(self):
		if self.window:
			self.window.UpdateRecord()

	def SetGridColour(self,color):
		self.grid_colour= wx.Colour(color)

	def GetGridColour(self):
		return self.grid_colour

	def SetBackColour(self,color):
		self.back_colour = color
		self.SetBackgroundColour(color)

	def GetBackColour(self):
		return self.back_colour

	def OnKeyDown(self, event):
		"""KeyDown event is sent first"""
		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()
		print "raw_code=",raw_code,";modifiers=",modifiers

		if raw_code == 39 or raw_code == 73 :  # <I> or ->  = zoom in 
			self.screenXsize += 20 
			print "X Zoom In"
		elif raw_code == 37 or raw_code ==79 :# <O> or  <-  = zomm out
			self.screenXsize -= 5 
			print "X Zoom Out"
		elif raw_code == 38:# <arrow up> = Y zomm in
			self.factorY += 0.2 
			print "Y Zoom In"
		elif raw_code == 40:# <arrow dn> = Y zomm out
			self.factorY -= 0.1 
			print "Y Zoom Out"
		elif  raw_code ==33:# <PgUp>   = Y move Up 
			self.offsetY -= 10
			print "Y Move Up"
		elif  raw_code ==34:# <PgDn>   = Y move Down
			self.offsetY += 30 
			print "Y Move Down"
		elif raw_code == 90 and modifiers ==2 :# <ctrl>+<Z>      = 
			self.SetRenderDefault()
		elif raw_code == 85 and modifiers ==2 :# <ctrl>+<U>     = increase Vout 
			self.AdjVout(100,'+')
		elif raw_code == 85 and modifiers ==6 :# <ctrl>+<shift>+<U>   = decrease Vout 
			self.AdjVout(10,'-')
		elif raw_code == 85 and modifiers ==3 :# <ctrl>+<alt>+<U>   = Vout@5.0V 
			self.AdjVout(5.0,'=')
			print "Set Vout to 5.0V"
		elif raw_code == 74 and modifiers ==7 :# <ctrl>+<shift>+<alt>+<J>   = Vout@10.0V
			self.AdjVout(10.0,'=')
			print "Set Vout to 10.0V"
		elif raw_code == 77 and modifiers ==7 :# <ctrl>+<shift>+<alt>+<M>   = Vout@15.0V
			self.AdjVout(15.0,'=')
			print "Set Vout to 15.0V"
		elif (raw_code == 3 and modifiers ==2) or raw_code == 32 :# <ctrl>+<Pause>   = run/pause
			self.OnRunStop(event)
		elif raw_code == 115 :# <F4> = pause
			self.Pause()
		elif raw_code == 113 :# <F2> = run
			self.Run()
		self.Refresh(True)

	def SetScreenXsize(self,Xsize):
		self.screenXsize = Xsize
		print "self.screenXsize",self.screenXsize

	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)

	def OnLogSetup(self,event):
		self.menu_log.Toggle() 
		self.log10_toggle = not self.log10_toggle
		if self.log10_toggle:
			print "Set as log10"
		else:
			print "Set as log"

		self.Refresh(True)

	def AdjVout(self,value,op):
		for signal in self.signals:
			if not signal:
				continue
			if op.startswith('+'):
				signal.IncreaseVout(value)
			elif op.startswith('-'):
				signal.DecreaseVout(value)
			elif op.startswith('='):
				signal.SetVout(value)


	def OnRunStop(self, evt):
		if not self.eut:
			wx.MessageBox(u"错误：无效的Sensor!\n  请先设置sensor!",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)

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
		self.menu_run.Toggle() 
		for signal in self.signals:
			if not signal:
				continue
			signal.Run()
			
	def Pause(self):
		self.running_flag = False
		self.menu_run.Toggle() 
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
		dlg = Dialog_Setup(self,-1,"signal UI&CFG",self.signals)
		if dlg.ShowModal()==wx.ID_OK:
			print "setup OK!"
			for (signal,cfg_panel) in dlg.ui_map:
				signal.SetUrl(cfg_panel.GetUrl())
				signal.SetOkColour(cfg_panel.GetOkColour())
				signal.SetBadColour(cfg_panel.GetBadColour())
				signal.SetFilterOption(cfg_panel.GetFilterOption())
				self.SetBackColour(cfg_panel.GetBackgroundColour())
				self.SetGridColour(cfg_panel.GetGridColour())
		else:
			print "setup cancelled!"
		
		dlg.Destroy() #释放资源
		self.Refresh(True)

	def SetSN(self,SN):
		for signal in self.signals:
			if not signal:
				continue
			signal.SetSN(SN)

	def UploadSN(self,SN):
		self.window.UploadSN(SN)

	def SetEut(self,eut):
		if not isinstance(eut,Eut):
			return
		self.eut = eut
		#print "start eut show refer...................................................................................................."
		#print eut.ShowRefer()
		#print "end eut show refer...................................................................................................."
		if self.window:
			self.window.SetName(eut.GetPN())
			#self.window.SetThermoValue(eut.GetThermoModel())

		refer_tables = self.eut.GetReferTable()
		i=0
		for signal in self.signals:#map refer_tables to signals as 1:1
			if not signal:
				continue
			signal.SetRefer_entries(refer_tables[i]) #first
			signal.SetPN(eut)
			i += 1
		self.Refresh(True)

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

	def line2log(self,value):
		if value < 0.001:
			return 0.0001
		if self.log10_toggle:
			return math.log10(value)
		else:
			return math.log(value)

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
		max_height= clientRect.height
		count = 0
		for refer_entry in self.eut.GetReferTable()[0]:
			count +=1
			if refer_num > 20 and count%sparse!=0:
				continue
			referY_= self.line2log(refer_entry.GetYvalue())
			maxY_ = self.line2log(self.eut.GetMaxY())
			y = int((1.0- referY_/maxY_)*max_height)*self.factorY + self.offsetY 
			#log for view
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
				#print " data_.Yvalue::",data_.GetYvalue()
				x1_ = x0_ + data_.GetLength()
				x0  = x0_ *self.screenXsize/maxX
				x1  = x1_ *self.screenXsize/maxX
				if data_.GetValid() == True:
					dc.SetPen(wx.Pen(signal.ok_colour,2,style = wx.SOLID))
				else:
					dc.SetPen(wx.Pen(signal.bad_colour,2,style = wx.SOLID))
				valueY_ = self.line2log(data_.GetYvalue())
				maxY_   = self.line2log(maxY)

				Y0=int((1.0-valueY_/maxY_)*max_height)*self.factorY + self.offsetY 
				#log for view
				#Y0__= math.log(Y0)
				#Y0  = int(Y0__ * Y0__)
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
		obj_ = Eut_editor.GetEut()
		if isinstance(obj_ ,Eut):
			self.SetEut(obj_ )
		elif isinstance(obj_ ,Test_Record):
			self.SetRecord(obj_ )
		else:
			print u"错误：无效的Sensor!"
			wx.MessageBox(u"错误：无效的Sensor!",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
			return False
		return True

	def SetUnknown(self):
		self.window.SetUnknown()

	def SetPass(self):
		self.window.SetPass()

	def SetFail(self):
		self.window.SetFail()



############################################################################################################################################
if __name__=='__main__':
	gModule = True

	app = wx.App()
	frm = Eut_Editor()
	frm.SetSize(wx.DisplaySize())
	frm.Maximize()
	frm.Show(True)
	app.SetTopWindow(frm)

	app.MainLoop()

