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
from data_point import Data_Point,Data_Real,Data_Validated
from data_validator import Data_Validator_Linear
import wx.lib.buttons as buttons 

import wx.lib.agw.balloontip as btip
import struct 
from thread_sqlite import Thread_Sql
import config_db
import sqlite3 as sqlite
import wx.lib.scrolledpanel as scrolledpanel
import codecs
from data_point import Data_Point,Signal_Control_Basic

#index for persist Queue

_CMD = 0
_DATA = 1


#index for eut and named_cells
_MODEL	= 0
_PN	= 1
_NTC	= 2
_NTC_PRC= 3
_UNIT	= 4
#eut only below
_RANGE	= 5#eut only
_REF_PTS= 6#eut only
#named cells only below
_REF_POS= 5#named_cells only
_REF_VAL= 6#named_cells only
_REF_PRC= 7#named_cells only
NAMED_CELLS_NUM= 7+1#named_cells number


#index for refer point
_XVALUE	= 0
_YVALUE	= 1
_PRECISION = 2


#index for named cells
_RC_LABEL	= 0
_LABEL		= 1
_RC_VALUE	= 2
_TYPE		= 3
_MAP		= 4

#index for refer_entry status



class Refer_Entry():
	def __init__(self,Xvalue=0,Xprecision=0,Yvalue=0,Yprecision=0,Yoffset=0):
		self.Xvalue = float( Xvalue)
		self.Xprecision = float( Xprecision)
		self.Yvalue     = float (Yvalue)
		self.Yprecision = float(Yprecision)
		self.Yoffset    = float(Yoffset)
		self.valid_status = False 

	def GetValidStatus(self):
		return self.valid_status

	def SetValidStatus(self,status):#status= True/False
		self.valid_status = status


	def GetXvalue(self):
		return self.Xvalue

	def SetXvalue(self,value):
		self.Xvalue= float(value)

	def GetXprecision(self):
		return self.Xprecision

	def SetXprecision(self,value):
		self.Xprecision= float(value)

	def GetYvalue(self):
		return self.Yvalue

	def SetYvalue(self,value):
		self.Yvalue= float(value)

	def GetYprecision(self):
		return self.Yprecision

	def SetYprecision(self,value):
		self.Yprecision= float(value)

	def GetYoffset(self):
		return self.Yoffset

	def SetYoffset(self,value):
		self.Yoffset= float(value)

class Thermo_Sensor():
	def __init(self,table=None):
		self.table=[]
		if table:
			self.SetTable(table)

	def SetTable(self,table):
		for x in table:
			#!!!!~~~~table item is as of [T,R]~~~!!!!!!!
			#!!!!~~~Xvalue=R, Yvalue=T~~~!!!!!!!
			self.table.append(Refer_Entry(Xvalue=x[1],Yvalue=x[0]))
		self.table.sort((key=lambda x:x.GetYvalue())

	def GetT(self,Rvalue):
		x0 = self.table[0]
		for x1 in self.table:
			#!!!!~~~Xvalue=R, Yvalue=T~~~!!!!!!!
			r0 = x0.GetXvalue()
			r1 = x1.GetXvalue()
			if Rvalue >= r0 and Rvalue <= r1:
				t0 =  x0.GetYvalue()
				t1 =  x1.GetYvalue()
				delta_R = r1 - r0
				delta_T = t1 - t0
				k = delta_T/delta_R
				delta_r =  Rvalue - r0
				tx= t0 + k*delta_r
				break
			x0 = x1

		return tx
			
	def GetR(self,Tvalue):
		x0 = self.table[0]
		for x1 in self.table:
			#!!!!~~~Xvalue=R, Yvalue=T~~~!!!!!!!
			t0 = x0.GetYvalue()
			t1 = x1.GetYvalue()
			if Tvalue >= t0 and Tvalue <= t1:
				r0 =  x0.GetXvalue()
				r1 =  x1.GetXvalue()
				delta_R = r1 - r0
				delta_T = t1 - t0
				k = delta_R/delta_T
				delta_t =  Tvalue - t0
				rx= t0 + k*delta_t
				break
			x0 = x1
		return rx
			
	


class Eut():
	def __init__(self,model=None,PN=None,SN=None,Refer_Table=[[],[]],NTC=None):
		self.model=model
		self.PN = PN
		self.SN = SN
		self.Refer_Table = Refer_Table
		self.NTC = NTC

	def SetReferTable(self,Refer_Table):
		self.Refer_Table = Refer_Table
		for table in self.Refer_Table:
			table.sort(key=lambda x:x.GetYvalue())

	def GetReferTable(self):
		return self.Refer_Table

	def SetNTC(self,NTC):
		self.NTC= NTC

	def GetNTC(self):
		return self.NTC


	def AppendReferTable(self,table_num,refer_entry):
		if not isinstance(Refer_Entry,refer_entry)
			return -1
		try:
			self.Refer_Table[table_num].append(refer_entry)
			self.Refer_Table[table_num].sort(key=lambda x:x.GetYvalue())
			return 1
		except:
			return -2
	def InitValidStatus(self):
		try:
			for table in self.Refer_Table:
				for i in table:
					i.SetValidStatus(False)
		except:
			pass

	def GetY(self,Xvalue,Yvalue,table_num=0):
		yi =None
		if Xvalue != None:# use Xvalue as index
			p0 = self.Refer_Table[table_num][0]
			for p1 in self.Refer_Table[table_num]:
				x0 = p0.GetXvalue()
				x1 = p1.GetXvalue()
				delta0 = abs(Xvalue - x0)
				delta1 = abs(Xvalue - x1)
				if (delta0 + delta1) > abs(x1 - x0):
					p0 = p1
					continue
				if abs(delta0) < abs(delta1): 
					yi =  p0.GetYvalue()
				else:
					yi =  p1.GetYvalue()
				break
		else:# use Yvalue as index
			if Yvalue <= self.Refer_Table[table_num][0].GetYvalue():#outof range
					yi =  self.Refer_Table[table_num][0].GetYvalue()
					self.Refer_Table[table_num][0].SetValidStatus(True)
			elif Yvalue >= self.Refer_Table[table_num][-1].GetYvalue():#outof range
					yi =  self.Refer_Table[table_num][-1].GetYvalue()
					self.Refer_Table[table_num][-1].SetValidStatus(True)
			else:
				p0 = self.Refer_Table[table_num][0]
				for p1 in self.Refer_Table[table_num]:
					if p1.GetValidStatus == True:
						p0 = p1
						continue
					y0 = p0.GetYvalue()
					y1 = p1.GetYvalue()
					delta0 = Yvalue - y0
					delta1 = Yvalue - y1
					if (delta0 + delta1) > abs(y1 - y0):
						p0 = p1
						continue
					if abs(delta0) < abs(delta1): 
						yi =  p0.GetYvalue()
						p0.SetValidStatus(True)
					else:
						yi =  p1.GetYvalue()
						p1.SetValidStatus(True)
					break

		return yi



class Refer_Sheet(wx.lib.sheet.CSheet):
	def __init__(self, parent=None,eut=None): #2 初始化模型
		super(Refer_Sheet, self).__init__(parent)
		self.SetNumberCols(4)
		self.SetNumberRows(205)
		self.number_rows= 203
		self.Init_Named_Cells()
		self.Init_Sheet()
		self.SetEut(eut)
		self.db_name = config_db.eut_db
		self.table_name = config_db.eut_table_name

	def GetEut(self,eut):
		return self.eut

	def SetEut(self,eut):
		self.eut	= eut
		if self.eut:
			self.Update_Cell(self.eut)

	def set_DB_name(self,db_name):
		if db_name:
			self.db_name = db_name

	def Init_Named_Cells(self):
		self.named_cells=[]
		for i in range(0,NAMED_CELLS_NUM):
			self.named_cells.append(None)
		self.named_cells[_MODEL] = [
				(0,0),		# index _RC_LABEL
				u"model/型号",	# index _LABEL
				(1,0),		# index _RC_VALUE
				"text",_MODEL]	# index _TYPE
		self.named_cells[_PN]	=[
				(0,1),
				u"PN/料号",
				(1,1),
				"text",_PN]	# index _TYPE
		self.named_cells[_NTC]	=[
				(2,0),
				u"NTC Resister(Ohm)\nNTC阻值(欧姆)",
				(3,0),
				"float",_NTC]	# index _TYPE
		self.named_cells[_NTC_PRC]=[
				(2,1),
				u"NTC Precision(%)\nNTC精度(%)",
				(3,1),
				"float",_NTC_PRC]	# index _TYPE
		self.named_cells[_UNIT]	=[
				(4,3),
				u"Unit\n单位",
				(5,3),
				"text",_UNIT]	# index _TYPE
		self.named_cells[_REF_POS] =[
				(4,0),
				u"Point\n位置",
				(5,0),
				"float",_REF_POS]	# index _TYPE
		self.named_cells[_REF_VAL] =[
				(4,1),
				u"Value\n参考值",
				(5,1),
				"float",_REF_VAL]	# index _TYPE
		self.named_cells[_REF_PRC] =[
				(4,2),
				u"Precision\n精度",
				(5,2),
				"float",_REF_PRC]	# index _TYPE

	def Init_Sheet(self):
		font_ = self.GetCellFont(0,0)
		font_.SetPointSize(12)
		self.SetDefaultCellFont(font_)
		self.SetDefaultRowSize(35,True)
		self.SetGridLineColour("RED")
		self.SetDefaultCellAlignment(wx.ALIGN_CENTER,wx.ALIGN_CENTER)
		for cell in self.named_cells:
			#print cell
			row,col = cell[_RC_LABEL]
			self.SetReadOnly (row,col,True)
			self.SetCellValue(row,col, cell[_LABEL])
			self.SetCellBackgroundColour(row,col, "Light Grey")
			if len(cell[_LABEL]) > 20:
				self.SetRowSize(row,36)
			if len(cell[_LABEL]) > 10:
				self.SetColSize(col,130)
		self.SetColSize(2,80)
		self.SetRowLabelSize(80)
		row,col = self.named_cells[_UNIT][_RC_VALUE]
		self.SetCellEditor(
				row,
				col,
				wx.grid.GridCellChoiceEditor(
					[u"Ohm",u"V",u"mA"],
					False))
#~~~~~~~~~~~~~~format row labels below~~~~~~~~~~~~~~~~~~~~~
		# !!!!!! first, setup normal cells
		row_labels =	(u"model/PN\n型号/料号","",
				u"NTC Res.\nNTC电阻","",
				u"Ref_values\n参考值")
		row_,col_ = self.named_cells[_MODEL][_RC_LABEL] 
		for row in range(row_,row_+5):
			self.SetRowLabelValue( row, row_labels[row] )
			if row_labels[row]:
				font_.SetPointSize(10)
			else:
				font_.SetPointSize(12)
			for col in range(col_,col_+5):
				self.SetReadOnly(row,col,True)
				self.SetCellBackgroundColour(row,col,"Light Grey")
				self.SetCellFont(row,col,font_)
		row_,col_ = self.named_cells[_REF_POS][_RC_VALUE]
		for row in range(row_,row_+200):
			self.SetRowLabelValue(row,'%d'%(row-4))
			for col in range(col_+3,col_+5):
				self.SetReadOnly(row,col,True)
				self.SetCellBackgroundColour(row,col,"Light Grey")
			for col in range(col_,col_+3):
				self.SetCellEditor(
						row,
						col,
						wx.grid.GridCellFloatEditor())

		# !!!!!! second, setup named cells,override normal cells
		for cell in self.named_cells:
			row,col = cell[_RC_VALUE]
			self.SetReadOnly(row,col,False)
			self.SetCellBackgroundColour(row,col,"white")
			if cell[_TYPE] == "float":
				self.SetCellEditor(
						row,
						col,
						wx.grid.GridCellFloatEditor())
		self.SetEut([
				"mk3",
				"333ke-78dk-233",
				20300,
				1,
				1,
				"200-20300",
				[[1,2,3],[2,2,3],[3,2,3],[4,2,3],[5,2,3],[6,2,3],[7,2,3],[8,2,3],[9,2,3],[10,2,3],[11,2,3],] ])
		pass

	def SetReadOnlyAll(self,read_only):
		for row in range(0,self.number_rows ):
			for col in range(0,self.GetNumberCols()):
				self.SetReadOnly(row,col,read_only)

	
	def SetEditable(self,read_only):
		for cell in self.named_cells:
			row,col = cell[_RC_VALUE]
			self.SetReadOnly(row,col,read_only)
		row_,col_ = self.named_cells[_REF_POS][_RC_VALUE]
		for row in range(row_,self.GetNumberRows()):
			for col in range(col_,col_+3):
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

	def Update_Cell(self,eut):
		#print self.GetNumberRows()
		for cell in self.named_cells[0:5]:
			row,col=cell[_RC_VALUE]
			index = cell[_MAP]
			#print row,col,index
			print index
			print self.eut[index] 
			self.SetCellValue( row, col, str(self.eut[index]) )
		row,col_= self.named_cells[_REF_POS][_RC_VALUE]
		for ref_points in self.eut[_REF_PTS]:
			for col in range(col_, col_ + 3):
				self.SetCellValue( row, col, str(ref_points[col]) )
				_row,_col = self.named_cells[_UNIT][_RC_VALUE]
				if row == _row and col == _col:
					self.SetCellValue( row, col, ref_points[col] )

			row +=1
	def SaveEut(self):
		self.Update_Value()
		self.SetReadOnlyAll(True)

		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		SELECT = "select count(*) from %s where PN like '%s'"%(self.table_name,self.eut[_PN])
		db_cursor.execute(SELECT)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where PN like  '%s'" % (self.table_name, self.eut[_PN])
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
			break

		bytes_block = ''
		for data in self.eut[_REF_PTS]:
			bytes_block += struct.pack('3f',
					data[_XVALUE],
					data[_YVALUE],
					data[_PRECISION],)	
	#	print self.eut[_REF_PTS]
		range_ = "%.2f-%.2f"%(self.eut[_REF_PTS][0][_YVALUE],
				self.eut[_REF_PTS][-1][_YVALUE])
	#	print range_
		eut_b = (self.eut[_MODEL],
			self.eut[_PN],
			self.eut[_NTC],
			self.eut[_NTC_PRC],
			self.eut[_UNIT],
			range_,
			bytes_block) 
		db_cursor.execute("insert into %s values (?,?,?,?,?,?,?)"%self.table_name,eut_b)
		db_con.commit()
		db_con.close()

	def show(self,PN):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()

		SELECT = "SELECT * FROM %s WHERE PN LIKE '%s'" % (self.table_name,PN)
		db_cursor.execute(SELECT)
		eut_b = db_cursor.fetchone()

		model,PN,NTC,NTC_precision,unit,range_,block =  eut_b

		data_points = []
		data_size = struct.calcsize('3f')
		offset = 0
		out = ""
		while 1:
			try:
				data = struct.unpack_from('3f',block, offset)
				offset += data_size
				data_points.append(data)
				#~ print data
			except:
				break
		eut = [model,PN,NTC,NTC_precision,unit,range_,data_points]
		self.SetEut(eut)
		#~ print "start format...\n"
		#~ sys.stdout.flush()
		line  =  str(model)+'\t'+ str(PN)+ '\t'+str(NTC) + '\t'+str(range_) + u'\t清单如下:\n'
		line += u"位置\t参考值 \t \t参考精度"
		print  line
		for curent_data in data_points:
			pos, value, precision= curent_data
			line=  "%04d\t"   % pos
			line+=  "%05.2f\t" % value
			line+=  "%05.2f\t"% precision
			print line

	def query(self,model_pattern,PN_pattern):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		
		SELECT = "SELECT model,PN,range FROM %s WHERE model LIKE '%%%s%%' and PN LIKE '%%%s%%'" %( 
			self.table_name,model_pattern,PN_pattern)
		db_cursor.execute(SELECT)
	
		euts =  db_cursor.fetchall()
		db_con.close()
		return euts


class Refer_Editor(wx.Frame):
	def __init__(self, 
			parent=None, 
			id=-1,
			size=(1024,768),
			pos=wx.DefaultPosition,
			title='model editor',
			entries=None):
		super(Refer_Editor, self).__init__(parent, id, title,size=size)
		self.db_name = config_db.eut_db
		self.table_name = config_db.eut_table_name
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
		self.btn_new = wx.Button(self,-1,u"新建")
		self.btn_save = wx.Button(self,-1,u"保存")
		self.btn_select = wx.Button(self,-1,u"选择")
		self.btn_edit = buttons.GenToggleButton(self,-1,u"编辑")
		self.sizer_btn_1.Add(self.btn_new)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_save)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_select)
		self.sizer_btn_1.Add((10,10),1)
		self.sizer_btn_1.Add(self.btn_edit)

		self.sizer_btn  = wx.BoxSizer(wx.VERTICAL) 
		self.btn_filter = wx.Button(self,-1,u"筛选")
		self.btn_selectDB = wx.Button(self,-1,u"选择数据库")
		self.sizer_btn.Add(self.btn_filter)
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
		self.btn_filter.Bind(wx.EVT_BUTTON, self.OnFilter,self.btn_filter)
		self.btn_selectDB.Bind(wx.EVT_BUTTON, self.OnSelectDb,self.btn_selectDB)
		self.btn_new.Bind(wx.EVT_BUTTON, self.OnNew,self.btn_new)
		self.btn_save.Bind(wx.EVT_BUTTON, self.OnSave,self.btn_save)
		self.btn_select.Bind(wx.EVT_BUTTON, self.OnSelect,self.btn_select)
		self.btn_edit.Bind(wx.EVT_BUTTON, self.OnToggleEdit,self.btn_edit)

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
		self.eut_list.Bind(wx.EVT_KEY_DOWN, self.OnModeOn,self.eut_list)
		self.eut_list.Bind(wx.EVT_KEY_UP, self.OnModeOff,self.eut_list)
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


		self.status_bar = self.CreateStatusBar()

		self.gauge = wx.Gauge(self.status_bar, -1, 100000, (100, 60), (250, 25), style = wx.GA_PROGRESSBAR)
		self.gauge.SetBezelFace(3)
		self.gauge.SetShadowWidth(3)


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
		print "init ok...."

	def Init_Persist(self):#启动数据库持久化线程,通过队列进行保存与取出数据
		self.persist = (Queue(0),Queue(0))
		sql = Thread_Sql(db_name=self.db_name,
				table_name=self.table_name,
				queue_in=self.persist[_CMD],
				queue_out=self.persist[_DATA]) 
		#sql.setDaemon(True)
		sql.start()

	def OnNew(self, event):
		"""KeyDown event is sent first"""
		print "clear all"
		self.refer_sheet.SelectAll()
		self.refer_sheet.Clear()
		self.refer_sheet.ClearSelection()
		self.refer_sheet.SetReadOnlyAll(False)# Clear readonly First
		self.refer_sheet.Init_Sheet()

	def OnSave(self, event):
		"""KeyDown event is sent first"""
		self.refer_sheet.SaveEut()
		return 

	def OnSelect(self, event):
		"""KeyDown event is sent first"""
		if wx.NO == wx.MessageBox(u"确认要使用此料？",
				style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
			return
		self.selected_eut = self.refer_sheet.eut
		self.Hide()
		print "hidding..."
		pass

	def OnToggleEdit(self, event):
		"""KeyDown event is sent first"""
		toggle = self.btn_edit.GetValue()
		print "toggle edit to ",toggle
		if not toggle:
			self.refer_sheet.SetEditable(False)
		else:
			self.refer_sheet.SetEditable(True)

		pass

#eut looks like [model,PN,NTC,NTC_PRC,unit,ref_points[[pos,value,precision],,,]]
	def Data_Persist(self):
		self.refer_sheet.Update_Value()
		bytes_block = ''
		#for cell in self.refer_sheet.named_cells:
		#row_,col_ = self.named_cells[_REF_POS][_RC_VALUE]
		for data in self.refer_sheet.eut[_REF_PTS]:
			bytes_block += struct.pack('3f',
					data[_XVALUE],
					data[_YVALUE],
					data[_PRECISION],)	
		print self.refer_sheet.eut[_REF_PTS]
		range_ = "%.0f-%.0f"%(self.refer_sheet.eut[_REF_PTS][0][_YVALUE],
				self.refer_sheet.eut[_REF_PTS][-1][_YVALUE])
		print range_
		cmd =  ("data:",("save:",(self.refer_sheet.eut[_MODEL],
					self.refer_sheet.eut[_PN],
					self.refer_sheet.eut[_NTC],
					self.refer_sheet.eut[_NTC_PRC],
					self.refer_sheet.eut[_UNIT],
					range_,
					bytes_block))) 
		self.persist[_CMD].put( cmd)


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

	def OnSelectDb(self,event):
		"""select db file to query"""
		dlg = wx.FileDialog(None,u"选择数据库文件",wildcard="*.db")
		if dlg.ShowModal() != wx.ID_OK:
			return
		db_name = dlg.GetPath()
		if db_name: 
			self.refer_sheet.set_DB_name(db_name)

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
		db_con   = sqlite.connect(self.db_name)
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
		item = self.eut_list.GetFocusedItem()
		PN =  self.eut_list.GetItem(item,2).GetText()
		print "view one",PN
		self.refer_sheet.show(PN)

	def OnFilter(self,event):
		self.eut_list.ClearAll()         

		entries = self.refer_sheet.query(
				model_pattern = self.filter_name.GetValue(),
				PN_pattern = self.filter_PN.GetValue())
		if not entries:
			return
		column = [(1,u"序号",50),(2,u"Model/\n型号",180),(3,u"PN/料号",120),(4,u"Range/范围",120)]
		for  column_ in  column:
			self.eut_list.InsertColumn(column_[0],column_[1],width=column_[2])
		count = 0 
		for  entry_ in entries:
			model,PN,range_ = entry_
			entry = ((0,count+1),(1,model),(2,PN),(3,range_))
			row = self.eut_list.InsertStringItem(
					sys.maxint,
					"%10d"%count)
			for col,value in entry:
				self.eut_list.SetStringItem(row,col,str(value))
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
	frm = Refer_Editor()
	frm.SetSize((1280,800))

	frm.Show()
	app.SetTopWindow(frm)

	app.MainLoop()
