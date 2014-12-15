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
		pwd_ = self.md5sum(password)
		psw_file.write(pwd_)
		psw_file.close()

gAuthen = Authen()
