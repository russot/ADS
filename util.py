# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import sys
import wx
import glob
import os 
import string
import threading
import time
from socket import *
from hashlib import md5
from StringIO import StringIO
import gzip
import cPickle as pickle

#from refer_entry import Refer_Entry

class Authen():

	def md5sum(self,text):
		m = md5()
		m.update(text.encode('utf-8'))
		return m.hexdigest()
	
	def Authenticate(self,role):
	
		if role == "Admin":
			message = u"管理密码"
			fname   = 'ad01'
		elif role == "User":
			message = u"用户密码"
			fname   = 'ad02'

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
		f=file(fname,'r')
		pwd_org=f.read()
		f.close()
		result = False
		if str(pwd_org)[:32] == pwd_:
			result = True
		return result

	def AuthenSetup(self,role):
		dlg= wx.PasswordEntryDialog(None, message=u"管理密码",
				caption=u"input password/输入密码", 
				value="", 
				style=wx.TextEntryDialogStyle,
				pos=wx.DefaultPosition)
		dlg.ShowModal()
		password  = dlg.GetValue()
		dlg.Destroy()
		pwd_ = self.md5sum(password)
		print pwd_
		f=file('ad01','r')
		pwd_org=f.read()
		f.close()
		if str(pwd_org)[:32] == pwd_:
			print u"可以开始了..."
		elif password == "wxpython":
			print u"初次设置..."
		else:
			print u"管理密码错"
			msg = wx.MessageDialog(None,message=u"错误:",
					caption=u"管理密码错")
			msg.ShowModal()
			return 
		if role == 'user':
			psw_file = file('ad02','w')
			message_ = u'新用户密码'
		else:
			psw_file = file('ad01','w')
			message_ = u'新管理密码'

		dlg= wx.PasswordEntryDialog(None, message=message_,
				caption=u"input new password/输入新密码", 
				value="", 
				style=wx.TextEntryDialogStyle,
				pos=wx.DefaultPosition)
		dlg.ShowModal()
		password  = dlg.GetValue()
		dlg.Destroy()
		pwd_ = self.md5sum(password)
		psw_file.write(pwd_)
		psw_file.close()

gAuthen = Authen()


class Zips():
	def zip(self,data):
		buf = StringIO()
		f   = gzip.GzipFile(mode='wb',fileobj=buf)
		try:
			f.write(data)
		finally:
			f.close()
		return buf.getvalue()#压缩后的数据块

	def unzip(self,cdata):
		buf = StringIO(cdata)
		f   = gzip.GzipFile(mode='rb',fileobj=buf)
		try:
			data=f.read()
		finally:
			f.close()
		return data

gZip = Zips()

class PickleZip():
	def dumps(self,obj):
		obj_pickle = pickle.dumps(obj)
		return  gZip.zip(obj_pickle)

	def loads(self,obj_picklez):
		obj_pickle = gZip.unzip(obj_picklez)
		return pickle.loads(obj_pickle )

gZpickle = PickleZip()

		
class Server_(threading.Thread):
	def __init__(self,commandline):
		threading.Thread.__init__(self)
		self.commandline = commandline
		self.setDaemon(True)

	def SetCommandline(self,commandline):
		self.commandline = commandline

	def run(self):
		os.system(self.commandline)
gServer4EP = Server_("python server_ep.py")

