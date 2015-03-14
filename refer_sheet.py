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

gModule = False




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
		self.SetNumberRows(0)
		self.Refresh(True)
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


	def UpdateField(self):
		for (name,value) in self.eut.field.items():
			#print "field name&value:",name,value
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
				editor =  wx.grid.GridCellChoiceEditor( [u"Ohm",u"Volt",u"Amp"], False)
				self.SetCellEditor( row+1, col, editor)
			elif re.search(r"X.*unit",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"mm",u"\xb0C"], False)
				self.SetCellEditor( row+1, col, editor)
			elif re.search(r"num",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"1",u"2"], False)
				self.SetCellEditor( row+1, col, editor)

	def UpdateTable(self):
		self.eut.UpdateTable(row=REF_ROW,col=0,window=self)

	def UpdateRecordOnce(self):#called upon new data received
		if not isinstance(self.eut,Test_Record):
			return
		recordn_0,recordn_1 = self.eut.GetLastRecord()
		tables = [[recordn_0,],[recordn_1,]]
		self.eut.UpdateRecord(col=0,window=self,tables=tables)

	def show_record(self,tables):
		for table in tables:
			if not table:
				continue
			for record in table:
				if not record:
					continue
				print record.refer.ShowSensor()
				print record.record.ShowSensor()
			
	def UpdateCell(self):
		self.UpdateTable()
		self.UpdateField()
		#print "update_cell end ", self.eut.field
		self.Refresh(True)




	def SaveEut(self):
		self.eut.Save(window=self)
		

	def show(self,PN):
		self.InitSheet()
		self.eut.RestoreFromDBZ(PN)
		if isinstance(self.eut,Test_Record):
			self.eut.InitTable()
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

