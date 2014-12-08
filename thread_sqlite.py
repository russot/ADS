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
	def __init__(self,db_name=config_db.data_db,queue_in=None,queue_out=None):
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
		

	def run(self):#运行一个线程
		self.db_con   =sqlite.connect(self.db_name)
		self.db_con.text_factory = str #解决8bit string 问题
		self.db_cursor=self.db_con.cursor()
		while True:
			self.Cmd_line(timeout=0.01)
			time.sleep(0.001)

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

eut_sql  =	{"fields":" eut_model TEXT, eut_PN TEXT, eut_range TEXT, data_points BLOB",
		"query":"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='eut'",
		"save":"INSERT INTO eut(eut_model,eut_PN,eut_range,data_points) VALUES(?,?,?,?)",}

data_sql = 	{"fields":" eut_name TEXT, eut_serial TEXT,data_valid BOOL,  create_time TimeStamp NOT NULL DEFAULT(datetime('now','localtime')), data_points BLOB",
		"query":"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='eut'",
		"save":"INSERT INTO eut(eut_model,eut_PN,eut_range,data_points) VALUES(?,?,?,?)",}




############################################################################################################################################
class Thread_Sql(threading.Thread):
	eut_sql  ={"fields":"model TEXT,PN TEXT,NTC FLOAT,NTC_precision FLOAT,unit TEXT, range TEXT, refer_points BLOB",
		"query_table":"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='eut'",
		"save":"INSERT INTO eut VALUES (?,?,?,?,?,?,?)"}

	data_sql ={"fields":" eut_name TEXT, eut_serial TEXT, data_valid BOOL, create_time TimeStamp NOT NULL DEFAULT(datetime('now','localtime')), data_points BLOB",
		"query_table":"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='data'",
		"save":"INSERT INTO data(eut_name,eut_serial,data_valid,create_time,data_points) VALUES(?,?,?,?,?)"}
	sql = {"eut":eut_sql,"data":data_sql}

	def __init__(self,db_name,table_name,queue_in=None,queue_out=None):
		threading.Thread.__init__(self)
		self.db_name    = db_name
		self.table_name = table_name
		self.queue_in   = queue_in
		self.queue_out  = queue_out
		self.CreateTable()
		
	def CreateTable(self):
		db_con   =sqlite.connect(self.db_name)
		db_con.text_factory = str #解决8bit string 问题
		db_cursor=db_con.cursor()
		cmd	 = Thread_Sql.sql[self.table_name]["query_table"]
		db_cursor.execute(cmd)
		for x in db_cursor:
			if x[0] < 1:
				SELECT   = "create table %s  "%(self.table_name)
				SELECT += "("
				SELECT += Thread_Sql.sql[self.table_name]["fields"]
				SELECT += ")"
				print SELECT
				db_cursor.execute(SELECT)
				db_con.commit()
			else:
				print "table %s existed already." % (self.table_name)
		#~ sys.stdout = self
		db_con.close()
		
	def write(self,TE):
		pass

	def run(self):#运行一个线程
		self.db_con   =sqlite.connect(self.db_name)
		self.db_con.text_factory = str #解决8bit string 问题
		self.db_cursor=self.db_con.cursor()
		while True:
			self.Cmd_line(timeout=0.01)
			time.sleep(0.001)

	def Cmd_line(self,timeout=0):
		
		target,cmd=self.queue_in.get()#get command (from self.queue_in), then process it and response(to  self.queue_out)
		if target.startswith("session"): #excute
			result = self.SessionPersist(cmd)#处理并返回结果(通过queue_out)
		elif target.startswith("data"):# 
			result = self.DataPersist(cmd)#处理并返回结果(通过queue_out)
		else:
			result = "Warning: request an  unknown target. \n\t Should starts with 'session' or 'data'"
		self.queue_out.put(result)
			
	def SessionPersist(self,session4persist):
		return None


	def DataPersist(self,block4persist):
		cmd, data = (block4persist[0], block4persist[1])

		if cmd.startswith("save"):
			SELECT   =  Thread_Sql.sql[self.table_name]["save"]
			print SELECT,data
			self.db_cursor.execute(SELECT,data)
			self.db_con.commit()
			return "save ok"

		if cmd.startswith("query"):
			field  	  = data[0]
			condition = data[1]
			#~ print "start query...\n"
			SELECT   = "select %s from %s %s"%(field,self.table_name, condition)
			print SELECT
			result = []
			self.db_cursor.execute(SELECT)
			while 1:
				try:
					record = self.db_cursor.fetchone()
					print record[0]
					result.append(record)
				except:
					break
				
			print 'date len',len(result)
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
	queue_eut = (Queue(0),Queue(0))

	app2 = Thread_Sql(db_name=config_db.eut_db,
		table_name = config_db.eut_table_name,
		queue_in   = queue_eut[0],
		queue_out  = queue_eut[1])
	app2.setDaemon(True)
	app2.start()

#~	cmd_ =("data:", ("query:",("*","data_valid=1 AND create_time LIKE '%2014-02-09%'")) )
#~	queue_data[0].put(cmd_)
#~	print "wait for SQL...."
#~	result = queue_data[1].get()
#~	print "result len is: %d"% (len(result))
#~	try:
#~		for row in result:
#~			cmd_=("data:",("save:",row))
#~			queue_data[0].put(cmd_)
#~			#~ print row 
#~			name,serial,valid,time,data_pack = row
#~			data_points = []
#~			data_size = struct.calcsize('I5f')
#~			offset = 0
#~			while 1:
#~				try:
#~					data = struct.unpack_from('I5f',data_pack, offset)
#~					#~ print data
#~					data_points.append(data)
#~					offset += data_size
#~				except:
#~					break
#~			#print name,'\t',serial,'\t',time, '\t','data as below'
#~			#ShowDataPoints(data_points)
#~	except:
#~		print "timeout1...."
#~		pass
#~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ save sql testing ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~	cmd_ =("data", ("save",("sst3278","s23-n38-22233444","10~10000")) )
#~	queue_eut[0].put(cmd_)
	cmd_ =("data", ("query",("*","where model like '%%' and PN like '%%'")) )
	queue_eut[0].put(cmd_)
	time.sleep(1)
	while not queue_eut[1].empty():
		row = queue_eut[1].get()
		if row:
			print row 
			#ShowDataPoints(data_points)
#`	cx   =sqlite.connect("sqlite3_eut.db")
#`	cx.text_factory = str #解决8bit string 问题
#`	cu=cx.cursor()
#`	#cu.execute('create table eut (name TEXT, age TEXT, skill TEXT)')
#`	#cx.commit()
#`	cu.execute('insert into eut values (?,?,?)',("ieek","99","doll"))
#`	cx.commit()
#`	cu.execute('select * from eut')
#`	for x in cu.fetchall():
#`		print x
#`
