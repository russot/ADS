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
from refer_entry import Refer_Entry
import pickle
from eut import Eut
from thermo_sensor import Thermo_Sensor
from util import gAuthen,gZip,gZpickle 

#index for refer table RC
REF_ROW = 6
REF_COL = 6

#index for named cells
_VALUE	= int(0)
_RC	= int(1)

gEut    = Eut()
gThermo = Thermo_Sensor()

gModule = False
####################################################################################################
class Record_Entry():
	def __init__(self,refer=None,record=None):
		self.refer  = refer
		self.record = record

	def GetRefer(self):
		return self.refer

	def SetRefer(self,refer):
		if isinstance(refer,Refer_Entry):
			self.refer  = refer
		else:
			raise ValueError

	def GetRecord(self):
		return self.record

	def SetRecord(self,record):
		if isinstance(record,Refer_Entry):
			self.record = record
		else:
			raise ValueError

####################################################################################################
class Test_Record():
	#__slots__ = {'ID':str, 'field': dict, 'Refer_Table': list}
	table_name = config_db.eut_record_TBname
	db_name = config_db.eut_db
	def __init__(self,PN='',SN='',Record_Table=[[],[]]):
		create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		self.Record_Table = Record_Table
		self.result = 'pass'
		self.field = {}
		self.field["PN"] = [PN,(0,0)]
		self.field["SN"] = [SN,(0,1)]
		self.field["model"]=['',(0,2)]
		self.field["time"]=[create_time,(0,3)]
		self.field["tempr"] = ['',(2,0)]
		self.field["NTCvalue"] =['',(2,1)]
		self.field["NTCrefer"] =['',(2,2)]
		self.field["NTCresult"] =['',(2,3)]
		self.field["X_unit"] = ["mm",(REF_ROW-2,0)]
		self.field["Y1_unit"] =["ohm",(REF_ROW-2,2)]
		self.field["Y2_unit"] =["ohm",(REF_ROW-2,REF_COL+2)]
		self.SetSN(SN)
		self.SetPN(PN)

#----------------------------------------------------------------------------------------------------
	def ShowField(self):
		out=''
		for key,value in self.field.items():
			out+="%s:%s\n"%(key,str(value[_VALUE]))
		return out

#----------------------------------------------------------------------------------------------------
	def SetupTimeStamp(self):
		create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		self.field["time"][_VALUE] = create_time

#----------------------------------------------------------------------------------------------------
	def SetupThermo(self,temprature,NTCvalue):
		self.field["tempr"][_VALUE] = float(temprature)
		self.field["NTCvalue"][_VALUE] = float(NTCvalue)
		refer_VALUE = gThermo.GetR(float(temprature))
		self.field["NTCrefer"][_VALUE]  = float(refer_VALUE)
		refer_precision = gThermo.GetPrecision()
		real_precision  = abs(float(NTCvalue) - refer_VALUE)/refer_VALUE
		if real_precision > refer_precision: 
			self.field["NTCresult"][_VALUE] = "Fail"
		else : 
			self.field["NTCresult"][_VALUE] = "Pass"


	
#----------------------------------------------------------------------------------------------------
	def SetPN(self,PN):
		print "setup PN"
		gEut.RestoreFromDBZ(PN)
	#		return None
		print "setup PN end...................................................................................................."
	#	if gEut.field["thermo_PN"]:#if has thermo_sensor,restore from DB
	#		gThermo.RestoreFromDBZ( gEut.field["thermo_PN"])

		self.field["PN"][_VALUE]   = gEut.field["PN"][_VALUE]
		self.field["model"][_VALUE]   = gEut.field["model"][_VALUE]
		self.field["X_unit"][_VALUE]  = gEut.field["X_unit"][_VALUE]
		self.field["Y1_unit"][_VALUE] = gEut.field["Y1_unit"][_VALUE]
		self.field["Y2_unit"][_VALUE] = gEut.field["Y2_unit"][_VALUE]

#----------------------------------------------------------------------------------------------------
	def SetSN(self,SN):
		if not SN or not isinstance(SN,str):
			print "warning:invalid SN, SN is set to 'abcd-0000001'!"
			self.field["SN"][_VALUE]='abcd-0000001'
			return
		self.field["SN"][_VALUE]=SN

#----------------------------------------------------------------------------------------------------
	def SetDefault(self):
		self.Record_Table = [[],[]]

#----------------------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------------------
	def AppendRecord(self,record,table_num=0):
		# record format: Refer_Entry
		if isinstance(record,Record_Entry):
			self.Record_Table[table_num].append(record)
		else:
			raise ValueError


#----------------------------------------------------------------------------------------------------
	def CreateTable(self,db_cursor):
		db_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'"%self.table_name)
		for x in db_cursor:
			if x[0] <=0 :
				SELECT   = "CREATE TABLE %s ("%(self.table_name)
				SELECT += " PN TEXT,"
				SELECT += " SN TEXT,"
				SELECT += " time TEXT,"
				SELECT += " result TEXT,"
				SELECT += " obj_self BLOB)"
				db_cursor.execute(SELECT)
			else:
				print "table %s existed already."%self.table_name


#----------------------------------------------------------------------------------------------------
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
				return None
			else:
				break
		cmd = "select * from %s where PN like '%s'" % (self.table_name, SN)
		db_cursor.execute(cmd)
		eut_b = db_cursor.fetchone()
		#print eut_b

		obj_x = gZpickle.loads(eut_b[3]) 
		self.field = obj_x.field
		self.Record_Table = obj_x.Record_Table 
		self.result = objx.result
		db_con.close()
		return obj_x
		#print "field after restore from DB",self.field

#----------------------------------------------------------------------------------------------------
	def Save2DBZ(self):
		#print "before save2db...", self.field
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cmd = "select count(*) from %s where SN like '%s'"%(self.table_name,self.field["SN"][_VALUE])
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where SN like '%s'" % (self.table_name, self.field["SN"][_VALUE])
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
			break
		print "obj len ......",len(gZpickle.dumps(self))
		record_bz = (self.field["PN"][_VALUE],
				self.field["SN"][_VALUE],
				self.field["time"][_VALUE],
				self.result,
				gZpickle.dumps(self)) 
		db_cursor.execute("insert into %s values (?,?,?,?,?)"%(self.table_name),record_bz)
		db_con.commit()
		db_con.close()



#----------------------------------------------------------------------------------------------------
	def UpdateTable(self,row,col,window):
		if not  self.field["PN"][_VALUE]:
			print "Error:invlid PN!"
			return 
		eut = Eut()
		eut.RestoreFromDBZ(self.field["PN"][_VALUE])
		
		if eut.field["thermo_PN"]:#if has thermo_sensor,restore from DB
			thermo_sensor = Thermo_Sensor()
			thermo_sensor.RestoreFromDBZ( eut.field["thermo_PN"])

		for table in self.Record_Table:
			table_len = len(table)*2+10
			if window.GetNumberRows() < table_len:
				window.SetNumberRows(table_len)
				print "table length %d >>>>>> %d"%(window.GetNumberRows(),table_len)
			if table is self.Record_Table[0]:
				col_start = col
				i    = 1
			else:
				col_start = col + REF_COL
				i    = 2
			col_ = col_start
			for name in (u"位置/mm",u"位偏移/mm",u"Sensor%d值"%(i),u"精度",u"结果"):
				window.SetCellValue(row,col_,name)
				window.SetReadOnly(row,col_,True)
				window.SetCellBackgroundColour(row,col_,"Grey")
				col_ += 1
			row_ = row-1
			for record_entry in table:
				row_ += 2
				window.SetRowLabelValue(row_,str(row_-row))
				record = record_entry.GetRecord()
				index  = record_entry.GetReferIndex()#index is  a tuple of (index_num,table_num)
				refer_entry  = eut.GetRefer(index)

				(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
				(Xvalue_,Xprecision_,Yvalue_,Yprecision_,Yoffset_,Ymin_,Ymax_)=record.Values()
				#show refer values
				col_ = col_start
				for value in (Xvalue,Xprecision,Yvalue,Yprecision):
					value_str = str(round(value,6))
					window.SetCellValue(row_,col_,value_str)
					window.SetReadOnly(row,col_,True)
					col_ += 1
				#show real values
				col_ = col_start
				for value in (Xvalue_,Xprecision_,Yvalue_,Yprecision_):
					value_str = str(round(value,6))
					window.SetCellValue(row_+1,col_,value_str)
					window.SetReadOnly(row_+1,col_,True)
					col_ += 1
				result = ''
				if (Xprecision_ > Xprecision) :
					result += u"X轴(位移)超差\n"
				if (Xprecision_ > Xprecision) :
					result += u"Y轴(测量值)超差"
				if not result:
					result  = u"PASS"
					color = "red"
				else:
					color = "green"
				window.SetCellBackgroundColour(row,col_,color)
				window.SetCellValue(row_+1,col_,result)
				window.SetReadOnly(row_+1,col_,True)
#----------------------------------------------------------------------------------------------------
	def QueryDB(self, time_pattern,PN_pattern):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		
		SELECT = "SELECT PN,SN,time FROM %s WHERE time LIKE '%%%s%%' and PN LIKE '%%%s%%'" %( 
			self.table_name,time_pattern,PN_pattern)
		db_cursor.execute(SELECT)
	
		entries =db_cursor.fetchall()
		db_con.close()
		column_format = (
				(1,u"序号",50),#column_num,view_text,width
				(2,u"PN/\n料号",180),
				(3,u"SN/流水号",120), 
				(4,u"time/时间",120),) 
		return (entries,column_format) # fields of each should be matched



####################################################################################################
####################################################################################################
####################################################################################################
DEMO_PN    = 'R939-5y'
if __name__=='__main__':
	app = wx.App()
	record = Test_Record()
	#gModule = True
	record.SetPN(DEMO_PN)
	record.AdjustSN(5)
	record.AdjustSN(-1)
	print record.ShowField()


