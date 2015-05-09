# -*- coding: utf-8 -*-
"""Signal UI component .""" 
import sys
import glob
import wxversion
wxversion.select("3.0")
import wx 
import wx.grid 
import wx.lib.sheet 
import threading
import time
#from socket import *
from Queue import Queue
import math
import wx.lib.buttons as buttons 
import sqlite3 as sqlite
import wx.lib.scrolledpanel as scrolledpanel
import codecs
from thermo_sensor import Thermo_Sensor
from test_record import Test_Record 
#from signal_control import Signal_Control
from refer_sheet import Refer_Sheet 
import util
from test_record import * 
from data_source import Data_Source,MyEvent, EVT_MY_EVENT

from refer_entry import Refer_Entry
import pga
import copy

_CMD = 0
_DATA = 1

gModule = False





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
		self.parent= parent
		self.db_name = Eut.db_name 
		#self.SetBackgroundColour("light grey")
		self.entries = entries





		#筛选器控件部分控件
		self.box_name=wx.StaticBox(self,label=u"型号")
		sizer_name = wx.StaticBoxSizer(self.box_name,wx.VERTICAL)
		self.filter_name = wx.TextCtrl(self,-1, size=(150,20))
		sizer_name.Add(self.filter_name, 0, wx.ALL, 0)

		self.box_PN=wx.StaticBox(self,label=u"料号")
		sizer_PN = wx.StaticBoxSizer(self.box_PN,wx.VERTICAL)
		self.filter_PN = wx.TextCtrl(self,-1, size=(150,20))
		sizer_PN.Add(self.filter_PN, 0, wx.ALL, 0)

		self.sizer_btn_1  = wx.BoxSizer(wx.HORIZONTAL) 
		self.btn_import = wx.Button(self,-1,u"导入...")
		self.btn_new = wx.Button(self,-1,u"新建")
		self.btn_save = wx.Button(self,-1,u"保存")
		self.btn_edit = buttons.GenToggleButton(self,-1,u"编辑")
		self.btn_edit.SetToggle(True)
		self.sizer_btn_1.Add(self.btn_import)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_new)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_save)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_edit)

		self.sizer_btn  = wx.BoxSizer(wx.VERTICAL) 
		self.btn_filter = wx.Button(self,-1,u"筛选")
		#self.btn_selectType = buttons.GenToggleButton(self,-1,u"Sensor")

		self.btn_selectType = wx.Choice(self, -1,
				(20, 20),
				(80, 20),
				[u"测试记录",u"NTC",u"传感器"])
		if self.parent:
			self.btn_selectType.SetSelection(2)#2==传感器
		else:
			self.btn_selectType.SetSelection(0)#0==测试记录



		self.btn_selectDB = wx.Button(self,-1,u"选择数据库")
		self.sizer_btn.Add(self.btn_filter,1)
		self.sizer_btn.Add(self.btn_selectType,1)
		self.sizer_btn.Add(self.btn_selectDB,1)
		self.sizer_filter = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer_filter.Add(self.sizer_btn_1)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_name)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_PN)
		self.sizer_filter.Add((10,20),1)



		btnszr = self.CreateButtonSizer(wx.OK|wx.CANCEL) 
		self.sizer_filter.Add(self.sizer_btn)
		self.sizer_filter.Add((10,20))
		self.sizer_filter.Add(btnszr, 0,wx.EXPAND|wx.ALL, 5) 

		self.btn_filter.Bind(wx.EVT_BUTTON, self.OnFilter)
		self.btn_selectType.Bind(wx.EVT_CHOICE, self.OnSelectType)
		self.btn_selectDB.Bind(wx.EVT_BUTTON, self.OnSelectDb)
		self.btn_import.Bind(wx.EVT_BUTTON, self.OnImport)
		self.btn_new.Bind(wx.EVT_BUTTON, self.OnNew)
		self.btn_save.Bind(wx.EVT_BUTTON, self.OnSave)
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

		self.sizer_sensors.Add(self.eut_list,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN)

		self.sheet_panel = wx.ScrolledWindow(self.scroller,-1)
		self.sheet_panel.SetScrollbars(1,1,100,100)
		self.sheet_sizer = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.sheet_panel.SetSizer(self.sheet_sizer)
		self.refer_sheet = Refer_Sheet(self.sheet_panel)
		self.refer_sheet.SetEut(Eut())
	

		self.sheet_sizer.Add(self.refer_sheet,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN) #右边输出
		self.debug_out   = wx.TextCtrl(self.splitter,-1,style=(wx.TE_MULTILINE|wx.TE_RICH2|wx.HSCROLL))
		self.sizer_info  = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.sizer_info.Add(self.debug_out,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN)
		self.debug_out.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.mode = ""



		self.scroller.SplitVertically(self.sensors_panel,self.sheet_panel,-500)
		self.Bind(wx.EVT_SIZE,self.OnResize)		

		self.splitter.SplitHorizontally(self.scroller,self.debug_out,-50)

		self.sizer_top = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.SetSizer(self.sizer_top)
		self.sizer_top.Add(self.sizer_filter,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer_top.Add(self.splitter,20,wx.EXPAND|wx.LEFT|wx.RIGHT)



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
		self.UpdateToggle()


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
			if not util.gAuthen.Authenticate(util.ADMIN):
				return False
		elif not util.gAuthen.Authenticate(util.USER):
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
			if not util.gAuthen.Authenticate(util.ADMIN):
				self.btn_edit.SetToggle(not toggle)
				return 
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
			if wx.NO ==	wx.MessageBox(u'确认换到"传感器"!',
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"Sensor")
			self.refer_sheet.SetEut(Eut())
		elif self.btn_selectType.GetSelection() == 0:
			if wx.NO ==	wx.MessageBox(u'确认更换到"测试记录"!',
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return
			self.box_name.SetLabel(u"时间&&&& (结果)")
			self.box_PN.SetLabel(u"料号")
			self.btn_selectType.SetLabel(u"测试记录")
			self.refer_sheet.SetEut(Test_Record())
		elif self.btn_selectType.GetSelection() == 1:
			if wx.NO ==	wx.MessageBox(u'确认更换到"NTC"!',
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"NTC")
			self.refer_sheet.SetEut(Thermo_Sensor())
		self.refer_sheet.SetDefault( )
		self.btn_selectType.Refresh()
		print "set DB table to  >>>> ",self.refer_sheet.eut.table_name

	def OnSelectDb(self,event):
		"""select db file to query"""
		dlg = wx.FileDialog(None,u"选择数据库文件",wildcard="*.db")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		db_name = dlg.GetPath()
		if db_name: 
			self.refer_sheet.SetDbName(db_name)
		dlg.Destroy()

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
			dlg = wx.FileDialog(None,"请选文件")
			if dlg.ShowModal() != wx.ID_OK:
				dlg.Destroy()
				return
			export_name = dlg.GetPath()
			tofile = codecs.open(export_name,'w+','gb2312')
			dlg.Destroy()

		self.export_detail(tofile)
		if not tofile is sys.stdout:
			tofile.close()

	def export_detail(self,tofile):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

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





####################################################################################################
class Signal(wx.Dialog):
	def __init__(self,window=None,ok_colour="green",bad_colour="red",url=None,table=None):
		super(Signal, self).__init__(parent=None)
		self.window = window
		self.config=util.gSession["signal_config"]
		self.cmd_queue=Queue(-10)
		self.data_queue=Queue(-10)
		self.started_flag = False
		self.thread_source = None
		self.count = 0
		self.xmax= 0.0
		self.ymax= 0.0
		self.SetRefer_entries(table)
		self.Bind(EVT_MY_EVENT, self.OnNewData)
		self.trig_status = False
		self.record = Test_Record()
		#self.NewRecordSN = ''
		self.result = True
		self.thermo = Thermo()
		self.Vout = 0.001
		self.Vout_req = 0.001
		self.temprature  = 0
		self.temprature_count  = 0
		self.Vout_adj_count = 5
		self.Charge_time = 1 

		self.sleep_cnt =0
		self.CHANGE_LEVEL=3
		self.JITTER_LEVEL=2
		self.thermo_count = 0
		self.thermo_PT = 0
		self.thermo_NTC = 0

		self.step_count = 0
		self.single_count = 0

	def GetConfig(self):
		return self.config

	def SetOption(self,cfg_panel):
		self.SetUrl(cfg_panel.GetUrl())
		self.SetOkColour(cfg_panel.GetOkColour())
		self.SetBadColour(cfg_panel.GetBadColour())
		self.SetBackColour(cfg_panel.GetBackColour())
		self.SetGridColour(cfg_panel.GetGridColour())
		self.SetFilterOption(cfg_panel.GetFilterOption())
		self.SetAutoOption(cfg_panel.GetAutoOption())
		self.SetAutoSaveOption(cfg_panel.GetAutoSaveOption())
		self.SetYmirrorOption(cfg_panel.GetYmirror_Option())
		self.SetVrefs(cfg_panel.GetVrefs())

	def GetVrefs(self):
		return  self.config["Vrefs"]

	def SetVrefs(self,Vrefs):
		self.config["Vrefs"] = Vrefs
		return  self.config["Vrefs"]

	def GetFilterOption(self):
		return  self.config["filter_option"]
		
	def SetFilterOption(self,option):
		self.config["filter_option"] = option
		if option == True:
			self.cmd_queue.put("Filter:On")
		else:
			self.cmd_queue.put("Filter:Off")
		return option

	def GetYmirrorOption(self):
		return  self.config["YmirrorOption"]

	def SetYmirrorOption(self,mirror):
		if mirror:
			self.config["YmirrorOption"] = True
		else:
			self.config["YmirrorOption"] = False
		return self.config["YmirrorOption"]

	def GetAutoOption(self):
		return  self.config["AutoOption"]

	def SetAutoOption(self,auto):
		if auto:
			self.config["AutoOption"] = True
		else:
			self.config["AutoOption"] = False
		return self.config["AutoOption"]

	def GetAutoSaveOption(self):
		return  self.config["AutoSaveOption"]

	def SetAutoSaveOption(self,auto):
		if auto:
			self.config["AutoSaveOption"] = True
		else:
			self.config["AutoSaveOption"] = False
		return self.config["AutoSaveOption"]

	def SetRecord(self,record):
		if not isinstance(record,Test_Record):
			return
		self.record = record

	def GetRecord(self):
		return self.record

	def SetVout(self,value_float):
		self.Vout_req = value_float
		self.Vout_adj_count = 8
		threading.Timer(0.2,self.SetVout_).start()

	def SetVout_(self):
		gVdd = pga.gPGA.Vrefs[_VDD]
		self.Vout_adj_count -= 1
		if self.Vout_adj_count != 0: 
			threading.Timer(1,self.SetVout_).start()
		deltaV = self.Vout_req - self.Vout
		deltaHex = abs(deltaV)/(gVdd*pga.gVout_Amp)*pga.gVout_Full*self.Charge_time 
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
		eut = util.gSession["eut"]
		rangeHL_cmd = "setup:PLC:com3:9600"
		self.cmd_queue.put(rangeHL_cmd)
		print "signal cmd>>>%s"%rangeHL_cmd 
		time.sleep(0.1)
		rangeH,rangeL = eut.GetXrange()
		rangeHL_cmd = "setup:PLC:rangeHL:%d;%d"%(rangeH,rangeL)
		print "signal cmd>>>%s"%rangeHL_cmd 
		self.cmd_queue.put(rangeHL_cmd)

	def SetEut_(self):#extract PN from eut object
		eut = util.gSession["eut"]
		if not isinstance(eut,Eut):
			print "Error: invalid type, should be Eut!"
			return None
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
		self.config["ok_colour"] = colour
		return self.config["ok_colour"]

	def GetOkColour(self):
		return self.config["ok_colour"]

	def GetBackColour(self):
		return self.config["BackColour"]

	def SetBackColour(self,colour):
		self.config["BackColour"] = colour
		return self.config["BackColour"]

	def GetGridColour(self):
		return self.config["GridColour"]

	def SetGridColour(self,colour):
		self.config["GridColour"] = colour
		return self.config["GridColour"]


	def SetBadColour(self,colour):
		self.config["bad_colour"] = colour 
		return  self.config["bad_colour"]

	def GetBadColour(self):
		return  self.config["bad_colour"]

	def SetUrl(self,url):
		if not url:
			return None
		self.config["url"]= url
		return self.config["url"]

	def GetUrl(self):
		return self.config["url"]

	def SetRefer_entries(self,table):
		#Warning: update config first before doing anything,先进行配置更新，再做其它!!!
		self.config=util.gSession["signal_config"]
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
		eut = util.gSession["eut"]
		cmd_map     =   {'Ohm':'R','ohm':'R',
				'Vol':'U','vol':'U',
				'Amp':'I','amp':'I',
				}

		#根据单位设置RUI
		unit = eut.GetYunit()
		sw_cmd = "adc:swt:%s:"%(cmd_map[unit[:3]])
		print sw_cmd
		self.cmd_queue.put(sw_cmd)
		time.sleep(0.1)

		#根据range_设置PGA
		range_ = eut.GetRange()
		r_code,a_code =  pga.gPGA.find_solution(range_,unit)
		pga_cmd = "adc:pga:r:%d:a:%d"%(r_code,a_code)
		print pga_cmd
		self.cmd_queue.put(pga_cmd)
		time.sleep(0.1)
		if self.AutoOption :
			self.SetRangHL()


		


	def Run(self):
		if self.started_flag != True:
			self.started_flag = True
			self.thread_source = Data_Source(self,self.GetUrl(),self.cmd_queue,self.data_queue)
			self.thread_source.setDaemon(True)
			self.thread_source.start() #启动后台线程, 与endpoint server进行连接与通信
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
		self.step_count = 0
		#self.window.SetUnknown()
		self.window.Refresh(True)


	def Pause(self):
		print "signal pause.....\n"
		self.cmd_queue.put("stop:")
		while not self.data_queue.empty(): # flush outdated data
			self.data_queue.get()
		#self.Init_Data()

	def Configure(self,command):
		self.cmd_queue.put(command)
	
	def SampleThermo(self):
		eut = util.gSession["eut"]
		if not eut.HasNTC():
			return
		thermo_cmd = "adc:temp:"
		#print thermo_cmd
		self.cmd_queue.put(thermo_cmd)
		#if self.trig_status:
		#	threading.Timer(0.08,self.SampleThermo).start()


	def SetDataRates(self,data_rates):
		self.window.window.ShowDataRates(data_rates)

	def OnNewData(self, event):
		if not self.refer_entries:
			return
		out = ''
		pos = 0
		value = 0
		eut = util.gSession["eut"]
		while not self.data_queue.empty():
			item = self.data_queue.get()
			if isinstance(item,dict):
				if self.trig_status == False:
					continue
				Xvalue_,Yvalue_ = item["value"]
				#print "Xvalue,Yvalue:",Xvalue,';',Yvalue_
				Xvalue = pga.gPGA.Get_Hex2MiliMeter(Xvalue_)
				Yvalue = pga.gPGA.Get_Hex2Float(Yvalue_)
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
				#检测到错误数据出现，处理并更新UI
				if (ystatus== False and item['flag'] != 'new') or (self.single_count > self.JITTER_LEVEL):
					status = False
					self.result = False
					self.record.SetResultFail()
					self.window.UpdateRecord()
				else:
					status = True
				record= Refer_Entry(
						Xvalue=Xvalue,
						Yvalue=Yvalue,
						Xprecision=Xprecision,
						Yprecision=Yprecision,
						valid_status=status)
				record.SetLength(length)
				self.record.AppendRecord(
					Record_Entry(
						refer	= refer_entry,
						record	= record
						)
					)
				#self.window.window.UpdateRecordOnce() # signal_control.UpdateRecord()
				self.window.Refresh(True)
			else:
				if item.startswith("trigger"):
					print "'signal' triggering.........."
					self.trig_status = True
					self.sleep_cnt = 0
					self.result = True
					self.Init_Data()
					self.record.InitRecord()
					self.window.UpdateRecord()
				elif item.startswith("sleep"):
					print "'signal' sleeping.........."
					self.sleep_cnt += 1
					if self.sleep_cnt == self.CHANGE_LEVEL: #New Eut inserted
						self.sleep_cnt = 0
						self.SampleThermo()# It's time to sample thermo!
						NewRecordSN = self.record.AdjustSN(1)#update SN!
					if  self.trig_status == True:
						self.trig_status = False
						if (self.result == False)\
								or (self.record.GetNTCresult() == False) \
								or (self.step_count != len(self.refer_entries)\
									and self.step_count != len(self.refer_entries)*2-1 ) :
							self.record.SetResultFail()
							print "test fail.........."
						else:
							self.record.SetResultPass()
							print "test pass!!!!!!!!!!!"
						if self.AutoSaveOption == True:
							print "saving.........."
							self.record.Save2DBZ()
							print "saving ok.........."
						print "step count ___%d ; \trefer entries__%d"%(self.step_count,len(self.refer_entries) )
					self.window.UpdateRecord()
					self.window.Refresh(True)
				elif item.startswith("0t:"):
					if not eut.HasNTC():
						continue
					hex_NTC = int(item[3:7],16)# protocol: '0t:nnnnpppp..........'
					hex_PT  = int(item[7:11],16)
					self.thermo_count += 1
					self.thermo_NTC   += hex_NTC
					self.thermo_PT    += hex_PT
					if self.thermo_count == 1:
						self.thermo_NTC  /= self.thermo_count
						self.thermo_PT   /= self.thermo_count
						self.record.SetupThermo(self.thermo_NTC,self.thermo_PT)
						self.thermo_count = 0
						self.thermo_NTC   = 0 
						self.thermo_PT    = 0 
						self.window.UpdateRecord()
				elif item.startswith("0v:"):
					hex_Vout = int(item[3:7],16)# protocol: '0t:vvvvpppp..........'
					hex_PT = int(item[7:11],16)
					self.Vout = pga.gPGA.Get_Hex2Vout(hex_Vout)
					self.temprature  += gThermo.GetTemprature(hex_PT)
					self.temprature_count += 1
					if self.temprature_count == 10:
						self.temprature /= 10
						self.record.SetThermo(self.temprature)
						self.window.UpdateRecord()
						self.temprature_count = 0
						self.temprature = 0
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

#index for circuit node
class Vrefs_cfgUI(wx.Dialog):
	def __init__(self,  parent=None, 
		id=-1,caption=u"Vrefs setup",Vrefs=[]):
		super(Vrefs_cfgUI, self).__init__(parent,id,caption)
		self.Vrefs=Vrefs

		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.SetSizer(self.topsizer)
		self.topsizer.Add((100,20))
		
		self.TextVref   = wx.TextCtrl(self,-1)
		self.TextVref.SetValue(str(self.Vrefs[pga._VREF]))
		self.TextVadc   = wx.TextCtrl(self,-1)
		self.TextVadc.SetValue(str(self.Vrefs[pga._VADC]))
		self.TextVdd   = wx.TextCtrl(self,-1)
		self.TextVdd.SetValue(str(self.Vrefs[pga._VDD]))
		self.TextPmm   = wx.TextCtrl(self,-1)
		self.TextPmm.SetValue(str(self.Vrefs[pga._PMM]))
		self.topsizer.Add(wx.StaticText(self,-1,u"参考电压Vref"))
		self.topsizer.Add((40,10))
		self.topsizer.Add(self.TextVref)		
		self.topsizer.Add((40,40))
		self.topsizer.Add(wx.StaticText(self,-1,u"ADC电压Vadc"))
		self.topsizer.Add((40,10))
		self.topsizer.Add(self.TextVadc)		
		self.topsizer.Add((40,40))
		self.topsizer.Add(wx.StaticText(self,-1,u"数字电压Vdd"))
		self.topsizer.Add((40,10))
		self.topsizer.Add(self.TextVdd)
		self.topsizer.Add(wx.StaticText(self,-1,u"脉冲数/mm"))
		self.topsizer.Add((40,10))
		self.topsizer.Add(self.TextPmm)

		btnszr = self.CreateButtonSizer(wx.OK|wx.CANCEL) 
		self.topsizer.Add((40,20))
		self.topsizer.Add(btnszr, 0,wx.EXPAND|wx.ALL, 5) 
		self.Fit()

	def GetVrefs(self):	
		self.Vrefs[pga._VREF] = float(self.TextVref.GetValue())
		self.Vrefs[pga._VADC] = float(self.TextVadc.GetValue())
		self.Vrefs[pga._VDD] = float(self.TextVdd.GetValue())
		self.Vrefs[pga._PMM] = float(self.TextPmm.GetValue())
		return self.Vrefs

class signal_cfgUI(wx.Panel):
	def __init__(self,  parent=None, id=-1, signal=None) :

		super(signal_cfgUI, self).__init__(parent, id)
		self.signal = signal
		self.config = copy.deepcopy(signal.GetConfig())
		
		
		self.Vrefs_btn = wx.Button(self,-1,u"校准")
		self.Vrefs_txt = wx.StaticText(self,-1)
		self.Vrefs_btn.SetBackgroundColour("red")
		#self.url_btn = wx.Button(self,-1,"set URL")
		self.ok_color_btn = wx.Button(self,-1,"Ok color")
		self.bad_color_btn = wx.Button(self,-1,"Bad color")
		url_box = wx.StaticBox(self, wx.ID_ANY, u"URL,如 127.0.0.1:8088/usb1",size=(200,50))
		url_sizer = wx.BoxSizer(wx.VERTICAL)
		self.url= wx.TextCtrl(url_box,-1,self.config["url"],size=(200,-1), style=wx.TE_PROCESS_ENTER)
		self.url.SetEditable(False)
		self.url.Bind(wx.EVT_LEFT_DCLICK, self.OnSetUrl)
		url_box.SetSizer(url_sizer)
		url_sizer.Add((40,20))
		url_sizer.Add(self.url)

		color_box = wx.StaticBox(self,-1, u"--背景色----------参考线色--",size=(170,50))
		box_sizer = wx.BoxSizer(wx.VERTICAL)
		back_color_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
		box_sizer.Add((40,20))
		box_sizer.Add(back_color_box_sizer)
		color_box.SetSizer(box_sizer)
		self.back_color_btn = wx.Button(color_box)
		self.grid_color_btn = wx.Button(color_box)
		back_color_box_sizer.Add(self.back_color_btn) 
		back_color_box_sizer.Add((3,10)) 
		back_color_box_sizer.Add(self.grid_color_btn) 

		self.Ymirror_option = wx.CheckBox(self,-1,u"Y镜像",(20,20),(160,-1))
		self.filter_option = wx.CheckBox(self,-1,u"使用滤波器",(20,20),(160,-1))
		self.auto_option = wx.CheckBox(self,-1,u"自动",(20,20),(160,-1))
		self.auto_save_option = wx.CheckBox(self,-1,u"保存",(20,20),(160,-1))
		self.filter_option.SetValue(self.config["filter_option"])
		self.auto_option.SetValue(self.config["AutoOption"])
		self.auto_save_option.SetValue(self.config["AutoSaveOption"])
		self.Ymirror_option.SetValue(self.config["YmirrorOption"])
		self.ok_color_btn.SetBackgroundColour(self.config["ok_colour"])
		self.bad_color_btn.SetBackgroundColour(self.config["bad_colour"])
		self.back_color_btn.SetBackgroundColour(self.config["BackColour"])
		self.grid_color_btn.SetBackgroundColour(self.config["GridColour"])
		self.ok_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.bad_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.back_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.grid_color_btn.Bind(wx.EVT_BUTTON, self.SelectColor)
		self.Vrefs_btn.Bind(wx.EVT_BUTTON, self.OnVrefsSetup)
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.topsizer.Add(self.Vrefs_btn)
		self.topsizer.Add(self.Vrefs_txt,1,wx.EXPAND|wx.ALL)
		self.topsizer.Add((100,20))
		self.topsizer.Add(url_box)
		
		self.hsizer= wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.hsizer.Add((20,20))
		#self.hsizer.Add(self.ok_color_btn)
		self.ok_color_btn.Show(False)
		self.hsizer.Add((20,20))
		#self.hsizer.Add(self.bad_color_btn)
		self.bad_color_btn.Show(False)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.hsizer)		
		self.topsizer.Add((40,20))
		self.topsizer.Add(color_box)		
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.filter_option)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.auto_option)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.auto_save_option)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.Ymirror_option)
		
		self.SetSizer(self.topsizer)
		self.Fit()
		self.ShowVrefs()

	def GetConfig(self):
		return	self.config

	def ShowVrefs(self):
		Vrefs = self.config["Vrefs"]
		Vrefs_str = u"Vref: %.4fV     \nVadc: %.4fV     \nVdd:  %.4fV   \n脉冲数/mm:%.2f"%(Vrefs[pga._VREF],Vrefs[pga._VADC],Vrefs[pga._VDD],Vrefs[pga._PMM])
		self.Vrefs_txt.SetLabel(Vrefs_str)

	def GetSignal(self):
		return self.signal

	def OnSetUrl(self, evt):
		if not util.gAuthen.Authenticate(util.ADMIN):
			return
		dlg =  wx.TextEntryDialog(None,u"请输入信源URL",u"URL输入",self.url.GetValue(),style=wx.OK|wx.CANCEL)
		if dlg.ShowModal() == wx.ID_OK:
			self.url.SetValue(dlg.GetValue())
		dlg.Destroy()

	def OnVrefsSetup(self,event):
		if not util.gAuthen.Authenticate(util.ADMIN):
			return 
		Vrefs = self.config["Vrefs"]
		dlg = Vrefs_cfgUI(Vrefs=copy.deepcopy(Vrefs))
		if dlg.ShowModal() == wx.ID_OK:
			self.config["Vrefs"] = dlg.GetVrefs()
			self.ShowVrefs()
			#pga.gPGA.SetVrefs(self.Vrefs)
		dlg.Destroy()

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
		elif event.GetId() == self.ok_color_btn.GetId():
			print "set bad color"
			self.bad_color_btn.SetBackgroundColour(color)
		elif event.GetId() == self.back_color_btn.GetId():
			print "set back color"
			self.back_color_btn.SetBackgroundColour(color)
		elif event.GetId() == self.grid_color_btn.GetId():
			print "set grid color"
			self.grid_color_btn.SetBackgroundColour(color)
		dlg.Destroy()

	def GetOkColour(self):
		return self.ok_color_btn.GetBackgroundColour()

	def GetBadColour(self):
		return self.bad_color_btn.GetBackgroundColour()

	def GetBackColour(self):
		return self.back_color_btn.GetBackgroundColour()

	def GetGridColour(self):
		return self.grid_color_btn.GetBackgroundColour()

	def GetUrl(self):
		return self.url.GetValue()

	def GetFilterOption(self):
		return self.filter_option.IsChecked()

	def GetYmirror_Option(self):
		return self.Ymirror_option.IsChecked()

	def GetAutoOption(self):
		return self.auto_option.IsChecked()

	def GetAutoSaveOption(self):
		return self.auto_save_option.IsChecked()
	
	def GetVrefs(self):
		return  self.config["Vrefs"]



############################################################################################################################################
class Dialog_Setup(wx.Dialog):
	""" configure the run time parameters """
	def __init__(self,  parent=None, 
		id=-1,caption=u"URL&UI setup", signals=[]) :

		super(Dialog_Setup, self).__init__(parent,id,caption)
		
		self.topsizer= wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.sig_sizer= wx.BoxSizer(wx.HORIZONTAL)
		self.cfg_panels = []
		for signal in signals:
			if not signal:
				continue
			cfg_panel = signal_cfgUI(self,-1,signal)
			self.cfg_panels.append(cfg_panel )
			self.sig_sizer.Add(cfg_panel,0,wx.EXPAND|wx.ALL,5)
		self.topsizer.Add((40,20))
		self.topsizer.Add(self.sig_sizer)		

		btnszr = self.CreateButtonSizer(wx.OK|wx.CANCEL) 
		self.topsizer.Add((40,20))
		self.topsizer.Add(btnszr, 0,wx.EXPAND|wx.ALL, 5) 

		self.SetSizer(self.topsizer)
		self.Fit()

Y_ = 0
TEXT = 1
SHOW = 2
VALUE = 3
############################################################################################################################################
class Signal_Panel(wx.lib.scrolledpanel.ScrolledPanel):   #3
	def __init__(self,  parent=None,
			size=(-1,-1),
			id=-1,
	 		signals=[],
			window=None):
		super(Signal_Panel, self).__init__(parent, id,size=size)
		#panel 创建
		self.window = window
		self.SetupScrolling(scroll_x=True, scroll_y=False, rate_x=20, rate_y=20)
		self.SetupScrolling() 
		if signals:
			self.SetSignals(signals)
		self.SetEut()
		self.grid_colour= wx.Colour(250,0,250,200)
		self.ok_colour= wx.Colour(0,0,250,200)
		self.bad_colour= wx.Colour(250,0,0,200)
		#self.refer_tables = None

		self.Bind(wx.EVT_PAINT, self.OnPaint)
		#self.Bind(wx.EVT_LEFT_DCLICK, self.OnShowCurrent)
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
		self.Bind(wx.EVT_MENU, self.OnSelectEut,self.menu_eut)
		self.Bind(wx.EVT_MENU, self.OnLogSetup,self.menu_log)
		#self.Bind(wx.EVT_WHEEL, self.OnZoom)
		#self.Bind(wx.EVT_MENU, self.OnSave,self.menu_save)
		self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.Bind(wx.EVT_CHAR, self.OnKeyDown)
		self.grid_v = [] 
		self.SetRenderDefault()
		
	def GetInfo(self):
		record= self.GetRecord()
		PN = record.GetPN()
		SN = record.GetSN()
		Thermo = record.GetThermo()
		NTCrefer = record.GetNTCrefer()
		NTCvalue = record.GetNTCvalue()
		NTCresult = record.GetNTCresult()
		result = record.GetResult()
		return (PN,SN,Thermo,NTCrefer,NTCvalue,NTCresult,result)

	def SetRenderDefault(self):
		self.log10_toggle = False
		self.factorY    = 1.0
		self.offsetY = 100 
		self.screenXsize = 120


	def GetRecord(self):
		return self.signals[0].GetRecord()

	def SetRecord(self,record):
		util.gSession["eut"]= Eut()
		eut = util.gSession["eut"]
		if not isinstance(record,Test_Record):
			return False
		PN = record.GetPN()
		eut.RestoreFromDBZ(PN)
		self.SetEut()
		self.signals[0].SetRecord(record)
		self.window.UpdateRecord()
		self.UpdateRecord()
		return True

	def UpdateRecord(self):
		if self.window:
			wx.PostEvent(self.window,MyEvent(60001)) #tell GUI to update


	def GetGridColour(self):
		return self.signals[0].GetGridColour()


	def GetBackColour(self):
		return self.signals[0].GetBackColour()

	def OnKeyDown(self, event):
		"""KeyDown event is sent first"""
		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()
		#print "raw_code=",raw_code,";modifiers=",modifiers

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
		elif raw_code == 88 and modifiers ==2 :# <ctrl>+<x>     = clear debug_out 
			self.window.clear_out()
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
		elif raw_code == 114 :# <F3> = pause
			self.Pause()
		elif raw_code == 113 :# <F2> = run
			self.Run()
		elif raw_code == 115 :# <F4> = setup
			self.Setup()
		elif raw_code == 116 :# <F5> = full screen
			self.window.ShowFullScreen(True)
		elif raw_code == 27 :# <ESC> = NOT full screen
			self.window.ShowFullScreen(False)
			app=wx.GetApp()
			frame = app.GetTopWindow()
			frame.StopLogo()
		elif raw_code == 118 :# <F7> = open/close debug window
			self.window.SetDebug()
		elif raw_code == 119 :# <F8> = expand/shrink sheet window
			self.window.SetSheet()
		elif raw_code == 120 :# <F9> = hide sheet field
			self.window.HideSheetField()
		elif raw_code == 112 :# <F1> = Select EUT
			self.SelectEut()
		self.Refresh(True)

	def SetScreenXsize(self,Xsize):
		self.screenXsize = Xsize
		print "self.screenXsize",self.screenXsize

	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		#self.PopupMenu(self.popmenu1, pos)

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
		try:
			#self.ToggleRun()#
			self.window.ToggleRun()#
		except:
			pass

	def ToggleRun(self):
		eut = util.gSession["eut"]
		if not eut:
			wx.MessageBox(u"错误：无效的传感器!\n  请先设置传感器!",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
		if util.gRunning != True:
			util.gRunning = True
			print "running..........."
			self.Run()
		else:
			print "pausing..........."
			util.gRunning = False
			self.Pause()
	def Run(self):
		self.menu_run.Toggle() 
		for signal in self.signals:
			if not signal:
				continue
			signal.Run()
			
	def Pause(self):
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
	
	def ResumeSession(self):
		self.SetEut()
		self.Refresh(True)

	def OnSetup(self,evt):
		self.Setup()
	
	def Setup(self):
		dlg = Dialog_Setup(self,-1,u"界面设置",self.signals)
		if dlg.ShowModal()==wx.ID_OK:
			print "setup OK!"
			for cfg_panel in dlg.cfg_panels:
				signal = cfg_panel.GetSignal()
				if not signal:
					continue
				signal.SetOption(cfg_panel)#cfg saved in signal.config
				#pga.gPGA.SetVrefs(signal.GetVrefs())
		else:
			print "setup cancelled!"
		
		dlg.Destroy() #释放资源
		if self.signals[0].config["Vrefs"] is util.gSession["signal_config"]["Vrefs"] or \
			self.signals[0].config["Vrefs"] is pga.gPGA.config["Vrefs"]:
				print "SET VREFS ALL OK!"
		self.Refresh(True)

	def SetSN(self,SN):
		for signal in self.signals:
			if not signal:
				continue
			signal.SetSN(SN)

	def UploadSN(self,SN):
		self.window.UploadSN(SN)

	def SetEut(self):
		#print "end eut show refer...................................................................................................."
		eut = util.gSession["eut"]
		if not eut:
			return
		print "\nload new eut:",eut
		if self.window:
			self.window.SetPN(eut.GetPN())
			if eut.HasNTC():
				self.window.ShowNTC(True)
			else:
				self.window.ShowNTC(False)
			#self.window.SetThermoValue(eut.GetThermoModel())

		refer_tables = eut.GetReferTable()
		i=0
		for signal in self.signals:#map refer_tables to signals as 1:1
			if not signal:
				continue
			signal.SetRefer_entries(refer_tables[i]) #first
			signal.SetEut_()
			i += 1
		self.Refresh(True)
		return True

	def UpdateGridValue(self):
		eut = util.gSession["eut"]
		if not isinstance(eut,Eut):
			return
		refer_table = eut.GetReferTable()[0]
		refer_num = len(refer_table)
		max_Y  = self.GetRect().height
		grid_Y = max_Y/(refer_num+1) 
		self.grid_v = [] 
		for i in range(0,refer_num):
			if self.signals[0].GetYmirrorOption():
				grid_Yi = grid_Y*(i+1) 
			else:
				grid_Yi = grid_Y*(refer_num-i) 
			show = True
			if refer_num > 40 and i%2 != 0:
				show = False
			grid_Vi = float(refer_table[i].GetYvalue())
			grid_Ti = "%.2f"%grid_Vi
			self.grid_v.append([grid_Yi,grid_Ti,show,grid_Vi]) 




	def OnPaint(self,evt):
		#print "redaw"
		self.ReDraw()

	def ReDraw(self):
		dc = wx.PaintDC(self)
		dc.SetBackground(wx.Brush(self.GetBackColour()))
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

	#查表法: 距离算法找到对应区间,线性插值法求值
	def GetGridY_(self,value):
		i0 = 0
		i1 = 1
		last = len (self.grid_v) - 1
		Vmin =  self.grid_v[0][VALUE]
		Vmax =  self.grid_v[last][VALUE]
		ascend= True
		if self.grid_v[0][VALUE]>self.grid_v[last][VALUE]:
			Vmin =  self.grid_v[last][VALUE]
			Vmax =  self.grid_v[0][VALUE]
			ascend= False
		if value <  Vmin:
			if ascend == True:
				i0 = 1
				i1 = 0
			else:
				i0 = last -1
				i1 = last
		elif value >  Vmax:
			if ascend == True:
				i0 = last -1
				i1 = last
			else:
				i0 = 1
				i1 = 0
		else:
			for i in range(0,len(self.grid_v)):
				value_i = self.grid_v[i][VALUE]
				value_j = self.grid_v[i+1][VALUE]
				delta_v_i = abs(value-value_i)
				delta_v_j = abs(value-value_j)
				delta_i_j= abs(value_i-value_j)
				# 距离算法找到对应区间
				if (delta_v_i+delta_v_j) > delta_i_j:
					continue
				i0 = i
				i1 = i+1
				break
		# 线性插值法求值
		delta_Y = self.grid_v[i1][Y_] - self.grid_v[i0][Y_]
		delta_X = self.grid_v[i1][VALUE] - self.grid_v[i0][VALUE]
		deltax = value-self.grid_v[i0][VALUE]
		Y  =   self.grid_v[i0][Y_] + deltax/delta_X*delta_Y 
		return Y


				


	def DrawGrid(self):
		eut = util.gSession["eut"]
		if not  eut:
			return
		self.DrawGrid_v2()

	def DrawGrid_v2(self):
		self.UpdateGridValue()
		dc = wx.ClientDC(self)
		clientRect = self.GetRect()
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		#return
		dc.SetPen(wx.Pen(self.GetGridColour(),1,style = wx.DOT))
		dc.SetTextForeground(self.GetGridColour())
		for grid in self.grid_v:
			if grid[SHOW]!= True:
				continue
			dc.DrawLine(0,grid[Y_] ,clientRect.width,grid[Y_] )
			dc.DrawText(grid[TEXT] ,0,grid[Y_]-15)

	def DrawGrid_v1(self):
		eut = util.gSession["eut"]
		dc = wx.ClientDC(self)
		clientRect = self.GetRect()
		#dc.SetPen(wx.Pen(wx.Colour(100,100,100,200),1,style = wx.SHORT_DASH))
		#return
		dc.SetPen(wx.Pen(self.GetGridColour(),1,style = wx.DOT))
		dc.SetTextForeground(self.GetGridColour())
		refer_num = len(eut.GetReferTable()[0])
		if refer_num < 60:
			sparse = 2
		else:
			sparse = refer_num / 20
		max_height= clientRect.height
		count = 0
		for refer_entry in eut.GetReferTable()[0]:
			count +=1
			if refer_num > 60 and count%sparse!=0:
				continue
			referY_= self.line2log(refer_entry.GetYvalue())
			maxY_ = self.line2log(eut.GetMaxY())
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
		self.DrawSignal_v2(signal,dc,clientRect)

	def DrawSignal_v2(self,signal,dc,clientRect):
		x0_ = 1
		x1_ = 1
		maxY= signal.GetMaxY() 
		maxX= signal.GetMaxX() 
		max_height = clientRect.height
		last_Y0    = max_height
		for data_ in signal.GetData():
			if not data_:
				continue
			if data_.GetYvalue() >= 0:
				#print " data_.Yvalue::",data_.GetYvalue()
				x1_ = x0_ + data_.GetLength()
				x0  = x0_ *self.screenXsize/maxX
				x1  = x1_ *self.screenXsize/maxX
				if data_.GetValid() == True:
					dc.SetPen(wx.Pen(signal.GetOkColour(),2,style = wx.SOLID))
				else:
					dc.SetPen(wx.Pen(signal.GetBadColour(),2,style = wx.SOLID))
				Y0 = self.GetGridY_(data_.GetYvalue())
				dc.DrawLine(x0,Y0,x0,last_Y0)
				dc.DrawLine(x0,Y0,x1,Y0)
				#print "x0,x1,Y0,last_Y0>>>>>>>>>>>>", x0,x1,Y0,last_Y0
				last_Y0 =  Y0
				x0_ = x1_




	def DrawSignal_v1(self,signal,dc,clientRect):
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
					dc.SetPen(wx.Pen(signal.GetOkColour(),2,style = wx.SOLID))
				else:
					dc.SetPen(wx.Pen(signal.GetBadColour(),2,style = wx.SOLID))
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
	
	def OnSelectEut(self,evt):
		self.SelectEut()

	def SelectEut(self):
		Eut_editor = Eut_Editor(self)
		if Eut_editor.ShowModal()!= wx.ID_OK:
			return Eut_editor.Destroy()

		obj_ = Eut_editor.GetEut()
		if not obj_.GetPN():
			return
		if isinstance(obj_ ,Eut):
			util.gSession["eut"] = obj_
			self.SetEut()
		elif isinstance(obj_ ,Test_Record):
			self.SetRecord(obj_ )
		else:
			print u"错误：无效的Sensor!"
			util.ShowMessage(u"错误：无效的Sensor!")
			return False
		return True


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

