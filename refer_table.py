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
from hashlib import md5

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

#index for named cells
_VALUE	= int(0)
_RC	= int(1)

#index for refer table RC
REF_ROW = 6
REF_COL = 6


class Authen():

	def md5sum(self,text):
		m = md5()
		m.update(text.encode('utf-8'))
		return m.hexdigest()
	
	def Authenticate(self,role):
	
		if role == "Admin":
			message = u"管理密码"
			fname   = "ad01"
		elif role == "User":
			message = u"用户密码"
			fname   = "ad02"

		dlg= wx.PasswordEntryDialog(None, message=message,
				caption=u"input password/输入密码", 
				value="", 
				style=wx.TextEntryDialogStyle,
				pos=wx.DefaultPosition)
		dlg.ShowModal()
		password  = dlg.GetValue()
		dlg.Destroy()
		pwd_ = self.md5sum(password)
		print pwd_,pwd_,pwd_
		f=open(f_name,'r')
		pwd_org=f.read()
		f.close()
		result = False
		if str(pwd_org)[:32] == pwd_:
			result = True
		return result

gAuthen = Authen()
class Refer_Entry(object):
#	__slots__ = {"Xvalue":float,"Xprecision":float,"Yvalue":float,"Yprecision":float,"Yoffset":float,"Ymin":float,"Ymax":float}
	def __init__(self,Xvalue=0,Xprecision=0,Yvalue=0,Yprecision=0,Yoffset=0,Ymin=0,Ymax=0,valid_status=False):
		self.valid_status = valid_status
		self.Xvalue	= self.ToFloat( Xvalue)
		self.Xprecision = self.ToFloat( Xprecision)
		self.Yvalue	= self.ToFloat (Yvalue)
		self.Yprecision = self.ToFloat(Yprecision)
		self.Yoffset	= self.ToFloat(Yoffset)
		self.Ymin = self.ToFloat(Ymin)
		self.Ymax = self.ToFloat(Ymax)

	def ToFloat(self,value):
		if not value:
			value = float(0)
		return float(value)

	def Values(self):
		return (self.Xvalue,self.Xprecision,self.Yvalue,self.Yprecision,self.Yoffset,self.Ymin,self.Ymax)

	def Show(self):
		out = ''
		out += "X:%.3f,"%(self.Xvalue)
		out += "Xp:%.3f,"%(self.Xprecision)
		out += "Y:%.3f,"%(self.Yvalue)
		out += "Yp:%.3f,"%(self.Yprecision)
		out += "Yo:%.3f,"%(self.Yoffset)
		return out

	def ShowThermo(self):
		out = ''
		out += "X:%.3f,"%(self.Xvalue)
		out += "Ymin:%.3f,"%(self.Ymin)
		out += "Y:%.3f,"%(self.Yvalue)
		out += "Ymax:%.3f,"%(self.Ymax)
		return out
	
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

	def GetYmin(self,value):
		return self.Ymin

	def SetYmin(self,value):
		self.Ymin= float(value)

	def GetYmax(self,value):
		return self.Ymax

	def SetYmax(self,value):
		self.Ymax= float(value)

	def GetYprecision(self):
		return self.Yprecision

	def SetYprecision(self,value):
		self.Yprecision= float(value)

	def GetYoffset(self):
		return self.Yoffset

	def SetYoffset(self,value):
		self.Yoffset= float(value)

class Thermo_Sensor():
	#__slots__ = {'ID':str, 'field': dict, 'Refer_Table': list}
	table_name =config_db.thermo_table_name
	db_name = config_db.eut_db
	def __init__(self,PN="",model="",value=0,precision=0,X_unit=u"\xb0C",Y_unit=u"ohm",table=[]):
		self.field = {}
		self.field["PN"]= [PN,(0,0)]
		self.field["model"]= [model,(0,1)]
		self.field["value"]= [value,(2,0)]
		self.field["precision"]=[precision,(2,1)]
		self.field["X_unit"] = [X_unit,(REF_ROW-2,0)]
		self.field["Y_unit"] = [Y_unit,(REF_ROW-2,2)]
		self.Refer_Table = []
		if table:
			self.SetTable(table)

		#as key for db access,

	def SaveField(self,window):
		#print "before save field ...",field
		for (name,value) in self.field.items():
			row,col = value[_RC]
			row +=1
			self.field[name][_VALUE]= window.GetCellValue(row,col)
		#print "after save field ...",field

	def SaveRefer(self,window):
		self.SetReferTable(self.SaveThermoTable(row=REF_ROW,col=0,window=window))

	def SaveRefer_Table(self,table):
		self.Refer_Table = table
		self.Refer_Table.sort(key=lambda x:x.GetYvalue())
		print	self.ShowRefer()

	def SaveThermoTable(self,row,col,window):
		table=[]
		col_ = col
		end = False
		Xvalue,Ymin,Yvalue,Ymax=(0,0,0,0)
		while True:
			row += 1
			col_ = col
			Xvalue = window.GetCellValue(row,col_)
			if len(Xvalue) == 0:
				break
			col_ += 1
			Ymin = window.GetCellValue(row,col_)
			col_ += 1
			Yvalue = window.GetCellValue(row,col_)
			col_ += 1
			Ymax = window.GetCellValue(row,col_)
			table.append(Refer_Entry(Xvalue = Xvalue,
						Ymin = Ymin,
						Yvalue = Yvalue,
						Ymax = Ymax,
						Yoffset = Yoffset))


		return table

	def CreateTable(self,db_cursor):
		db_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'"%self.table_name)
		for x in db_cursor:
			if x[0] <=0 :
				SELECT   = "CREATE TABLE %s ("%(self.table_name)
				SELECT += " PN TEXT,"
				SELECT += " model TEXT,"
				SELECT += " value FLOAT,"
				SELECT += " precision FLOAT,"
				SELECT += " X_unit TEXT,"
				SELECT += " Y_unit TEXT,"
				#SELECT += " create_time TimeStamp NOT NULL DEFAULT(datetime('now','localtime')),"
				SELECT += " Refer_Table BLOB)"
				self.db_cursor.execute(SELECT)
				self.db_con.commit()
			else:
				print "table thermo_sensor existed already."

	def RestoreFromDB(self,PN):
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,PN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] <= 0:
				wx.MessageBox(u"抱歉！此记录不存在!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
				return
			else:
				break
		cmd = "select * from %s where PN like '%s'" % (self.table_name, self.field["PN"])
		db_cursor.execute(cmd)
		eut_b = db_cursor.fetchone()

		self.field["PN"][_VALUE]	= eut_b[0]
		self.field["model"][_VALUE]	= eut_b[1]
		self.field["value"][_VALUE]	= eut_b[2]
		self.field["precision"][_VALUE]	= eut_b[3]
		self.field["X_unit"][_VALUE]	= eut_b[4]
		self.field["Y_unit"][_VALUE]	= eut_b[5]
		self.Refer_Table = self.Blob2Refers(eut_b[6]) 
		db_con.close()

	def Save2DB(self):
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,self.field["PN"])
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where PN like '%s'" % (self.table_name, self.field["PN"])
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
			break
		eut_b = (self.field["PN"][_VALUE],
			self.field["model"][_VALUE],
			self.field["value"][_VALUE],
			self.field["precision"][_VALUE],
			self.field["X_unit"][_VALUE],
			self.field["Y_unit"][_VALUE],
			self.Refers2Blob(self.Refer_Table)) 
		db_cursor.execute("insert into %s values (?,?,?,?,?,?,?)"%self.table_name,eut_b)
		db_con.commit()
		db_con.close()

	def Refers2Blob(self,Refer_Table):
		bytes_block = ''
		for refer_entry in Refer_Table:
			bytes_block += struct.pack('4f',
					refer_entry.GetXvalue(),
					refer_entry.GetYmin(),
					refer_entry.GetYvalue(),
					refer_entry.GetYmax())	
		return bytes_block
	
	def Blob2Refers(self,block):
		data_size = struct.calcsize('4f')
		offset = 0
		Refer_Table=[]
		while 1:
			try:
				data = struct.unpack_from('4f',block, offset)
				offset += data_size
				Refer_Table.append(Refer_Entry(
						Xvalue = data[0],
						Ymin   = data[1],
						Yvalue = data[2],
						Ymax   = data[3],
						))
				#~ print data
			except:
				break
		return Refer_Table


	def ShowRefer(self):
		try:
			for refer_entry in self.Refer_Table:
				print refer_entry.ShowThermo()
		except:
			pass

	def SetField(self,line):
		if line.startswith("#"):
			return
		field_name,value = line.split(',')[:2]
		if self.field.has_key(field_name):
			self.field[field_name][_VALUE] = value
		#as key for db access,

	def SetRefer(self,line):
		if line.startswith("#"):
			return
		
		values = line.split(',')[:-1]#remove '\n'
		if len(values) >=4 :
			entry =  Refer_Entry( Xvalue=values[0],
					Ymin = values[1],
					Yvalue=values[2],
					Ymax= values[3])
		else:
			entry =  Refer_Entry( Xvalue=values[0],
					Yvalue=values[1])
		self.Refer_Table.append(entry)
	
	#used for PT100/1000 and NTC thermo_resistor
	def Import(self,reader):
		for x in range(0,15):
			line = reader.readline()
			if line.startswith('###'):#表格起始标志
				break
			try:
				self.SetField(line)
			except:
				pass
		#clear table and append new values by SetRefer(line)
		del self.Refer_Table
		self.Refer_Table = []
		for line in reader.readlines():
			try:
				self.SetRefer(line)
			except:
				pass
		self.Refer_Table.sort(key=lambda x:x.GetYvalue())


	#used only for PT100/PT1000 thermo_resistor
	def SetTable(self,table): 
		for value in table:
			#!!!!~~~~table item is as of [T,R]~~~!!!!!!!
			#!!!!~~~Xvalue=R, Yvalue=T~~~!!!!!!!
			self.Refer_Table.append(Refer_Entry( Xvalue=value[0],
						Yvalue=value[1]))
		self.Refer_Table.sort(key=lambda x:x.GetYvalue())

	#calculate Thermo from Resistor value
	def GetT(self,Rvalue):
		x0 = self.Refer_Table[0]
		for x1 in self.Refer_Table:
			#!!!!~~~Xvalue=R, Yvalue=T~~~!!!!!!!
			r0 = x0.GetXvalue()
			r1 = x1.GetXvalue()
			delta0 = abs(Rvalue-r0)
			delta1 = abs(Rvalue-r1)
			#judge being within by comparing delta_sum 
			if (delta0+delta1) > abs(r1-r0):
				x0 = x1
				continue
			#found and compute linearly
			t0 =  x0.GetYvalue()
			t1 =  x1.GetYvalue()
			delta_R = r1 - r0
			delta_T = t1 - t0
			k = delta_T/delta_R
			delta_r =  Rvalue - r0
			tx= t0 + k*delta_r
			break

		return tx
			
	#calculate Resistor from Thermo value
	def GetR(self,Tvalue):
		x0 = self.Refer_Table[0]
		for x1 in self.Refer_Table:
			#!!!!~~~Xvalue=R, Yvalue=T~~~!!!!!!!
			t0 = x0.GetYvalue()
			t1 = x1.GetYvalue()
			delta0 = abs(Tvalue-t0)
			delta1 = abs(Tvalue-t1)
			#judge being within by comparing delta_sum 
			if (delta0+delta1) > abs(t1-t0):
				x0 = x1
				continue
			#found and compute linearly
			r0 =  x0.GetXvalue()
			r1 =  x1.GetXvalue()
			delta_R = r1 - r0
			delta_T = t1 - t0
			k = delta_R/delta_T
			delta_t =  Tvalue - t0
			rx= t0 + k*delta_t
			break
		return rx
			
	


class Eut():
	#__slots__ = {'ID':str, 'field': dict, 'Refer_Table': list}
	table_name = config_db.eut_table_name
	db_name = config_db.eut_db
	def __init__(self,model=None,PN=None,SN=None,Refer_Table=[[],[]],thermo_PN=None):
		self.field={}
		self.field["PN"] = [PN,(0,0)]
		self.field["SN"] = [SN,(0,1)]
		self.field["model"]=[model,(0,2)]
		self.field["thermo_PN"] = [thermo_PN,(2,0)]
		self.field["signal_num"] =[ 2,(2,1)]
		self.field["X_unit"] = ["mm",(REF_ROW-2,0)]
		self.field["Y1_unit"] =["ohm",(REF_ROW-2,2)]
		self.field["Y2_unit"] =["ohm",(REF_ROW-2,REF_COL+2)]
		self.Refer_Table = Refer_Table

	def SaveField(self,window):
		#print "before save field ...",field
		for (name,value) in self.field.items():
			row,col = value[_RC]
			row +=1
			self.field[name][_VALUE]= window.GetCellValue(row,col)
		#print "after save field ...",field
	def SaveRefer(self,window):
		table = []
		table0 =  self.SaveSensorTable(row=REF_ROW,col=0,window=window)
		table1 =  self.SaveSensorTable(row=REF_ROW,col=REF_COL,window=window)
		table.append( table0)
		table.append( table1)
		self.SetReferTable(table)
		print	self.ShowRefer()

	def SaveSensorTable(self,row,col,window):
		table=[]
		col_ = col
		end = False
		Xvalue,Xprecision,Yvalue,Yprecision,Yoffset=(0,0,0,0,0)
		while True:
			row += 1
			col_ = col
			Xvalue = window.GetCellValue(row,col_)
			if len(Xvalue) == 0:
				break
			col_ += 1
			Xprecision = window.GetCellValue(row,col_)
			col_ += 1
			Yvalue = window.GetCellValue(row,col_)
			col_ += 1
			Yprecision = window.GetCellValue(row,col_)
			col_ += 1
			Yoffset = window.GetCellValue(row,col_)
			table.append(Refer_Entry(Xvalue = Xvalue,
						Xprecision = Xprecision,
						Yvalue = Yvalue,
						Yprecision = Yprecision,
						Yoffset = Yoffset))


		return table

	def CreateTable(self,db_cursor):
		db_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'"%self.table_name)
		for x in db_cursor:
			if x[0] <=0 :
				SELECT   = "CREATE TABLE %s ("%(self.table_name)
				SELECT += " PN TEXT,"
				SELECT += " SN TEXT,"
				SELECT += " model TEXT,"
				SELECT += " thermo_PN TEXT,"
				SELECT += " signal_num int,"
				SELECT += " X_unit TEXT,"
				SELECT += " Y1_unit TEXT,"
				SELECT += " Y2_unit TEXT,"
				#SELECT += " create_time TimeStamp NOT NULL DEFAULT(datetime('now','localtime')),"
				SELECT += " Refer_Table1 BLOB,"
				SELECT += " Refer_Table2 BLOB)"
				db_cursor.execute(SELECT)
				#self.db_con.commit()
			else:
				print "table eut existed already."

	def RestoreFromDB(self,PN):
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,PN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] <= 0:
				wx.MessageBox(u"抱歉！此记录不存在!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
				return
			else:
				break
		cmd = "select * from %s where PN like '%s'" % (self.table_name, PN)
		db_cursor.execute(cmd)
		eut_b = db_cursor.fetchone()
		#print eut_b

		self.field["PN"][_VALUE]	= eut_b[0]
		self.field["SN"][_VALUE]	= eut_b[1]
		self.field["model"][_VALUE]	= eut_b[2]
		self.field["thermo_PN"][_VALUE]	= eut_b[3]
		self.field["signal_num"][_VALUE]= eut_b[4]
		self.field["X_unit"][_VALUE]	= eut_b[5]
		self.field["Y1_unit"][_VALUE]	= eut_b[6]
		self.field["Y2_unit"][_VALUE]	= eut_b[7]
		del self.Refer_Table
		self.Refer_Table = []
		self.Refer_Table.append(self.Blob2Refers(eut_b[8]))
		self.Refer_Table.append(self.Blob2Refers(eut_b[9]))
		db_con.close()
		#print "field after restore from DB",self.field

	def Save2DB(self):
		#print "before save2db...", self.field
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cretia = self.field["PN"][_VALUE]
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,cretia)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where PN like '%s'" % (self.table_name, cretia)
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
			break
		eut_b = ( self.field["PN"][_VALUE],
			self.field["SN"][_VALUE],
			self.field["model"][_VALUE],
			self.field["thermo_PN"][_VALUE],
			self.field["signal_num"][_VALUE],
			self.field["X_unit"][_VALUE],
			self.field["Y1_unit"][_VALUE],
			self.field["Y2_unit"][_VALUE],
			self.Refers2Blob(self.Refer_Table[0]),
			self.Refers2Blob(self.Refer_Table[1])) 
		db_cursor.execute("insert into %s values (?,?,?,?,?,?,?,?,?,?)"%self.table_name,eut_b)
		db_con.commit()
		db_con.close()

	def Refers2Blob(self,Refer_Table):
		bytes_block = ''
		for refer_entry in Refer_Table:
			bytes_block += struct.pack('5f',
					refer_entry.GetXvalue(),
					refer_entry.GetXprecision(),
					refer_entry.GetYvalue(),
					refer_entry.GetYprecision(),
					refer_entry.GetYoffset())	
		return bytes_block
	
	def Blob2Refers(self,block):
		data_size = struct.calcsize('5f')
		offset = 0
		Refer_Table=[]
		while 1:
			try:
				data = struct.unpack_from('5f',block, offset)
				offset += data_size
				Refer_Table.append(Refer_Entry(
						Xvalue		= data[0],
						Xprecision	= data[1],
						Yvalue		= data[2],
						Yprecision	= data[3],
						Yoffset		= data[4],))
			except:
				break
		return Refer_Table

	def SetField(self,line):
		if line.startswith("#"):
			return
		field_name,value = line.split(',')[:2]
		if self.field.has_key(field_name):
			self.field[field_name][_VALUE] = value
		#as key for db access,
	def SetRefer(self,line):
		if line.startswith("#"):
			return
		
		values = line.split(',')[:-1]#remove '\n'
		refer_entry1 = Refer_Entry(
				Xvalue		=values[0],
				Xprecision	=values[1],
				Yvalue		=values[2],
				Yprecision	=values[3],
				Yoffset		=values[4])
		self.AppendReferTable(0,refer_entry1)
		refer_entry2 = Refer_Entry(
				Xvalue		=values[5],
				Xprecision	=values[6],
				Yvalue		=values[7],
				Yprecision	=values[8],
				Yoffset		=values[9])
		self.AppendReferTable(1,refer_entry2)
		
	def Import(self,reader):
		for x in range(0,15):
			line = reader.readline()
			if line.startswith('###'):#表格起始标志
				break
			try:
				self.SetField(line)
			except:
				pass
		#
		for line in reader.readlines():
			try:
				self.SetRefer(line)
			except:
				pass

	
	def SetReferTable(self,Refer_Table):
		self.Refer_Table = Refer_Table
		for table in self.Refer_Table:
			table.sort(key=lambda x:x.GetYvalue())

	def GetReferTable(self):
		return self.Refer_Table 

	def SetThermoSensor(self,thermo_sensor):
		self.thermo_sensor= thermo_sensor

	def GetThermoSensor(self):
		return self.thermo_sensor


	def AppendReferTable(self,table_num,refer_entry):
		if not isinstance(refer_entry,Refer_Entry):
			return -1
		try:
			self.Refer_Table[table_num].append(refer_entry)
			# use Yvalue as index, and table is sorted by Yvalue
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


	def ShowRefer(self):
		try:
			for table in self.Refer_Table:
				for refer_entry in table:
					refer_entry.Show()
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
				#judge being within by comparing delta_sum 
				if (delta0 + delta1) > abs(x1 - x0):
					p0 = p1
					continue
				#use nearby Yvalue
				if abs(delta0) < abs(delta1): 
					yi =  p0.GetYvalue()
				else:
					yi =  p1.GetYvalue()
				break
		else:# use Yvalue as index, and table is sorted by Yvalue
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
					#judge being within by comparing delta_sum 
					if (delta0 + delta1) > abs(y1 - y0):
						p0 = p1
						continue
					#use nearby Yvalue
					if abs(delta0) < abs(delta1): 
						yi =  p0.GetYvalue()
						p0.SetValidStatus(True)
					else:
						yi =  p1.GetYvalue()
						p1.SetValidStatus(True)
					break

		return yi # if not found, return None object



class Refer_Sheet(wx.lib.sheet.CSheet):
	def __init__(self, parent=None,eut=None): #2 初始化模型
		super(Refer_Sheet, self).__init__(parent)
		self.SetNumberCols(20)
		self.SetNumberRows(500)
		self.number_rows= 500
		#self.Init_Named_Cells()
		self.Init_Sheet()
		self.eut = Eut()
		self.SetEut(eut)
		self.db_name=config_db.eut_db
		self.SetTableName(config_db.eut_table_name)

	def GetEut(self,eut):
		return self.eut

	def SetEut(self,eut):
		if isinstance(eut,Thermo_Sensor) or isinstance(eut,Eut):
			self.eut = eut
			self.UpdateCell()

	def SetDbName(self,db_name):
		if db_name:
			self.db_name = db_name

	def GetDbName(self):
		return	self.db_name

	def SetTableName(self,table_name):
		if table_name:
			self.table_name = table_name 

	def GetTableName(self):
		return self.table_name

	def Init_Sheet(self):
		font_ = self.GetCellFont(0,0)
		font_.SetPointSize(12)
		self.SetDefaultCellFont(font_)
		self.SetDefaultRowSize(35,True)
		self.SetDefaultColSize(100,True)
		self.SetGridLineColour("RED")
		self.SetDefaultCellAlignment(wx.ALIGN_CENTER,wx.ALIGN_CENTER)
		self.SelectAll()
		self.Clear()
		self.ClearSelection()

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

	def UpdateField(self,field):
		font_ = self.GetCellFont(0,0)
		font_.SetPointSize(12)
		for (name,value) in field.items():
			if value[_VALUE]== None:
				value[_VALUE] = ''
			row,col = value[_RC]
			self.SetCellValue(row,col, str(name))
			self.SetCellValue(row+1,col, value[_VALUE])
			self.SetReadOnly(row,col,True)
			self.SetCellBackgroundColour(row,col,"Light Grey")
			self.SetCellFont(row,col,font_)
			if re.search(r"Y.*unit",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"Ohm",u"V",u"mA"], False)
				self.SetCellEditor( row+1, col, editor)
			elif re.search(r"X.*unit",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"mm",u"\xb0°C"], False)
				self.SetCellEditor( row+1, col, editor)
			elif re.search(r"num",name):
				editor =  wx.grid.GridCellChoiceEditor( [u"1",u"2"], False)
				self.SetCellEditor( row+1, col, editor)

	def UpdateNTCTable(self,row,col,table):
		col_ = col
		for name in (u"温度/ \xb0C",u"最小值/ohm",u"中间值/ohm",u"最大值/ohm"):
			self.SetCellValue(row,col_,name)
			self.SetReadOnly(row,col_,True)
			self.SetCellBackgroundColour(row,col_,"Grey")
			col_ +=1
		row_ = row
		for refer_entry in table:
			row_ += 1
			self.SetRowLabelValue(row_,str(row_-row))
			(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
			col_ = col
			for value in (Xvalue,Ymin,Yvalue,Ymax):
				self.SetCellValue(row_,col_,str(value))
				self.SetCellEditor(
					row_,
					col_,
					wx.grid.GridCellFloatEditor())
				col_ += 1

	def UpdateSensorTable(self,row,col,table,table_num):
		table_len = len(table[table_num])+10
		print "table length>>>>>>>>>>>>>>",self.GetNumberRows(),table_len
		if self.GetNumberRows() < table_len:
			self.SetNumberRows(table_len)
		col_ = col
		for name in (u"位置/mm",u"位偏移/mm",u"Sensor%d值"%(table_num+1),u"精度",u"修正值"):
			self.SetCellValue(row,col_,name)
			self.SetReadOnly(row,col_,True)
			self.SetCellBackgroundColour(row,col_,"Grey")
			col_ +=1
		row_ = row
		for refer_entry in table[table_num]:
			row_ += 1
			self.SetRowLabelValue(row_,str(row_-row))
			(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
			col_ = col
			for value in (Xvalue,Xprecision,Yvalue,Yprecision,Yoffset):
				self.SetCellValue(row_,col_,str(value))
				self.SetCellEditor(
					row_,
					col_,
					wx.grid.GridCellFloatEditor())
				col_ += 1

	def UpdateRefer(self,table):
		if isinstance(self.eut,Thermo_Sensor):
			self.UpdateNTCTable(row=5,col=0,table=table)
		elif isinstance(self.eut,Eut):
			self.UpdateSensorTable(row=REF_ROW,col=0,table=table,table_num=0)
			self.UpdateSensorTable(row=REF_ROW,col=REF_COL,table=table,table_num=1)

	def UpdateCell(self):
		self.UpdateField(self.eut.field)
		self.UpdateRefer(self.eut.Refer_Table)
		#print "update_cell end ", self.eut.field


	def SaveSensorTable(self,row,col):
		table=[]
		col_ = col
		end = False
		x= 0
		while True:
			row += 1
			col_ = col
			Xvalue,Xprecision,Yvalue,Yprecision,Yoffset=(0,0,0,0,0)
			Xvalue = self.GetCellValue(row,col_)
			if len(Xvalue) == 0:
				break
			col_ += 1
			Xprecision = self.GetCellValue(row,col_)
			col_ += 1
			Yvalue = self.GetCellValue(row,col_)
			col_ += 1
			Yprecision = self.GetCellValue(row,col_)
			col_ += 1
			Yoffset = self.GetCellValue(row,col_)
			table.append(Refer_Entry(Xvalue = Xvalue,
						Xprecision = Xprecision,
						Yvalue = Yvalue,
						Yprecision = Yprecision,
						Yoffset = Yoffset))


		table.sort(key=lambda x:x.GetYvalue())
		return table

	def SaveField(self,field):
		#print "before save field ...",field
		for (name,value) in field.items():
			row,col = value[_RC]
			row +=1
			field[name][_VALUE]= self.GetCellValue(row,col)
		#print "after save field ...",field
	def SaveRefer_Eut(self):
		table = []
		table.append( self.SaveSensorTable(row=REF_ROW,col=0))
		table.append( self.SaveSensorTable(row=REF_ROW,col=REF_COL))
		for t in table:
			for r in t:
				print "............",r.GetYvalue()
		self.eut.SetReferTable(table)
		print	self.eut.ShowRefer()
		return table

	def SaveEut(self):
		self.eut.SaveField(window=self)
		self.eut.SaveRefer(window=self)
		self.eut.Save2DB()
		

	def show(self,PN):
		self.Init_Sheet()
		self.eut.RestoreFromDB(PN)
		self.UpdateCell()

	def query(self,model_pattern,PN_pattern):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		
		SELECT = "SELECT model,PN FROM %s WHERE model LIKE '%%%s%%' and PN LIKE '%%%s%%'" %( 
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
		dlg = wx.FileDialog(None,u"选择csv文件",wildcard="*.csv")
		if dlg.ShowModal() != wx.ID_OK:
			return
		eut_name = dlg.GetPath()
		if not eut_name:
			return 
		reader =file(eut_name,"r")
		reader.readline()#跳过第一行注释行
		type_ = reader.readline().split(",")
		if type_[1].startswith("NTC"):
			eut = Thermo_Sensor()
		elif type_[1].startswith("sensor"):
			eut = Eut()
		else:
			wx.MessageDialog(None,u"type值错误，必须是NTC或Sensor",u"警告",wx.YES_DEFAULT).ShowModal()
			return 
		
		self.InitSheet()
		eut.Import(reader)
		eut.ShowRefer()
		self.refer_sheet.SetEut(eut)
		print u"temp unit\xb0"

	def OnNew(self, event):
		"""KeyDown event is sent first"""
		dlg = wx.TextEntryDialog(None,u"请输入参考条目数:","  ","200")
		if dlg.ShowModal() == wx.ID_OK:
			num = int(dlg.GetValue())
			self.refer_sheet.SetNumberRows(num)
			if self.refer_sheet.table_name == Eut.table_name:
				self.refer_sheet.SetEut(Eut())
			else:
				self.refer_sheet.SetEut(Thermo_Sensor())


	def InitSheet(self):
		self.refer_sheet.SelectAll()
		self.refer_sheet.Clear()
		self.refer_sheet.ClearSelection()
		self.refer_sheet.SetReadOnlyAll(False)# Clear readonly First
		self.refer_sheet.Init_Sheet()

	def OnSave(self, event):
		if not gAuthen.Authenticate("User"):
			return
		self.refer_sheet.SaveEut()
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
		self.eut = self.refer_sheet.GetEut()

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

	def OnSelectType(self,event):
		"""select table file to query"""
		if self.btn_selectType.GetLabelText() == u"Thermo":
			if wx.NO ==	wx.MessageBox(u"确认更换到Sensor!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				toggle = self.btn_selectType.GetToggle()
				self.btn_selectType.SetToggle(not toggle)
				return

			self.btn_selectType.SetLabel(u"Sensor")
			self.refer_sheet.SetTableName( Eut.table_name )
		else:
			if wx.NO ==	wx.MessageBox(u"确认更换到Thermo!",
					style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
				toggle = self.btn_selectType.GetToggle()
				self.btn_selectType.SetToggle(not toggle)
				return

			self.btn_selectType.SetLabel(u"Thermo")
			self.refer_sheet.SetTableName( Thermo_Sensor.table_name )
		print "set DB table_name to  >>>>>>>>>>>>>>>>>>>>>>>>",self.refer_sheet.table_name

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
		print "view one",PN
		self.refer_sheet.show(PN)

	def OnFilter(self,event):
		self.UpdateToggle()
		self.eut_list.ClearAll()         

		entries = self.refer_sheet.query(
				model_pattern = self.filter_name.GetValue(),
				PN_pattern = self.filter_PN.GetValue())
		if not entries:
			return
		column = [(1,u"序号",50),(2,u"Model/\n型号",180),(3,u"PN/料号",120),]
		for  column_ in  column:
			self.eut_list.InsertColumn(column_[0],column_[1],width=column_[2])
		count = 0 
		for  entry_ in entries:
			model,PN= entry_
			entry = ((0,count+1),(1,model),(2,PN))
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




############################################################################################################################################


if __name__=='__main__':
	app = wx.App()
	frm = Refer_Editor()
	frm.SetSize((1280,800))

	frm.Show()
	app.SetTopWindow(frm)

	app.MainLoop()

