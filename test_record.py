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
		self.SetSN(SN)
		self.PN = PN
		self.PNversion = '1.0'
		self.Record_Table = Record_Table

	def SetSN(self,SN):
		if not SN or not isinstance(SN,str):
			print "Warning:invalid SN, SN is set to 'ABCD-0000001'!"
			self.SN='ABCD-0000001'
			return
		self.SN=SN

	def AdjustSN(self,x):
		index = -1
		digits =  0
		while  self.SN[index:].isdigit():
			index -= 1
			digits +=1
		SN_prefix = self.SN[:index+1]
		serial_num = string.atoi(self.SN[index+1:])
		serial_num += int(x)
		self.SN = SN_prefix + '%0*d'%(digits, serial_num)
		return self.SN

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
		cmd = "select count(*) from %s where PN like '%s' and SN like '%s'"%(self.table_name,self.PN,self.SN)
		db_cursor.execute(cmd)
		for existed in db_cursor:
			if existed[0] > 0:
				if wx.NO == wx.MessageBox(u"注意！此记录已存在\n 确认要更新？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
				else:
					cmd = "delete from %s where  PN like '%s' and SN like '%s'"%(self.table_name,self.PN,self.SN)
					db_cursor.execute(cmd)
					db_con.commit()
			else:
				if  wx.NO == wx.MessageBox(u"确认要保存？",
						style=wx.CENTER|wx.ICON_QUESTION|wx.YES_NO):
					return
			break
		record_b = (self.PN,
				self.PNversion,
				self.SN,
				self.RTable2Blob(self.Record_Table[0]),
				self.RTable2Blob(self.Record_Table[1]))
		db_cursor.execute("insert into %s values (?,?,?,?,?,?,?,?,?,?)"%self.table_name,eut_b)
		db_con.commit()
		db_con.close()



	def RTable2Blob(self,table):
		if not table:
			return ''
		bytes_block = ''
		for refer_entry in table:
			bytes_block += struct.pack('5f',
					refer_entry.GetXvalue(),
					refer_entry.GetXprecision(),
					refer_entry.GetYvalue(),
					refer_entry.GetYprecision(),
					refer_entry.GetYoffset())	
		return bytes_block




############################################################################################################################################


if __name__=='__main__':
	record = TestRecord(PN="diek",SN="ieik-sab01-02883")

	print record.AdjustSN(5)
	print record.AdjustSN(-1)

