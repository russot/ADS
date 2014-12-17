# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys
import glob
import wx 
import os 
import string
import time
import const
from Queue import Queue
import math
import re
import struct 
import config_db
import sqlite3 as sqlite
from refer_table import Refer_Entry
import pickle

#index for refer table RC
REF_ROW = 6
REF_COL = 6

#index for named cells
_VALUE	= int(0)
_RC	= int(1)

class Record_Entry():
	def __init__(self,refer=None,record=None):
		# refer_index format: (index_num,table_num)
		# record format: Refer_Entry
		self.refer_index = refer_index
		self.record = record

	def GetReferIndex(self):
		# refer_index format: (index_num,table_num)
		return self.refer_index

	def SetReferIndex(self,index):
		# refer_index format: (index_num,table_num)
		self.refer_index = index

	def GetRecord(self):
		return self.record

	def SetRecord(self,record):
		if isinstance(record,Refer_Entry):
			self.record = record
		else:
			raise ValueError

class TestRecord():
	#__slots__ = {'ID':str, 'field': dict, 'Refer_Table': list}
	table_name = config_db.eut_record_TBname
	db_name = config_db.eut_db

	def __init__(self,PN='',SN='',Record_Table=[[],[]]):
		self.create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		self.Record_Table = Record_Table
		self.result = 'pass'
		self.field = {}
		self.field["PN"] = [PN,(0,0)]
		self.field["SN"] = [SN,(0,1)]
		self.field["model"]=['',(0,2)]
		self.field["time"]=['',(0,3)]
		self.field["tempr"] = ['',(2,0)]
		self.field["NTCvalue"] =['',(2,1)]
		self.field["NTCrefer"] =['',(2,2)]
		self.field["NTCresult"] =['',(2,3)]
		self.field["X_unit"] = ["mm",(REF_ROW-2,0)]
		self.field["Y1_unit"] =["ohm",(REF_ROW-2,2)]
		self.field["Y2_unit"] =["ohm",(REF_ROW-2,REF_COL+2)]
		self.SetSN(SN)

	def SetSN(self,SN):
		if not SN or not isinstance(SN,str):
			print "Warning:invalid SN, SN is set to 'ABCD-0000001'!"
			self.field["SN"][_VALUE]='ABCD-0000001'
			return
		self.field["SN"][_VALUE]=SN

	def AdjustSN(self,x):
		index = -1
		digits =  0
		SN = self.field["SN"][_VALUE]
		while  SN[index:].isdigit():
			index -= 1
			digits +=1
		SN_prefix = SN[:index+1]
		serial_num = string.atoi(SN[index+1:])
		serial_num += int(x)
		self.field["SN"][_VALUE] = SN_prefix + '%0*d'%(digits, serial_num)
		return self.field["SN"][_VALUE]

	def AppendRecord(self,record,table_num=0):
		# record format: Refer_Entry
		if isinstance(record,Record_Entry):
			sefl.Record_Table[table_num].append(record)
		else:
			raise ValueError

	def Save2DB(self):
		#print "before save2db...", self.field
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cmd = "select count(*) from %s where PN like '%s' and SN like '%s'"%(self.table_name,self.field["PN"][_VALUE],self.field["SN"][_VALUE])
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where  PN like '%s' and SN like '%s'"%(self.table_name,self.field["PN"][_VALUE],self.field["SN"][_VALUE])

	def CreateTable(self,db_cursor):
		db_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'"%self.table_name)
		for x in db_cursor:
			if x[0] <=0 :
				SELECT   = "CREATE TABLE %s ("%(self.table_name)
				SELECT += " PN TEXT,"
				SELECT += " SN TEXT,"
				SELECT += " CreateTime TEXT,"
				SELECT += " result TEXT,"
				SELECT += " obj_self BLOB)"
				db_cursor.execute(SELECT)
			else:
				print "table %s existed already."%self.table_name


	def RestoreFromDBZ(self,SN):
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		cmd = "select count(*) from %s where SN like '%s'"%(self.table_name,SN)
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

		obj_x = gZpickle.loads(eut_b[3]) 
		self.field = obj_x.field
		self.Record_Table = obj_x.Record_Table 
		self.result = objx.result
		db_con.close()
		#print "field after restore from DB",self.field

	def Save2DBZ(self):
		#print "before save2db...", self.field
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cmd = "select count(*) from %s where SN like '%s'"%(self.table_name,self.SN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where SN like '%s'" % (self.table_name, self.SN)
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
			break
		print "obj len ......",len(gZpickle.dumps(self))
		record_bz = (self.PN,
				self.SN,
				self.create_time,
				self.result,
				gZpickle.dumps(self)) 
		db_cursor.execute("insert into %s values (?,?,?,?,?)"%(self.table_name),record_bz)
		db_con.commit()
		db_con.close()


	def UpdateTable(self,row,col,window):
		for table in self.Refer_Table:
			table_len = len(table)+10
			print "table length>>>>>>>>>>>>>>",window.GetNumberRows(),table_len
			if window.GetNumberRows() < table_len:
				window.SetNumberRows(table_len)
			if table == self.Refer_Table[0]:
				col_start = col
				i    = 1
			else:
				col_start = col + REF_COL
				i    = 2
			col_ = col_start
			for name in (u"位置/mm",u"位偏移/mm",u"Sensor%d值"%(i),u"精度",u"修正值"):
				window.SetCellValue(row,col_,name)
				window.SetReadOnly(row,col_,True)
				window.SetCellBackgroundColour(row,col_,"Grey")
				col_ +=1
			row_ = row
			for refer_entry in table:
				row_ += 1
				window.SetRowLabelValue(row_,str(row_-row))
				(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
				col_ = col_start
				for value in (Xvalue,Xprecision,Yvalue,Yprecision,Yoffset):
					value_str = str(round(value,6))
					window.SetCellValue(row_,col_,value_str)
					window.SetCellEditor(
						row_,
						col_,
						wx.grid.GridCellFloatEditor())
					col_ += 1

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
		
		values = line.split(',')
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
		



############################################################################################################################################


if __name__=='__main__':
	record = TestRecord(PN="diek",SN="ieik-sab01-02883")

	print record.AdjustSN(5)
	print record.AdjustSN(-1)

	s = pickle.dumps(record)
	r2 = pickle.loads(s)

	print r2.PN,r2.SN,r2.PNversion
