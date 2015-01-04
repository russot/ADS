# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import os 
import wx 
import wx.grid 
import wx.lib.sheet 
from socket import *
import math
import re
from thread_sqlite import Thread_Sql
import config_db
import sqlite3 as sqlite
from util import gAuthen,gZip,gZpickle 
from refer_entry import Refer_Entry







#index for named cells
_VALUE	= int(0)
_RC	= int(1)

#index for refer table RC
REF_ROW = 6
REF_COL = 6



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
	def GetPrecision(self):
		return self.field["precision"][_VALUE]

	def SetDefault(self):
		self.field["PN"][_VALUE] 	= ''
		self.field["model"][_VALUE]	= ''
		self.field["value"][_VALUE]	= 0  
		self.field["precision"][_VALUE]	= 0
		self.field["X_unit"][_VALUE]	= u'\xb0C'
		self.field["Y_unit"][_VALUE]	= u'ohm'
		self.Refer_Table = []

	def SetReferTable(self,table):
		self.Refer_Table = table
		self.Refer_Table.sort(key=lambda x:x.GetYvalue())
		print	self.ShowRefer()

	def Save(self,window):	
		self.SaveField(window)
		self.SaveRefer(window)
		self.Save2DBZ()

	def SaveField(self,window):
		#print "before save field ...",field
		for (name,value) in self.field.items():
			row,col = value[_RC]
			row +=1
			self.field[name][_VALUE]= window.GetCellValue(row,col)
		#print "after save field ...",field

	def SaveRefer(self,window):
		self.SetReferTable(self.SaveTable(row=REF_ROW,col=0,window=window))

	def SaveTable(self,row,col,window):
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
						Ymax = Ymax))


		return table

	def CreateTable(self,db_cursor):
		db_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'"%self.table_name)
		for x in db_cursor:
			if x[0] <=0 :
				#SELECT   = "CREATE TABLE %s ("%(self.table_name)
				#SELECT += " PN TEXT,"
				#SELECT += " model TEXT,"
				#SELECT += " value FLOAT,"
				#SELECT += " precision FLOAT,"
				#SELECT += " X_unit TEXT,"
				#SELECT += " Y_unit TEXT,"
				##SELECT += " create_time TimeStamp NOT NULL DEFAULT(datetime('now','localtime')),"
				#SELECT += " Refer_Table BLOB)"
				#db_cursor.execute(SELECT)
				#self.db_con.commit()
				SELECT   = "CREATE TABLE %s ("%(self.table_name)
				SELECT += " PN TEXT,"
				SELECT += " model TEXT,"
				SELECT += " obj_self BLOB)"
				db_cursor.execute(SELECT)
			else:
				print "table thermo existed already."

	def RestoreFromDBZ(self,PN):
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,PN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] <= 0:
				if gModule:
					wx.MessageBox(u"抱歉！此记录不存在!",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
				else:
					print u"抱歉！此记录不存在!"
				return False
			else:
				break
		cmd = "select * from %s where PN like '%s'" % (self.table_name, PN)
		db_cursor.execute(cmd)
		eut_b = db_cursor.fetchone()

		obj_x = gZpickle.loads(eut_b[2]) 
		self.field = obj_x.field
		self.Refer_Table = obj_x.Refer_Table 
		db_con.close()
		return True


	def Save2DBZ(self):
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,self.field["PN"][_VALUE])
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return None
				else:
					cmd = "delete from %s where PN like '%s'" % (self.table_name, self.field["PN"][_VALUE])
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return None
			break
		print "obj len ......",len(gZpickle.dumps(self))
		eut_bz = (self.field["PN"][_VALUE],
				self.field["model"][_VALUE],
				gZpickle.dumps(self)) 
		db_cursor.execute("insert into %s values (?,?,?)"%(self.table_name),eut_bz)
		db_con.commit()
		db_con.close()
		return True


	def UpdateTable(self,row,col,window):
		table_len = len(self.Refer_Table)+10
		if window.GetNumberRows() < table_len:
			window.SetNumberRows(table_len)
			print "table length %d >>>>>> %d"%(window.GetNumberRows(),table_len)
		col_ = col
		for name in (u"温度/ \xb0C",u"最小值/ohm",u"中间值/ohm",u"最大值/ohm"):
			window.SetCellValue(row,col_,name)
			window.SetReadOnly(row,col_,True)
			window.SetCellBackgroundColour(row,col_,"Grey")
			col_ +=1
		row_ = row
		for refer_entry in self.Refer_Table:
			row_ += 1
			window.SetRowLabelValue(row_,str(row_-row))
			(Xvalue,Xprecision,Yvalue,Yprecision,Yoffset,Ymin,Ymax)=refer_entry.Values()
			col_ = col
			for value in (Xvalue,Ymin,Yvalue,Ymax):
				value_str = str(round(value,6))
				window.SetCellValue(row_,col_,value_str)
				window.SetCellEditor(
					row_,
					col_,
					wx.grid.GridCellFloatEditor())
				col_ += 1


	def ShowRefer(self):
		try:
			out = ''
			for refer_entry in self.Refer_Table:
				out += refer_entry.ShowThermo()
		except:
			pass
		return out

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
		print values
		if len(values) >=3 :
			entry =  Refer_Entry( Xvalue=values[0],
					Ymin = values[1],
					Yvalue=values[2],
					Ymax= values[3])
		else:
			entry =  Refer_Entry( Xvalue=values[0],
					Yvalue=values[1])
		self.Refer_Table.append(entry)
	
	#used for PT100/1000 and NTC thermo_resistor
	def Import(self):
		dlg = wx.FileDialog(None,u"选择csv文件",wildcard="*.csv")
		if dlg.ShowModal() != wx.ID_OK:
			return
		file_name = dlg.GetPath()
		if not file_name:
			return 
		self.ImportFrom(file_name)

	def ImportFrom(self,file_name):
		reader =file(file_name,"r")
		reader.readline()#跳过第一行注释行
		type_ = reader.readline()
		if not type_.startswith("type,NTC"):
			err_msg =u"导入文件中的type行值错误，必须是'type,NTC'" 
			if not gModule:
				wx.MessageDialog(None,err_msg,u"警告",wx.YES_DEFAULT).ShowModal()
			else:
				print err_msg
			return 
		print "import now"
		lines =  reader.readlines()
		for line in lines[0:15]:
			if line.startswith('###'):#表格起始标志
				break
			try:
				self.SetField(line)
			except Exception,e:
				print "set field exception:",e
				pass

		#clear table and append new values by SetRefer(line)
		start = False
		self.Refer_Table = []
		for line in lines:
			if start == True:
				try:
					self.SetRefer(line)
				except Exception,e:
					print "set refer exception:",e
					pass
			if line.startswith('###'):
				start = True
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
			r0 = x0.GetYvalue()
			r1 = x1.GetYvalue()
			delta0 = abs(Rvalue-r0)
			delta1 = abs(Rvalue-r1)
			#judge being within by comparing delta_sum 
			if (delta0+delta1) > abs(r1-r0):
				x0 = x1
				continue
			#found and compute linearly
			t0 =  x0.GetXvalue()
			t1 =  x1.GetXvalue()
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
			t0 = x0.GetXvalue()
			t1 = x1.GetXvalue()
			delta0 = abs(Tvalue-t0)
			delta1 = abs(Tvalue-t1)
			#judge being within by comparing delta_sum 
			if (delta0+delta1) > abs(t1-t0):
				x0 = x1
				continue
			#found and compute linearly
			r0 =  x0.GetYvalue()
			r1 =  x1.GetYvalue()
			delta_R = r1 - r0
			delta_T = t1 - t0
			k = delta_R/delta_T
			delta_t =  Tvalue - t0
			rx= r0 + k*delta_t
			print "r0=",r0,"  r1=",r1,"  k=",k,"  delta_t=",delta_t,"  rx=",rx
			break
		return rx
			

	def QueryDB(self, model_pattern,PN_pattern):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		
		SELECT = "SELECT model,PN FROM %s WHERE model LIKE '%%%s%%' and PN LIKE '%%%s%%'" %( 
			self.table_name,model_pattern,PN_pattern)
		db_cursor.execute(SELECT)
	
		entries =db_cursor.fetchall()
		db_con.close()
		column_format = (
				(1,u"序号",50),#column_num,view_text,width
				(2,u"Model/温度传感器型号",180),
				(3,u"PN/料号",120),) 
		return (entries,column_format) # fields of each should be matched	
############################################################################################################################################

gModule = False
if __name__=='__main__':
	#app = wx.App()
	gModule = True
	thermo_demo = Thermo_Sensor()
	thermo_demo.ImportFrom("j2000.csv")
	for key,value in thermo_demo.field.items():
		print key,"=",value
	for x in thermo_demo.Refer_Table:
		print x.ShowThermo()
#	thermo_demo.Save2DBZ()
# 	wx.MessageBox(u" 确认退出",
#		style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
	PN = thermo_demo.field["PN"][_VALUE]
	thermo_demo.RestoreFromDBZ(PN)
	for key,value in thermo_demo.field.items():
		print key,"=",value
	for x in thermo_demo.Refer_Table:
		print x.ShowThermo()
 	#wx.MessageBox(u" 确认退出",
		#style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
	tempr = 40.5
	tempR = thermo_demo.GetR(tempr)
	print ">>>temprature %5f and R is %5f"%(tempr,thermo_demo.GetR(tempr))
	print "<<<temprature %5f and R is %5f"%(thermo_demo.GetT(tempR),tempR)
	tempr = 20.5
	tempR = thermo_demo.GetR(tempr)
	print ">>>temprature %5f and R is %5f"%(tempr,thermo_demo.GetR(tempr))
	print "<<<temprature %5f and R is %5f"%(thermo_demo.GetT(tempR),tempR)
	tempr = 25
	tempR = thermo_demo.GetR(tempr)
	print ">>>temprature %5f and R is %5f"%(tempr,thermo_demo.GetR(tempr))
	print "<<<temprature %5f and R is %5f"%(thermo_demo.GetT(tempR),tempR)

