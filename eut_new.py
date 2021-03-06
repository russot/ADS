# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import wx 
import wx.grid 
import wx.lib.sheet 
import re
import time
import config_db
import sqlite3 as sqlite
from util import gAuthen,gZip,gZpickle 
from refer_entry import Refer_Entry
from thermo_sensor import *


#index for named cells
_VALUE	= int(0)
_RC	= int(1)

#index for refer table RC
REF_ROW = 6
REF_COL = 6

class Eut():
	#__slots__ = {'ID':str, 'field': dict, 'Refer_Table': list}
	table_name = config_db.eut_table_name
	db_name = config_db.eut_db
	def __init__(self,model='',PN='',SN='',Refer_Table=[[],[]],thermo_PN=''):
		self.field={}
		self.field[u"料号"] = [PN,(0,0)]
		self.field[u"Ver"] = [SN,(0,1)]
		self.field[u"型号"]=[model,(0,2)]
		self.field[u"NTC料号"] = [thermo_PN,(2,0)]
		#self.field["signal_num"] =[ 2,(2,1)]
		self.field[u"浮子长度"] =[ 32,(2,2)]
		self.field[u"总长度"] =[ 532,(2,3)]
		self.field[u"位置"] = ["mm",(REF_ROW-2,0)]
		self.field[u"信号1单位"] =["ohm",(REF_ROW-2,2)]
		self.field[u"信号2单位"] =["ohm",(REF_ROW-2,REF_COL+2)]
		self.Refer_Table = Refer_Table

	def GetTotalLength(self):
		value =  self.field[u"总长度"][_VALUE]
		return float(value)

	def GetHeadLength(self):
		value =  self.field[u"浮子长度"][_VALUE]
		return float(value)

	def GetXlength(self):
		x0_ = float(self.Refer_Table[0][ 0].GetXvalue())
		xn_ = float(self.Refer_Table[0][-1].GetXvalue())
		xmax = xn_
		if x0_ > xn_:
			xmax = x0_
		return xmax

	def GetXrange(self):
		head_length  = self.GetHeadLength()
		Xlength      = self.GetXlength()
		total_length = self.GetTotalLength()
		XHigh = total_length - Xlength + head_length
		XLow  = total_length 
		return (int(XHigh),int(XLow))

	def GetPN(self):
		return self.field[u"料号"][_VALUE]

	def GetYunit(self):
		return self.field[u"信号1单位"][_VALUE]

	def GetRange(self):
		min_ = self.Refer_Table[0][ 0].GetYvalue()
		max_ = self.Refer_Table[0][-1].GetYvalue()
		return (min_,max_)

	def HasNTC(self):
		if self.field[u"NTC料号"][_VALUE] !='':
			return True
		else:
			return False


	def GetThermoModel(self):
		PN = self.field[u"NTC料号"][_VALUE]
		thermo_sensor = Thermo_Sensor()
		thermo_sensor.RestoreFromDBZ(PN)
		return str(thermo_sensor.field[u"型号"][_VALUE])


	def GetRefer( index=(0,0) ):#parameter is  a tuple of (index,table_num)
		index_num,table_num=index
		return self.Refer_Table[table_num][index_num]

	def SetDefault(self):
		self.field[u"料号"][_VALUE]	= ''
		self.field[u"Ver"][_VALUE]	= ''
		self.field[u"型号"][_VALUE]	= ''
		self.field[u"NTC料号"][_VALUE]	= ''
		#self.field["signal_num"][_VALUE]= ''
		self.field[u"位置"][_VALUE]	= ''
		self.field[u"信号1单位"][_VALUE]	= ''
		self.field[u"信号2单位"][_VALUE]	= ''
		del self.Refer_Table
		self.Refer_Table = [[],[]]

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
		table = []
		table0 =  self.SaveSensorTable(row=REF_ROW,col=0,window=window)
		table1 =  self.SaveSensorTable(row=REF_ROW,col=REF_COL,window=window)
		table.append( table0)
		table.append( table1)
		self.SetReferTable(table)
		#print	self.ShowRefer()

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
				SELECT += " Ver TEXT,"
				SELECT += " model TEXT,"
				SELECT += " obj_self BLOB)"
				db_cursor.execute(SELECT)
			else:
				print "table eut existed already."

	def RestoreFromDBZ(self,PN):
		print "queried PN is ",PN
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		cmd = "select count(*) from %s where PN like '%s'"%(self.table_name,PN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] <= 0:
			#	wx.MessageBox(u"抱歉！此记录不存在!",
			#		style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO)
				return
			else:
				break
		cmd = "select * from %s where PN like '%s'" % (self.table_name, PN)
		db_cursor.execute(cmd)
		eut_b = db_cursor.fetchone()
		#print eut_b

		obj_x = gZpickle.loads(eut_b[3]) 
		self.field = obj_x.field
		self.Refer_Table = obj_x.Refer_Table 
		for table in self.Refer_Table:
			if not table:
				continue
			table.sort(key=lambda x:x.GetYvalue())
		db_con.close()
		try:
			print "X range:",self.GetXrange()
		except:
			pass
		#print "field after restore from DB",self.field

	def Save2DBZ(self):
		#print "before save2db...", self.field
		db_con = sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor = db_con.cursor()
		self.CreateTable(db_cursor)
		cretia = self.field[u"料号"][_VALUE]
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
		obj_self = gZpickle.dumps(self)
		print "obj len ......%d"%(len(obj_self))
		#eut_bz = (self.field[[u"料号"][_VALUE], self.field[u"Ver"][_VALUE], self.field[u"型号"][_VALUE], obj_self )
		#db_cursor.execute("insert into %s values (?,?,?,?)"%(self.table_name),eut_bz)
		db_con.commit()
		db_con.close()

	def UpdateTable(self,row,col,window):
		for table in self.Refer_Table:
			table_len = len(table)+10
			if window.GetNumberRows() < table_len:
				window.SetNumberRows(table_len)
				print "table length %d >>>>>> %d"%(window.GetNumberRows(),table_len)
			if table is self.Refer_Table[0]:
				col_start = col
				i    = 1
			else:
				col_start = col + REF_COL
				i    = 2
			col_ = col_start
			for name in (u"位置/mm",u"位偏移/mm",u"信号%d值"%(i),u"精度",u"修正值"):
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
		try:
			refer_entry2 = Refer_Entry(
					Xvalue		=values[5],
					Xprecision	=values[6],
					Yvalue		=values[7],
					Yprecision	=values[8],
					Yoffset		=values[9])
			self.AppendReferTable(1,refer_entry2)
		except Exception,e:
			print e
			pass

	def Import(self):
		dlg = wx.FileDialog(None,u"选择csv文件",wildcard="*.csv")
		if dlg.ShowModal() != wx.ID_OK:
			return
		eut_name = dlg.GetPath()
		if not eut_name:
			return 
		reader =file(eut_name,"r")
		reader.readline()#跳过第一行注释行
		type_ = reader.readline()
		if not type_.startswith("type,sensor"):
			wx.MessageDialog(None,u"导入文件中的type行值错误，必须是'type,sensor'",u"警告",wx.YES_DEFAULT).ShowModal()
			return 
		print "import now...................."
		time_start = time.time()
		lines =  reader.readlines()
		for line in lines[0:15]:
			if line.startswith('###'):#表格起始标志
				break
			try:
				self.SetField(line)
			except:
				pass
		#
		del self.Refer_Table
		self.Refer_Table = [[],[]]
		start = False
		for line in lines:
			if start == True:
				self.SetRefer(line)
			if line.startswith('###'):
				start = True
		for table in self.Refer_Table:
			table.sort(key=lambda x:x.GetYvalue())
		print "import end in %ds...................."%(time.time()-time_start)
		#print self.ShowRefer()
	
	def SetReferTable(self,Refer_Table):
		self.Refer_Table = Refer_Table
		for table in self.Refer_Table:
			if not table:
				continue
			table.sort(key=lambda x:x.GetYvalue())

	def GetReferTable(self):
		return self.Refer_Table 

	def SetThermoSensor(self,thermo_sensor):
		self.thermo_sensor= thermo_sensor

	def GetThermoSensor(self):
		return self.thermo_sensor

	def GetMaxY(self,table_num=0):
		return self.Refer_Table[table_num][-1].GetYvalue()


	def AppendReferTable(self,table_num,refer_entry):
		if not isinstance(refer_entry,Refer_Entry):
			return -1
		try:
			self.Refer_Table[table_num].append(refer_entry)
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
			out = ''
			for table in self.Refer_Table:
				for refer_entry in table:
					out += refer_entry.ShowSensor() + '\n'
		except:
			pass
		return out


	def GetReferEntry_X(self,Xvalue=None,Yvalue=None,table_num=0):
		refer_entry =None
		x0 = self.Refer_Table[table_num][0].GetXvalue()
		xn = self.Refer_Table[table_num][-1].GetXvalue()
		if x0 > xn:
			Xmax =self.Refer_Table[table_num][0]
			Xmin =self.Refer_Table[table_num][-1]
		else:
			Xmax =self.Refer_Table[table_num][-1]
			Xmin =self.Refer_Table[table_num][0]
		print "Xmin,Xmax,X--------------------",Xmin.GetXvalue(),Xmax.GetXvalue(),Xvalue

		if Xvalue >= Xmax.GetXvalue():
			refer_entry = Xmax
		elif Xvalue <= Xmin.GetXvalue():
			refer_entry = Xmin
		else:
			p0 = self.Refer_Table[table_num][0]
			for p1 in self.Refer_Table[table_num]:
				x0_ = p0.GetXvalue()
				x1 = p1.GetXvalue()
				delta0 = abs(Xvalue - x0_)
				delta1 = abs(Xvalue - x1)
				#judge being within by comparing delta_sum 
				if (delta0 + delta1) > abs(x1 - x0_):
					p0 = p1
					continue
				if Yvalue != None:
					y0 = p0.GetYvalue()
					y1 = p1.GetYvalue()
					delta0 = Yvalue - y0
					delta1 = Yvalue - y1
					#use nearby Yvalue
					if abs(delta0) < abs(delta1): 
						refer_entry =  p0
					else:
						refer_entry =  p1
				else:
					if x0 > xn:
						refer_entry =  p1
					else:
						refer_entry =  p0


					break

		return refer_entry


	def GetReferEntry_Y(self,Xvalue=None,Yvalue=None,table_num=0):
		refer_entry =None
		if Yvalue <= self.Refer_Table[table_num][0].GetYvalue():#outof range
				refer_entry =  self.Refer_Table[table_num][0]
		elif Yvalue >= self.Refer_Table[table_num][-1].GetYvalue():#outof range
				refer_entry =  self.Refer_Table[table_num][-1]
		else:
			p0 = self.Refer_Table[table_num][0]
			for p1 in self.Refer_Table[table_num]:
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
					refer_entry =  p0
					p0.SetValidStatus(True)
				else:
					refer_entry =  p1
					p1.SetValidStatus(True)
				break
		return refer_entry

	def GetReferEntry(self,Xvalue=None,Yvalue=None,table_num=0):
		'''Xvalue should be None for using Yvalue as index,
		or integer for using itself as index '''
		refer_entry =None
		if Xvalue != None:# use Xvalue as index
			refer_entry = self.GetReferEntry_X(Xvalue,Yvalue,table_num)
		else:# use Yvalue as index, and table is sorted by Yvalue
			refer_entry = self.GetReferEntry_Y(Xvalue,Yvalue,table_num)
		return refer_entry # if not found, return None object

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
				(2,u"型号",180),
				(3,u"料号",120),) 
		return (entries,column_format) # fields of each should be matched


############################################################################################################################################


if __name__=='__main__':

	print "not tested yet......"
