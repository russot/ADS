# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys
import glob
import os 
import string
import time
import const
#from Queue import Queue
#import math
#import re
#import struct 
import config_db
import sqlite3 as sqlite
from refer_entry import Refer_Entry
from eut import Eut
from thermo_sensor import Thermo_Sensor
#from util import gAuthen,gZip,gZpickle 
import util

from thermo import Thermo

#index for refer table RC
REF_ROW = 6
REF_COL = 6

#index for named cells
_VALUE	= int(0)
_RC	= int(1)
_STR	= int(2)

gEut    = Eut()
gThermo = Thermo()
Demo_PT = "pt1000-01"

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
	field_  =  {}
	field_["PN"] =u"料号"
	field_["thermo_PN"] =u"NTC料号"
	field_["total_length"] =u"总长度"
	field_["head_length"] =u"浮子长度"
	field_["signal_num"] =u"信号数量"
	field_["SN"] =u"编号"
	field_["Ver"] =u"版本"
	field_["model"]=u"型号"
	field_["time"] =u"时间"
	field_["tempr"]=u"温度"
	field_["NTCvalue"] =u"NTC实测"
	field_["NTCrefer"] =u"NTC参考"
	field_["NTCresult"]=u"NTC结果"
	field_["result"]   =u"总结果"
	field_["X_unit"]   =u"位置单位"
	field_["Y1_unit"]  =u"信号1单位"
	field_["Y2_unit"]  =u"信号2单位"
	field_["precision"]=u"精度"
	field_["value"]= u"标准值"
	field_["Y_unit"] = u"信号单位"
	def __init__(self,PN='',SN='',Record_Table=[[],[]]):
		create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		self.Record_Table = Record_Table
		self.result = 'Pass'
		self.field = {}
		self.field["PN"] = [PN,(0,0),u"料号"]
		self.field["SN"] = [SN,(0,1),u"编号"]
		self.field["model"]=[None,(0,2),u"型号"]
		self.field["time"]=[create_time,(0,3),u"时间"]
		self.field["tempr"] = [None,(2,0),u"温度"]
		self.field["NTCrefer"] = [None,(2,1),u"NTC参考"]
		self.field["NTCvalue"] = [None,(2,2),u"NTC实测"]
		self.field["NTCresult"] = [None,(2,3),u"NTC判定"]
		self.field["result"] =[None,(2,4),u"总结果"]
		self.field["X_unit"] = ["mm",(REF_ROW-2,0),u"位置单位"]
		self.field["Y1_unit"] =["ohm",(REF_ROW-2,2),u"信号1单位"]
		self.field["Y2_unit"] =["ohm",(REF_ROW-2,REF_COL+2),u"信号2单位"]
		self.SetSN(SN)
		self.SetPN(PN)
		self.table_origin_row = 0
		self.InitRecord()
		gThermo.SetPT(Demo_PT)

#----------------------------------------------------------------------------------------------------
	def GetResult(self):
		return self.field["result"][_VALUE]

#----------------------------------------------------------------------------------------------------
	def SetResultFail(self):
		self.field["result"][_VALUE] = False 
		self.result = True

#----------------------------------------------------------------------------------------------------
	def SetResultPass(self):
		self.field["result"][_VALUE] = True 
		self.result = True

#----------------------------------------------------------------------------------------------------
	def SetResultNG(self):
		self.SetResultFail()

#----------------------------------------------------------------------------------------------------
	def GetPN(self):
		return self.field["PN"][_VALUE] 

#----------------------------------------------------------------------------------------------------
	def GetSN(self):
		return self.field["SN"][_VALUE] 

#----------------------------------------------------------------------------------------------------
	def GetThermo(self):
		return self.field["tempr"][_VALUE] 

#----------------------------------------------------------------------------------------------------
	def GetNTCrefer(self):
		return self.field["NTCrefer"][_VALUE] 

#----------------------------------------------------------------------------------------------------
	def GetNTCvalue(self):
		return self.field["NTCvalue"][_VALUE] 

#----------------------------------------------------------------------------------------------------
	def GetNTCresult(self):
		return self.field["NTCresult"][_VALUE] 

#----------------------------------------------------------------------------------------------------
	def Show(self):
		out=''
		out += self.ShowField()
		out += self.ShowRecord()
		return out

#----------------------------------------------------------------------------------------------------
	def SetThermo(self,value):
		self.field["tempr"][_VALUE] = float(value)

#----------------------------------------------------------------------------------------------------
	def GetRecord(self):
		out=[]
		try:
			for table in self.Record_Table:
				if not table:
					continue
				for record_entry in table:
					record = record_entry.GetRecord()
					out.append(record)
		except:
			pass
		return out

#----------------------------------------------------------------------------------------------------
	def ShowRecord(self):
		out=''
		count = 1
		for table in self.Record_Table:
			if not table:
				continue
			for record_entry in table:
				refer  = record_entry.GetRefer()
				record = record_entry.GetRecord()
				out+="%04d,refer ,%s\n"%(count, refer.ShowSensor())
				out+="%04d,record,%s\n"%(count, record.ShowSensor())
				count += 1
		return out
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
	def SetupThermo(self,hex_NTC,hex_PT):
		(result,temprature,Rntc,Rref) = gThermo.Validate(hex_NTC=hex_NTC,hex_PT=hex_PT)
		self.field["tempr"][_VALUE] = float(temprature)
		self.field["NTCvalue"][_VALUE] = float(Rntc)
		self.field["NTCrefer"][_VALUE]  = float(Rref)
		if result == True:
			self.field["NTCresult"][_VALUE] = True
		else:
			self.field["NTCresult"][_VALUE] = False
		
		return (result,temprature,Rntc,Rref)



	
#----------------------------------------------------------------------------------------------------
	def SetPN(self,PN):
		if not PN:
			return
		print "setup PN"
		gEut.RestoreFromDBZ(PN)
	#		return None
		print "setup PN end...................................................................................................."
		if gEut.HasNTC():#if has thermo_sensor,restore from DB
			gThermo.SetNTC(gEut.field["thermo_PN"][_VALUE])
			self.field["NTCvalue"] =[None,(2,1),u"NTC实测值"]
			self.field["NTCrefer"] =[None,(2,2),u"NTC参考值"]
			self.field["NTCresult"] =[None,(2,3),u"NTC结果"]

		self.field["PN"][_VALUE]   = gEut.field["PN"][_VALUE]
		self.field["model"][_VALUE]   = gEut.field["model"][_VALUE]
		self.field["X_unit"][_VALUE]  = gEut.field["X_unit"][_VALUE]
		self.field["Y1_unit"][_VALUE] = gEut.field["Y1_unit"][_VALUE]
		self.field["Y2_unit"][_VALUE] = gEut.field["Y2_unit"][_VALUE]

#----------------------------------------------------------------------------------------------------
	def SetSN(self,SN):
		if not SN:
			print "warning:invalid SN, SN is set to 'abcd-0000001'!"
			self.field["SN"][_VALUE]='abcd-0000001'
			return
		self.field["SN"][_VALUE]=SN
		print "recod SN is set to ---->>> ",self.field["SN"][_VALUE]

#----------------------------------------------------------------------------------------------------
	def InitRecord(self):
		self.field["NTCvalue"][_VALUE] = None
		self.field["NTCrefer"][_VALUE]  = None
		self.field["NTCresult"][_VALUE]  = None
		self.field["result"][_VALUE]  = None
		self.Record_Table = [[],[]]
		self.InitTable()

	def InitTable(self):
		#self.last_row = self.table_origin_row 
		self.last_index = 0

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
		if isinstance(record,Record_Entry):
			self.Record_Table[table_num].append(record)
		else:
			raise ValueError
	def GetLastRecord(self):
		if self.Record_Table[1] :
			try:
				if self.Record_Table[1][-1]:
					return (self.Record_Table[0][-1],self.Record_Table[1][-1])
			except:
				pass
		else:
			return (self.Record_Table[0][-1],None)

	

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
	def RestoreFromDBZ(self,SN):#search by unique_number of SN 
		print "try to restore",SN
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		cmd = "select count(*) from %s where SN like '%s'"%(self.table_name,SN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] <= 0:
				util.ShowMessage(u"抱歉！此记录不存在!")
				return None
			else:
				break
		cmd = "select * from %s where SN like '%s'" % (self.table_name, SN)
		db_cursor.execute(cmd)
		eut_b = db_cursor.fetchone()
		#print eut_b
		if not eut_b:
			print "Warning:%s not found!\n"%SN
			return None

		obj_x = util.gZpickle.loads(eut_b[4]) 
		self.field = obj_x.field
		self.Record_Table = obj_x.Record_Table 
		self.result = obj_x.result
		db_con.close()
		self.ShowRecord()
		return obj_x
		#print "field after restore from DB",self.field

#----------------------------------------------------------------------------------------------------
	def Save2DBZ(self):
		self.SetupTimeStamp()
		#print "before save2db...", self.field
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		obj_dbz = util.gZpickle.dumps(self)
		print "obj len ......",len(obj_dbz)
		record_bz = (self.field["PN"][_VALUE],
				self.field["SN"][_VALUE],
				self.field["time"][_VALUE],
				self.result,
				obj_dbz ) 
		db_cursor.execute("insert into %s values (?,?,?,?,?)"%(self.table_name),record_bz)
		db_con.commit()
		db_con.close()



#----------------------------------------------------------------------------------------------------
	def UpdateTable(self,row=6,col=0,window=None):
		self.InitTable()
		self.UpdateHeader(row,col,window)
		self.UpdateRecord(col,window,self.Record_Table)

#----------------------------------------------------------------------------------------------------
	def UpdateHeader(self,row=6,col=0,window=None):
		for table in self.Record_Table:
			#window.SetNumberRows(10)
			if table is self.Record_Table[0]:
				col_start = col
				i    = 1
			else:
				col_start = col + REF_COL
				i    = 2
			col_ = col_start
			signal_ref =u"sig.%d ref.\n信号%d标准\n%s"%(i,i,window.GetCellValue(row-1,col_+2))
			signal_real =u"sig.%d real.\n信号%d实测\n%s"%(i,i,window.GetCellValue(row-1,col_+2))
			window.SetRowSize(row,60)
			for width,name in ((50,u"Href\n高度参考\nmm"),(50,u"H\n高度实测\nmm"),(80,signal_ref),(80,signal_real),(120,u"judge@%\n结果@%")):
				window.SetCellValue(row,col_,name)
				window.SetReadOnly(row,col_,True)
				window.SetCellBackgroundColour(row,col_,"Grey")
				window.SetColSize(col_,width)
				col_ += 1
		self.last_row = row + 1
		self.table_origin_row = row + 1
		#print "last row>>>>>>>>>>>>>",self.last_row

#----------------------------------------------------------------------------------------------------
	def UpdateRecord(self,col=0,window=None,tables=[]):
		self.UpdateRecord_v2(col,window,tables)
		#print "test_record update record.................."
#----------------------------------------------------------------------------------------------------
	def UpdateRecord_v1(self,col=0,window=None,tables=[]):
		#print "test_record update record.................."
		for table in tables:
			if not table:
				continue
			row_ = self.last_row
			row  = self.last_row
			if table is tables[0]:
				col_start = col
			else:
				col_start = col + REF_COL
			col_ = col_start
			#print self.last_row
			for record_entry in table:
				if not record_entry:
					continue
				sheet_len =window.GetNumberRows()  
				window.SetNumberRows(sheet_len + 2)
				#print "table length  >>>>>> sheet_len@%d"%(sheet_len+2)
				self.last_index += 1
				#print "row,row_,row_index",row,row_,row_index
				window.SetRowLabelValue(row_,str(self.last_index))
				window.SetRowLabelValue(row_+1,"")
				record		= record_entry.GetRecord()
				refer_entry  	= record_entry.GetRefer()#index is  a tuple of (index_num,table_num)

				(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
				(Xvalue_,Xprecision_,Yvalue_,Yprecision_,Yoffset_,Ymin_,Ymax_)=record.Values()
				Xprecision_,Yprecision_x,xstatus_x,ystatus_x = refer_entry.Validate(Xvalue_,Yvalue_)
				#print record.Values()
				#show refer values
				color = "light gray"
				if record.GetLength() == 100:
					result = ''
					if (Yprecision_ > Yprecision) :
						result = u" 信号超差%.1f"%(Yprecision_*100)
						color = "red"
					else:
						result  = u"Y:PASS"
						color = "green"
					if Xprecision >0 and (Xprecision_ > Xprecision) :
							result += u";H偏差%.1fmm\n"%Xprecision_
							color = "red"
				col_ = col_start
				for value in (Xvalue,Xprecision,Yvalue,Yprecision):
					value_str = str(round(value,6))
					window.SetCellValue(row_,col_,value_str)
					window.SetReadOnly(row_,col_,True)
					col_ += 1
				#show real values
				col_ = col_start
				for value in (Xvalue_,Xprecision_,Yvalue_,Yprecision_):
					value_str = str(round(value,6))
					#print "row, col,str:::::::::",row_+1,col_,value_str
					window.SetCellBackgroundColour(row_+1,col_,color)
					window.SetCellValue(row_+1,col_,value_str)
					window.SetReadOnly(row_+1,col_,True)
					col_ += 1
				window.SetCellBackgroundColour(row_+1,col_,color)
				if record.GetLength() == 100:
					window.SetCellValue(row_+1,col_,result)
				window.SetReadOnly(row_+1,col_,True)
				row_ += 2 # next record_entry

			self.last_row = row_
		#print "last row>>>>>>>>>>>>>",self.last_row
		
#----------------------------------------------------------------------------------------------------
	def UpdateRecord_v2(self,col=0,window=None,tables=[]):
		#print "test_record update record.................."
		for table in tables:
			if not table:
				continue
			row_ = self.last_row
			if table is tables[0]:
				col_start = col
			else:
				col_start = col + REF_COL
			col_ = col_start
			#print self.last_row
			for record_entry in table:
				if not record_entry:
					continue
				record		= record_entry.GetRecord()
				refer_entry  	= record_entry.GetRefer()#index is  a tuple of (index_num,table_num)

				(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
				(Xvalue_,Xprecision_,Yvalue_,Yprecision_,Yoffset_,Ymin_,Ymax_)=record.Values()
				Xprecision_,Yprecision_x,xstatus_x,ystatus_x = refer_entry.Validate(Xvalue_,Yvalue_)
				Xprecision_,Yprecision_x,xstatus_x,ystatus_x = refer_entry.Validate(None,Yvalue_)
				#print record.Values()
				#show refer values
				color = "light gray"
				result = ''
				if record.GetLength() == 100:
					if (Yprecision_ > Yprecision) :
						result = u"信号NG@%.1f"%(Yprecision_*100)
						color = "red"
					else:
						result = u"信号OK@%.1f"%(Yprecision_*100)
						color = "green"
					if Xprecision_ > Xprecision :
						result += u";H偏差%.1fmm\n"%Xprecision_
						color = "red"
					else:
						result += u";H偏差%.1fmm\n"%Xprecision_

				if result == '':
					continue
				sheet_len =window.GetNumberRows()  
				window.SetNumberRows(sheet_len+1)
				self.last_index += 1
				window.SetRowLabelValue(row_,str(self.last_index))
				window.SetRowSize(row_,20)

				#show result 
				col_ = col_start
				for value in (Xvalue,Xvalue_,Yvalue,Yvalue_,result):
					if isinstance(value,float):
						value_str = str(round(value,2))
					else:
						value_str = value
					window.SetCellBackgroundColour(row_,col_,color)
					window.SetCellValue(row_,col_,value_str)
					window.SetReadOnly(row_,col_,True)
					col_ += 1
				row_ += 1 # next record_entry

			self.last_row = row_

#----------------------------------------------------------------------------------------------------
	def QueryDB(self, time_pattern,PN_pattern):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		if time_pattern.find("NG") >= 0:
			time_pattern = time_pattern.strip("NG")
			SELECT = "SELECT PN,SN,time,result FROM %s WHERE time LIKE '%%%s%%' and PN LIKE '%%%s%%' and result LIKE '%%NG%%'" %( 
				self.table_name,time_pattern,PN_pattern)
		elif time_pattern.find("Pass") >= 0:
			time_pattern = time_pattern.strip("Pass")
			SELECT = "SELECT PN,SN,time,result FROM %s WHERE time LIKE '%%%s%%' and PN LIKE '%%%s%%' and result LIKE '%%Pass%%'" %( 
				self.table_name,time_pattern,PN_pattern)
		else:
			SELECT = "SELECT PN,SN,time,result FROM %s WHERE time LIKE '%%%s%%' and PN LIKE '%%%s%%'" %( 
				self.table_name,time_pattern,PN_pattern)

		db_cursor.execute(SELECT)
	
		entries =db_cursor.fetchall()
		db_con.close()
		column_format = (
				(1,u"序号",50),#column_num,view_text,width
				(2,u"PN/\n料号",150),
				(3,u"SN/流水号",100), 
				(4,u"time/时间",100), 
				(5,u"result/结果",50),) 
		return (entries,column_format) # fields of each should be matched



####################################################################################################
####################################################################################################
####################################################################################################
DEMO_PN    = 'R939-5y'
if __name__=='__main__':
	record = Test_Record()
	#gModule = True
	record.SetPN(DEMO_PN)
	record.AdjustSN(5)
	record.AdjustSN(-1)
	print record.ShowField()


