# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys
import glob
import wx 
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
import codecs
from data_point import Data_Point,Signal_Control_Basic






class Dialog_Query(wx.Frame):
	def __init__(self, 
			parent=None, 
			id=-1,
			size=(1024,768),
			pos=wx.DefaultPosition,
			title='query !'):
		super(Dialog_Query, self).__init__(parent, id, title,size=size)
		self.db_name = config_db.Connection_db
		self.SetBackgroundColour("light grey")





		#筛选器控件部分控件
		box_valid=wx.StaticBox(self,label=u"结果")
		sizer_valid = wx.StaticBoxSizer(box_valid,wx.VERTICAL)
		self.filter_valid = wx.ComboBox(self,-1,"Fail",(20,20),(60,20),("All","Pass","Fail"),wx.CB_DROPDOWN)
		sizer_valid.Add(self.filter_valid, 0, wx.ALL, 0)

		box_name=wx.StaticBox(self,label=u"名称")
		sizer_name = wx.StaticBoxSizer(box_name,wx.VERTICAL)
		self.filter_name = wx.TextCtrl(self,-1, size=(200,20))
		sizer_name.Add(self.filter_name, 0, wx.ALL, 0)

		box_serial=wx.StaticBox(self,label=u"编号")
		sizer_serial = wx.StaticBoxSizer(box_serial,wx.VERTICAL)
		self.filter_serial = wx.TextCtrl(self,-1, size=(200,20))
		sizer_serial.Add(self.filter_serial, 0, wx.ALL, 0)

		box_time=wx.StaticBox(self,label=u"时间",style=wx.ALIGN_CENTER)
		sizer_time = wx.StaticBoxSizer(box_time,wx.VERTICAL)
		self.filter_time  = wx.TextCtrl(self,-1, size=(200,20))
		sizer_time.Add(self.filter_time, 0, wx.ALL, 0)

		self.sizer_btn  = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.btn_filter = wx.Button(self,-1,u"筛选")
		self.btn_select = wx.Button(self,-1,u"选择数据库")
		self.sizer_btn.Add(self.btn_filter)
		self.sizer_btn.Add(self.btn_select)
		self.sizer_filter = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_name)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_serial)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_time)
		self.sizer_filter.Add((10,20),1)
		self.sizer_filter.Add(sizer_valid)
		self.sizer_filter.Add(self.sizer_btn)
		self.btn_filter.Bind(wx.EVT_BUTTON, self.OnFilter,self.btn_filter)
		self.btn_select.Bind(wx.EVT_BUTTON, self.OnSelectDb,self.btn_select)

		#列表输出窗口部分
		self.scroller = wx.SplitterWindow(self)
		self.scroller.SetMinimumPaneSize(1)
		#左边列表
		self.panel_signals = wx.ScrolledWindow(self.scroller,-1)
		self.panel_signals.SetScrollbars(1,1,100,100)
		self.sizer_signals = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.panel_signals.SetSizer(self.sizer_signals)
		self.list_signals =wx.ListCtrl(parent=self.panel_signals,
				id=-1,
				style=wx.LC_REPORT,)
		#~ pos=wx.DefaultPosition,
							#~ size=wx.DefaultSize,
							#~ style=wx.LC_REPORT,
							#~ validator=wx.DefaultValidator,
							#~ name="")
		#~ self.il=wx.ImageList(16,16,True)
		#~ for name in glob.glob("smicon??.png"):
			#~ self.il_max = self.il.Add(wx.Bitmap(name, wx.BITMAP_TYPE_PNG))
		#~ self.list_signals.AssignImageList(self.il,wx.IMAGE_LIST_SMALL)

		self.sizer_signals.Add(self.list_signals,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.DOWN)
		#右边输出
		self.panel_info  =  wx.ScrolledWindow(self.scroller,-1)
		self.debug_out   = wx.TextCtrl(self.panel_info,-1,style=(wx.TE_MULTILINE|wx.TE_RICH2|wx.HSCROLL))
		self.sizer_info  = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.panel_info.SetSizer(self.sizer_info)
		self.sizer_info.Add(self.debug_out,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.list_signals.Bind(wx.EVT_LEFT_DCLICK, self.OnViewOne,self.list_signals)
		self.list_signals.Bind(wx.EVT_KEY_DOWN, self.OnModeOn,self.list_signals)
		self.list_signals.Bind(wx.EVT_KEY_DOWN, self.OnModeOff,self.list_signals)
		self.debug_out.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.mode = ""



		self.panel_signals.Hide()
		self.panel_info.Hide()
		self.scroller.SplitVertically(self.panel_signals,self.panel_info,-300)
		self.Bind(wx.EVT_SIZE,self.OnResize)		

		self.sizer_top = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗

		self.SetSizer(self.sizer_top)
		self.sizer_top.Add(self.sizer_filter,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.sizer_top.Add((20,20),1)
		self.sizer_top.Add(self.scroller,20,wx.EXPAND|wx.LEFT|wx.RIGHT)


		status_bar = self.CreateStatusBar()

		self.gauge = wx.Gauge(status_bar, -1, 100000, (100, 60), (250, 25), style = wx.GA_PROGRESSBAR)
		self.gauge.SetBezelFace(3)
		self.gauge.SetShadowWidth(3)


		self.popmenu1 = wx.Menu()
		self.menu_export = self.popmenu1.Append(wx.NewId(), u"导出", u"导出到文本框")
		self.menu_export2file = self.popmenu1.Append(wx.NewId(), u"导出到文件", u"")
		self.menu_view = self.popmenu1.Append(wx.NewId(), u"显示到图形", u"")
		self.Bind(wx.EVT_MENU, self.OnExport,self.menu_export)
		self.Bind(wx.EVT_MENU, self.OnExport,self.menu_export2file)
		self.Bind(wx.EVT_MENU, self.OnViewGUI,self.menu_view)
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnPopup,self.list_signals)

		self.Relayout()
		sys.stdout = self.debug_out

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

	def OnModeOff(self, event):
		"""KeyDown event is sent first"""

		#~ raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		#~ if raw_code == 75 and modifiers==3:
			#~ self.Close()
		if modifiers==2:
			self.mode = ""
	def OnSelectDb(self,event):
		"""select db file to query"""
		dlg = wx.FileDialog(None,u"选择数据库文件",wildcard="*.db")
		if dlg.ShowModal() != wx.ID_OK:
			return
		self.db_name = dlg.GetPath()
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
		#~ self.scroller.SetSize((self.GetSize().x, self.GetSize().y-100 ))
		#~ self.scroller.SplitVertically(self.panel_signals,self.panel_info,-300)
		#~ self.scroller.Layout()
		#~ self.panel_signals.Layout()
		#~ self.panel_info.Layout()
		self.Layout()

		self.panel_signals.Refresh(True)
		self.Refresh(True)		

	def OnViewGUI(self,event):
		item = self.list_signals.GetFocusedItem()
		serial =  self.list_signals.GetItem(item,3).GetText()
		time  =  self.list_signals.GetItem(item,4).GetText()
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

		SELECT = "SELECT * FROM data  WHERE"
		SELECT += " eut_serial LIKE '%%%s%%' " % (serial)
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
		item = self.list_signals.GetFocusedItem()
		serial =  self.list_signals.GetItem(item,3).GetText()
		time  =  self.list_signals.GetItem(item,4).GetText()
		valid = "ALL"
		print "view one"
		self.ViewOne(sys.stdout,serial,time,valid)

	def ViewOne(self,tofile,serial,time,filter_valid_):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

		SELECT = "SELECT * FROM data  WHERE"
		SELECT += " eut_serial LIKE '%%%s%%' " % (serial)
		SELECT += " AND create_time LIKE '%%%s%%' " % (time)

		db_cursor.execute(SELECT)
		row = db_cursor.fetchone()

		name,serial,data_valid,time,data_pack = row

		data_points = []
		data_size = struct.calcsize('I5f')
		offset = 0
		out = ""
		#~ print "start unpack...\n"
		#~ sys.stdout.flush()
		while 1:
			try:
				data = struct.unpack_from('I5f',data_pack, offset)
				data_points.append(data)
				#~ print data
				offset += data_size
			except:
				break
		#~ print "start format...\n"
		#~ sys.stdout.flush()
		if data_valid == 1:
			valid_view = '\nPass: '
		else:
			valid_view = '\nFail: '
		out += valid_view + name + '\t' + serial + '\t' + time + u'数据清单如下:\n'
		out += u"位置\t数值\t参考值\t参考精度\t实际精度\t结果\n"
		print >> tofile, out
		for curent_data in data_points:
			valid = curent_data[0]
			pos   = curent_data[1]
			value= curent_data[2]
			value_refer= curent_data[3]
			precision_refer= curent_data[4]
			precision= curent_data[5]
			if filter_valid_ == "ALL" or filter_valid_ == valid:
				if valid:
					valid_view = u"Pass"

				else:
					valid_view = u"Fail"
					self.debug_out.SetStyle( self.debug_out.GetNumberOfLines(),
							-1,
							wx.TextAttr("yellow","red"))
				line_cur  =  "%4d\t"   % pos
				line_cur +=  "%5.2f\t" % value
				line_cur +=  "%5.2f\t" % value_refer
				line_cur +=  "%5.4f\t\t" % precision_refer
				line_cur +=  "%5.4f\t\t"% precision
				line_cur +=  "%s\n"   % valid_view
				print >> tofile,line_cur
				out += line_cur 
				self.debug_out.SetStyle( self.debug_out.GetNumberOfLines(),
						-1,
						wx.TextAttr("black","white"))
		#return out

	def OnFilter(self,event):
		dialog = wx.ProgressDialog("Query Progress",
				"Query data from database.....",
				maximum=50000,
				parent=self,
				style=wx.PD_ELAPSED_TIME|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)


		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

		tmp_str = self.filter_valid.GetValue()
		if tmp_str == "Pass":
			filter_valid = "1"
		elif tmp_str == "Fail":
			filter_valid = "0"
		else:
			filter_valid = ""

		filter_name = self.filter_name.GetValue()
		filter_serial = self.filter_serial.GetValue()
		filter_time  = self.filter_time.GetValue()

		SELECT = "SELECT * FROM data  WHERE "
		SELECT += " eut_name LIKE '%%%s%%' " % (filter_name)
		SELECT += " AND eut_serial LIKE '%%%s%%' " % (filter_serial)
		SELECT += " AND create_time LIKE '%%%s%%' " % (filter_time)

		if filter_valid  != "":
			SELECT += " AND data_valid=%s " % (filter_valid)

		print SELECT

		self.list_signals.ClearAll()
		column = [(1,u"序号",90),(2,u"结果",60),(3,u"型号名称",130),(4,u"SN编号",150),(5,u"时间",200)]
		for  column_ in  column:
			self.list_signals.InsertColumn(column_[0],column_[1],width=column_[2])

		signals_count = 0
		db_cursor.execute(SELECT)
		while 1:
			item =""
			color = "white"
			try:
				signals_count += 1
				#~ img = random.randint(0, self.il_max)
				#~ self.list_signals.SetItemImage(index, img, img)

				row = db_cursor.fetchone()
				name,serial,data_valid,time,block = row
				if data_valid == True:
					valid = "Pass"
				else:
					valid = "Fail"
					color = "red"
				data = [(1,valid),(2,name),(3,serial),(4,time)]

			except:
				break
			row = "%10d"%signals_count
			index = self.list_signals.InsertStringItem(sys.maxint,row)
			for col_ in data:
				self.list_signals.SetStringItem(index,col_[0],col_[1])
				item_ = self.list_signals.GetItemCount()
			self.list_signals.SetItemBackgroundColour(index, color)
			dialog.Update(signals_count)
			self.gauge.SetValue(signals_count)

		self.PushStatusText(u"共 %d 数据条目找到!"%(signals_count-1))
		dialog.Destroy()

	def OnExport(self,event):
		export_name = ""
		item = self.popmenu1.FindItemById(event.GetId())
		if item.GetText() == u"导出"  :
			tofile = sys.stdout
		else:
			dlg = wx.FileDialog(None,"select a file ")
			if dlg.ShowModal() != wx.ID_OK:
				return
			export_name = dlg.GetPath()
			tofile = codecs.open(export_name,'w+','gb2312')
		item_x = self.list_signals.GetFirstSelected()
		if item_x == -1:
			max_index = self.list_signals.GetItemCount()
			columns = self.list_signals.GetColumnCount()
			out=''
			for column in range(0,columns):
				out += self.list_signals.GetColumn(column).GetText()
				out += ','
			out += '\n'
			for item_index in range(0,max_index):
				for column in range(0,columns):
					out += self.list_signals.GetItem(item_index,column).GetText()
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

		item = self.list_signals.GetFirstSelected()
		output = ''
		while item !=-1:
			serial =  self.list_signals.GetItem(item,3).GetText()
			time  =  self.list_signals.GetItem(item,4).GetText()

			self.ViewOne(tofile,serial,time,filter_valid)
			item = self.list_signals.GetNextSelected(item)
		#print >> tofile, output
		if  export_name != "":
			tofile.close()

	def run_(self):
		origin_stdout = sys.stdout
		sys.stdout= self.debug_out
		self.db_con   =sqlite.connect(self.db_name)
		self.db_con.text_factory = str #解决8bit string 问题
		self.db_cursor=self.db_con.cursor()
		self.db_cursor.execute("SELECT * FROM data ")
		out = u"  序号结果:\t名字\t编号\t时间\n"
		count = 0
		while 1:
			try:
				count += 1
				row = self.db_cursor.fetchone()
				name,serial,data_valid,time,block = row
				out += "%06d "%count
				if data_valid == True:
					out += "Pass:\t"
				else:
					out += "Fail:\t"
				out += "%s\t"%name
				out += "%s\t"%serial

				out += "%s\t"%time
				out += '\n'
			except:
				break
		print out
		sys.stdout = origin_stdout



############################################################################################################################################


if __name__=='__main__':
	app = wx.App()
	frm = Dialog_Query()
	frm.SetSize((800,600))

	frm.Show()
	app.SetTopWindow(frm)

	app.MainLoop()

