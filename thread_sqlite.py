# -*- coding: utf-8 -*-
#!python
"""sqlite module for persist session and data.""" 
import sys 
import wx 
import os 
import string 
import threading 
from Queue import Queue
import sqlite3 as sqlite
import config_db
import struct 
import time


############################################################################################################################################
class Thread_Sqlite(threading.Thread):
	def __init__(self,db_name=config_db.Connection_db,queue_in=None,queue_out=None):
		threading.Thread.__init__(self)
		self.db_name   = db_name
		self.queue_in   = queue_in
		self.queue_out = queue_out
		self.CreateTable()
		
	def CreateTable(self):
		self.db_con   =sqlite.connect(self.db_name)
		self.db_cursor=self.db_con.cursor()
		self.db_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s'"%config_db.data_table_name)
		for x in self.db_cursor:
			if x[0] < 1:
				SELECT   = "CREATE TABLE %s ("%(config_db.data_table_name)
				SELECT += " eut_name TEXT,"
				SELECT += " eut_serial TEXT,"
				SELECT += " data_valid BOOL,"
				SELECT += " create_time TimeStamp NOT NULL DEFAULT(datetime('now','localtime')),"
				SELECT += " data_points BLOB)"
				self.db_cursor.execute(SELECT)
				self.db_con.commit()
			else:
				print "table data existed already."
		#~ sys.stdout = self
		
	def write(self,TE):
		pass

	def run(self):#运行一个线程
		self.db_con   =sqlite.connect(self.db_name)
		self.db_con.text_factory = str #解决8bit string 问题
		self.db_cursor=self.db_con.cursor()
		while True:
			self.Cmd_line(timeout=0.01)

	def Cmd_line(self,timeout=0):
		
		target,cmd=(self.queue_in.get() )#get command (from self.queue_in), then process it and response(to  self.queue_out)
		if target.startswith("session:"): #excute
			result = self.SessionPersist(cmd)#处理并返回结果(通过queue_out)
		elif target.startswith("data:"):# 
			result = self.DataPersist(cmd)#处理并返回结果(通过queue_out)
		else:
			result = "Warning: request an  unknown target. \n\t Should be 'session:' or 'data:'"
		self.queue_out.put(result)
			
	def SessionPersist(self,session4persist):
		return None


	def DataPersist(self,data4persist):
		cmd, data= (data4persist[0], data4persist[1])
		#~ s = struct.Struct("fff")
		if cmd.startswith("save:"):
			
			#~ str = s.pack(*data[2])
			#~ print s.unpack(str)
			#~ str=struct.pack("fff", data[2][0],data[2][1],data[2][2] )
			SELECT   = "INSERT INTO data(eut_name,eut_serial,data_valid,data_points) VALUES(?,?,?,?)"
			self.db_cursor.execute(SELECT, data )
			self.db_con.commit()
			return None
			#~ return "saved ok:\t%s/%s\n"%(data[0], data[1])
		if cmd.startswith("query:"):
			#~ print "start query...\n"
			#~ SELECT   = "SELECT * FROM data  WHERE eut_name LIKE 'nokiaa%' "
			SELECT   = "SELECT %s FROM data WHERE %s"%(data[0], data[1])
			#~ print SELECT
			self.db_cursor.execute(SELECT)
			result=self.db_cursor.fetchall()
			
			#~ for row in qself.db_cursor:
				#~ result.append(row)
				
			return result
			#~ return self.db_cursor.fetchall()

def ShowDataPoints(data_points):
	print "位置\t数值\t参考值\t参考精度\t实际精度\t结果"
	for curent_data in data_points:
		valid = curent_data[0]
		pos   = curent_data[1]
		value= curent_data[2]
		value_refer= curent_data[3]
		precision_refer= curent_data[4]
		precision= curent_data[5]

		print "%d\t%5.2f\t%5.2f\t%5.4f\t%5.4f\t"%(pos, value,value_refer, precision_refer, precision),valid


if __name__=='__main__':
	queue_in_ = Queue(-1)
	queue_out_= Queue(-1)
	#~ cmd = ("data:", ("save:",("nokiaa-3310","cd0-90de-89818738",struct.pack("fff",1.1,2.2,3.67))  ) )
	#~ queue_in_.put(cmd )
	#~ cmd_ = ("data:", ("query:",("*","1=1")) )
	#~ queue_in_.put(  cmd_  )
	app = Thread_Sqlite(db_name="sqlite3_all.db",queue_in=queue_in_, queue_out=queue_out_) 
	app.setDaemon(True)
	app.start()
	cmd_ =("data:", ("query:",("*","1=1")) )
	queue_in_.put(cmd_)
	result = queue_out_.get()
	try:
		for row in result:
			#~ print row 
			name,serial,time,data_pack = row
			data_points = []
			data_size = struct.calcsize('I5f')
			offset = 0
			while 1:
				try:
					data = struct.unpack_from('I5f',data_pack, offset)
					#~ print data
					data_points.append(data)
					offset += data_size
				except:
					break
			print name,'\t',serial,'\t',time, '\t','data as below'
			ShowDataPoints(data_points)
	except:
		pass

