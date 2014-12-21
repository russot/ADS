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
#for zip function

#index for persist Queue
_CMD = 0
_DATA = 1






#index for refer_entry status

#index for named cells
_VALUE	= int(0)
_RC	= int(1)

#index for refer table RC
REF_ROW = 6
REF_COL = 6



class Refer_Sheet(wx.lib.sheet.CSheet):
	def __init__(self, parent=None,eut=None): #2 初始化模型
		super(Refer_Sheet, self).__init__(parent)
		self.SetNumberCols(20)
		self.SetNumberRows(500)
		self.number_rows= 500
		#self.Init_Named_Cells()
		self.InitSheet()
		self.eut = Eut()
		self.SetEut(eut)
		self.db_name=config_db.eut_db

	def GetEut(self):
		return self.eut

	def SetEut(self,eut):
		if isinstance(eut,Thermo_Sensor) or isinstance(eut,Eut) or isinstance(eut,Test_Record):
			self.eut = eut
			self.UpdateCell()

	def SetDbName(self,db_name):
		if db_name:
			self.db_name = db_name

	def GetDbName(self):
		return	self.db_name


	def InitSheet(self):
		self.SetNumberRows(1)
		font_ = self.GetCellFont(0,0)
		font_.SetPointSize(12)
		self.SetDefaultCellFont(font_)
		self.SetDefaultRowSize(35,True)
		self.SetDefaultColSize(100,True)
		self.SetGridLineColour("RED")
		self.SetDefaultCellAlignment(wx.ALIGN_CENTER,wx.ALIGN_CENTER)

	def SetReadOnlyAll(self,read_only):
		for row in range(0,self.number_rows ):
			for col in range(0,self.GetNumberCols()):
				self.SetReadOnly(row,col,read_only)

	
	def SetEditable(self,read_only):
		# from row 7, editable
		for value in self.eut.field.values():
			row,col = value[_RC]
			row += 1
			self.SetReadOnly(row,col,read_only)
		for row in range(REF_ROW+1,self.GetNumberRows()):
			for col in range(0,self.GetNumberCols()):
				self.SetReadOnly(row,col,read_only)

#eut looks like [model,PN,NTC,NTC_PRC,unit,range,ref_points[[pos,value,precision],,,]]
	def Update_Value(self):
		for index in range(0,5):
			row,col	= self.named_cells[index][_RC_VALUE]
			value 	= self.GetCellValue(row,col)
			type_	= self.named_cells[index][_TYPE]
			if type_ == "float":
				self.eut[index] = float(value)
			else:
				self.eut[index] = value

		row,col_ = self.named_cells[_REF_POS][_RC_VALUE]
		end = False
		self.eut[_REF_PTS] = []
		while not end:
			point = []
			for col in range(col_, col_ + 3):
				value = self.GetCellValue(row,col)
				if not value:
					end = True
					break
				point.append(float(value))
			if not end:
				self.eut[_REF_PTS].append(point)
				row +=1
		#sort refer points by YVALUE as below
		self.eut[_REF_PTS].sort(key=lambda x:x[_YVALUE])	

	def UpdateField(self):
		for (name,value) in self.eut.field.items():
			if isinstance(value[_VALUE],int):
				value_str = str(value[_VALUE])
			elif isinstance(value[_VALUE],float):
				value_str = str(round(value[_VALUE],6))
			elif isinstance(value[_VALUE],str):
				value_str = value[_VALUE].decode('utf-8')
			else:
				value_str = value[_VALUE]

			row,col = value[_RC]
			#print value_str,'.....................................................................................................'
			self.SetCellValue(row,col, str(name))
			self.SetCellValue(row+1,col, value_str)
			self.SetReadOnly(row,col,True)
			self.SetReadOnly(row+1, col,True)
			self.SetCellBackgroundColour(row,col,"Light Grey")
			if re.search(r"Y.*unit",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"Ohm",u"V",u"mA"], False)
				self.SetCellEditor( row+1, col, editor)
			elif re.search(r"X.*unit",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"mm",u"\xb0C"], False)
				self.SetCellEditor( row+1, col, editor)
			elif re.search(r"num",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"1",u"2"], False)
				self.SetCellEditor( row+1, col, editor)

	def UpdateTable(self):
		self.eut.UpdateTable(row=REF_ROW,col=0,window=self)

	def UpdateCell(self):
		self.UpdateTable()
		self.UpdateField()
		#print "update_cell end ", self.eut.field




	def SaveEut(self):
		self.eut.Save(window=self)
		

	def show(self,PN):
		self.InitSheet()
		self.eut.RestoreFromDBZ(PN)
		self.UpdateCell()

	def QueryDB(self, model_pattern,PN_pattern):
		return self.eut.QueryDB( model_pattern,PN_pattern)

	def Import(self):
		self.InitSheet()
		self.eut.Import()
		self.UpdateCell()
	
	def NewEut(self):
		dlg = wx.TextEntryDialog(None,u"请输入参考条目数:","  ","200")
		if dlg.ShowModal() == wx.ID_OK:
			num = int(dlg.GetValue())
			self.SetNumberRows(num)
			self.SetDefault()

	def SetDefault(self):
			self.eut.SetDefault()
			self.InitSheet()
			self.UpdateCell()


class Refer_Editor(wx.Dialog):
	def __init__(self, 
			parent=None, 
			id=-1,
			size=(1024,768),
			pos=wx.DefaultPosition,
			title='model editor',
			entries=None):
		super(Refer_Editor, self).__init__(parent, id, title,size=size)
		self.db_name = Eut.db_name 
		#self.SetBackgroundColour("light grey")
		self.entries = entries





		#筛选器控件部分控件
#		box_valid=wx.StaticBox(self,label=u"结果")
#		sizer_valid = wx.StaticBoxSizer(box_valid,wx.VERTICAL)
#		self.filter_valid = wx.ComboBox(self,-1,"Fail",(20,20),(60,20),("All","Pass","Fail"),wx.CB_DROPDOWN)
#		sizer_valid.Add(self.filter_valid, 0, wx.ALL, 0)

		box_name=wx.StaticBox(self,label=u"Model/型号")
		sizer_name = wx.StaticBoxSizer(box_name,wx.VERTICAL)
		self.filter_name = wx.TextCtrl(self,-1, size=(200,20))
		sizer_name.Add(self.filter_name, 0, wx.ALL, 0)

		box_PN=wx.StaticBox(self,label=u"Part_number/料号")
		sizer_PN = wx.StaticBoxSizer(box_PN,wx.VERTICAL)
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
		self.btn_selectType = buttons.GenToggleButton(self,-1,u"Sensor")
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
		self.btn_selectType.Bind(wx.EVT_BUTTON, self.OnSelectType)
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
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnPopup,self.refer_sheet)

		self.Relayout()
		sys.stdout = self.debug_out
		sys.stderr = self.debug_out
		self.UpdateToggle()
		print "sheet init ok...."

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
		if not gAuthen.Authenticate("User"):
			return
		self.refer_sheet.SaveEut()
		self.btn_edit.SetToggle(True)
		self.UpdateToggle()
		return 

	def OnSelect(self, event):
		"""KeyDown event is sent first"""
		if wx.NO == wx.MessageBox(u"确认要使用此料？",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
			return
		if not isinstance(self.refer_sheet.GetEut(),Eut):
			wx.MessageBox(u"您选的不是传感器\n  请选择传感器!!!",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
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

#eut looks like [model,PN,NTC,NTC_PRC,unit,ref_points[[pos,value,precision],,,]]
#	def Data_Persist(self):
#		self.refer_sheet.Update_Value()
#		bytes_block = ''
#		#for cell in self.refer_sheet.named_cells:
#		#row_,col_ = self.named_cells[_REF_POS][_RC_VALUE]
#		for data in self.refer_sheet.eut[_REF_PTS]:
#			bytes_block += struct.pack('3f',
#					data[_XVALUE],
#					data[_YVALUE],
#					data[_PRECISION],)	
#		print self.refer_sheet.eut[_REF_PTS]
#		range_ = "%.0f-%.0f"%(self.refer_sheet.eut[_REF_PTS][0][_YVALUE],
#				self.refer_sheet.eut[_REF_PTS][-1][_YVALUE])
#		print range_
#		cmd =  ("data:",("save:",(self.refer_sheet.eut[_MODEL],
#					self.refer_sheet.eut[_PN],
#					self.refer_sheet.eut[_NTC],
#					self.refer_sheet.eut[_NTC_PRC],
#					self.refer_sheet.eut[_UNIT],
#					range_,
#					bytes_block))) 
#		self.persist[_CMD].put( cmd)


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
		if self.btn_selectType.GetLabelText() == u"Thermo":
			if wx.NO ==	wx.MessageBox(u"确认更换到Sensor!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"Sensor")
			self.refer_sheet.SetEut(Eut())
		elif self.btn_selectType.GetLabelText() == u"Sensor":
			if wx.NO ==	wx.MessageBox(u"确认更换到Record!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"Record")
			self.refer_sheet.SetEut(Test_Record())
		elif self.btn_selectType.GetLabelText() == u"Record":
			if wx.NO ==	wx.MessageBox(u"确认更换到Thermo!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				return

			self.btn_selectType.SetLabel(u"Thermo")
			self.refer_sheet.SetEut(Thermo_Sensor())
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
		item = self.refer_sheet.GetFocusedItem()
		serial =  self.refer_sheet.GetItem(item,3).GetText()
		time  =  self.refer_sheet.GetItem(item,4).GetText()
		db_con   = sqlite.connect(self.refer_sheet.GetDbName())
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

		SELECT = "SELECT * FROM %s  WHERE"%(self.refer_sheet.GetTableName())
		SELECT += " PN LIKE '%%%s%%' " % (serial)
		SELECT += " AND create_time LIKE '%%%s%%' " % (time)

		db_cursor.execute(SELECT)
		row = db_cursor.fetchone()

		name,serial,data_valid,time,data_pack = row

		if data_valid == 1:
			valid_view = '\nPass: '
			bg_color = "grey"
		else:
			valid_view = '\nFail: '
			bg_color = "blue"
		data_points = []
		data_size = struct.calcsize('I5f')
		offset = 0
		out = ""
		while 1:
			try:
				data = struct.unpack_from('I5f',data_pack, offset)
				data_points.append(data)
				#~ print data
				offset += data_size
			except:
				break
		#app = wx.App()
		frame = wx.Frame(parent=None, size=(800,600))
		frame.CreateStatusBar()
		frame.PushStatusText(u"结果：%s  生成时间：%s " % ( valid_view, time ))
		#app.SetTopWindow(frame)
		gui_ctrl=Signal_Control_Basic(parent=frame,
				size_=(1024,768),
				id=-1,
				bg_color = bg_color ,
				color_ok=wx.Color(0,250,0,200),
				color_bad=wx.Color(250,0,0,200),
				eut_name=name,
				eut_serial=serial,
				points=len(data_points)+1)
		maxvalue = max(data_points,key=lambda x:x[2])
		gui_ctrl.SetMaxValue(maxvalue[2])
		index_ = 0
		for data_v in data_points:
			data_v_obj = Data_Validated(valid = data_v[0],
					pos   = data_v[1],
					value= data_v[2],
					value_refer= data_v[3],
					precision_refer= data_v[4],
					precision= data_v[5])
			gui_ctrl.AppendPointValue(index_,data_v_obj)
			index_ += 1
		topsizer = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		topsizer.Add(gui_ctrl,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		frame.SetSizer(topsizer)
		frame.Show(True)
		#app.MainLoop()


	def OnViewOne(self,event):
		item = self.eut_list.GetFocusedItem()
		PN =  self.eut_list.GetItem(item,2).GetText()
		#print "view one",PN
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
				col += 1
			count += 1

		self.PushStatusText(u"共 %d 数据条目找到!"%count)

	def OnExport(self,event):
		export_name = ""
		item = self.popmenu1.FindItemById(event.GetId())
		
		if item.gettext() == u"导出"  :
			tofile = sys.stdout
		else:
			dlg = wx.FileDialog(None,"select a file ")
			if dlg.ShowModal() != wx.ID_OK:
				return
			export_name = dlg.GetPath()
			tofile = codecs.open(export_name,'w+','gb2312')
		item_x = self.refer_sheet.GetFirstSelected()
		if item_x == -1:
			max_index = self.refer_sheet.GetItemCount()
			columns = self.refer_sheet.GetColumnCount()
			out=''
			for column in range(0,columns):
				out += self.refer_sheet.GetColumn(column).GetText()
				out += ','
			out += '\n'
			for item_index in range(0,max_index):
				for column in range(0,columns):
					out += self.refer_sheet.GetItem(item_index,column).GetText()
					out += ','
				out += '\n'
			print >> tofile, out
			if export_name !="":
				tofile.close()
		else:
			self.export_detail(tofile,export_name)

	def export_detail(self,tofile, export_name):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

		tmp_str = self.filter_valid.GetValue()
		if tmp_str == "Pass":
			filter_valid = 1
		elif tmp_str == "Fail":
			filter_valid = 0 
		else:
			filter_valid = "ALL" 

		item = self.refer_sheet.GetFirstSelected()
		output = ''
		while item !=-1:
			serial =  self.refer_sheet.GetItem(item,3).GetText()
			time  =  self.refer_sheet.GetItem(item,4).GetText()

			self.ViewOne(tofile,serial,time,filter_valid)
			item = self.refer_sheet.GetNextSelected(item)
		#print >> tofile, output
		if  export_name != "":
			tofile.close()




############################################################################################################################################


if __name__=='__main__':
	app = wx.App()
	frm = Refer_Editor()
	frm.SetSize((1280,800))

	frm.Show()
	app.SetTopWindow(frm)

	app.MainLoop()

