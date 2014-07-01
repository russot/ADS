# -*- coding: utf-8 -*-
#!python
"""Create a Frame instance and display image.""" 
import sys 
import wx 
import os 
from wx import xrc 
import urllib
from signal_control import Signal_Control
import pickle
import string 
import wx.lib.scrolledpanel as scrolledpanel
import threading 
from Queue import Queue
import sqlite3 as sqlite
import config_db

from thread_sqlite import Thread_Sqlite


class Frame(wx.Frame):   #3
	def __init__(self,  parent=None, id=-1,size=(1024,768),
		pos=wx.DefaultPosition,
		title='Hello,wxPython!'):
		super(Frame, self).__init__(parent, id, title,size=size)
		self.signals = []
		self.spaces = []
		self.signals_count = 0
		self.signals_status = "stopped"
		

		


		self.scroller = wx.SplitterWindow(self)
		self.scroller.SetMinimumPaneSize(1)		
		self.leftsizer = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		


		self.btn_add = wx.Button(self,-1,"add")
		self.btn_del = wx.Button(self,-1,"del")
		self.btn_run = wx.Button(self,-1,"start")
		self.step_add = wx.SpinCtrl(self, -1,"5", wx.DefaultPosition, (50,-1), wx.SP_ARROW_KEYS,0, 20, 1)
		self.sizer_toolbar = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.sizer_toolbar.Add(self.btn_run)  # run 放在第一位
		self.sizer_toolbar.Add((100,20))
		self.sizer_toolbar.Add(self.step_add)
		self.sizer_toolbar.Add(self.btn_add)
		self.sizer_toolbar.Add(self.btn_del)
		self.btn_add.Bind(wx.EVT_BUTTON, self.OnAddSignals,self.btn_add)
		self.btn_del.Bind(wx.EVT_BUTTON, self.OnDelSignals,self.btn_del)
		self.btn_run.Bind(wx.EVT_BUTTON, self.OnRunSignals,self.btn_run)
		



		self.panel_signals = wx.ScrolledWindow(self.scroller,-1)
		self.panel_signals.SetScrollbars(1,1,200,200)
		#~ self.panel_signals = scrolledpanel.ScrolledPanel(self.scroller,-1,size=(200,500),style=wx.TAB_TRAVERSAL|wx.BORDER_SUNKEN)
		self.sizer_signals = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.panel_signals.SetSizer(self.sizer_signals)
#		self.AddSignals(2)

	   

		self.panel_info  = wx.ScrolledWindow(self.scroller,-1)
		self.debug_out   = wx.TextCtrl(self.panel_info,-1,style=(wx.TE_MULTILINE|wx.HSCROLL))
		self.sizer_info  = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.panel_info.SetSizer(self.sizer_info)
		#~ self.sizer_info.Add((10,10))
		self.sizer_info.Add(self.debug_out,1,wx.EXPAND|wx.LEFT|wx.RIGHT)
		

		self.panel_signals.Hide()
		self.panel_info.Hide()
		#~ self.scroller.Initialize(self.panel_signals)
		self.scroller.SplitVertically(self.panel_signals,self.panel_info,-300)

		
		self.topsizer =wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
		self.topsizer.Add(self.sizer_toolbar)
		self.topsizer.Add(self.scroller)

		self.SetSizer(self.topsizer)
		self.CreateMenu()

		sys.stdout = self.debug_out
		sys.stderr = self.debug_out
		self.Bind(wx.EVT_SIZE,self.OnResize)
		self.debug_out.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

		#创建 持久化线程,通过两个队列管道进行数据交换
		self.queue_persist_in = Queue(-1)
		self.queue_persist_out = Queue(-1)
		self.persist = Thread_Sqlite(queue_in  = self.queue_persist_in, 
							queue_out= self.queue_persist_out) 
		self.persist.setDaemon(True)
		self.persist.start()
		self.SetEditable(False)
		self.AddSignals(1)
		
		self.Relayout()

	def OnResize(self,evt):
		self.Relayout()
	
	def OnKeyDown(self, event):
		"""KeyDown event is sent first"""

		raw_code = event.GetRawKeyCode()
		modifiers = event.GetModifiers()

		#~ if raw_code == 75 and modifiers==3:
			#~ self.Close()
		if raw_code == 75 and modifiers==2:
			self.debug_out.SetValue("")
		
		# Must Skip the event to allow OnChar to be called
		#~ event.Skip()
		
		
	def Relayout(self):

		self.scroller.SetSize((self.GetSize().x, self.GetSize().y-100 ))
		self.scroller.SplitVertically(self.panel_signals,self.panel_info,-100)
		self.panel_signals.Layout()



		self.PushStatusText("total %d signals "%(self.signals_count))
		self.panel_signals.Refresh(True)
		self.Refresh(True)
		
	def CreateMenu(self):

		self.menuBar = wx.MenuBar()# 创建菜单栏 
		# 创建File菜单栏
		self.menu1 = wx.Menu()
		self.menu_open = self.menu1.Append(wx.NewId(), "&open", "open session")
		self.menu_save = self.menu1.Append(wx.NewId(), "&save", "save session")
		self.menu1.AppendSeparator()
		self.menu_import = self.menu1.Append(wx.NewId(), "&import...", "import data")
		self.menu_export = self.menu1.Append(wx.NewId(), "&export...", "export data")
		self.menuBar.Append(self.menu1, "&File")                
		 # 创建Edit菜单栏
		self.menu2 = wx.Menu()
		self.menu2.Append(wx.NewId(), "&Copy", "Copy in status bar")
		self.menu2.Append(wx.NewId(), "C&ut", "")
		self.menu2.Append(wx.NewId(), "&Paste", "")
		self.menu2.AppendSeparator()
		self.menu2.Append(wx.NewId(), "&Options...", "Display Options")
		self.menuBar.Append(self.menu2, "&Edit")
		
		helpmenu = wx.Menu()
		helpmenu.Append(wx.ID_ABOUT, "About")
		self.menuBar.Append(helpmenu, "Help")
		
		self.SetMenuBar(self.menuBar)
		self.Bind(wx.EVT_MENU, self.OnSaveSession, self.menu_save)
		self.Bind(wx.EVT_MENU, self.OnOpenSession, self.menu_open)
		self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)

		self.statusBar = self.CreateStatusBar()#1 创建状态栏 
		


		self.editable = False
		self.popmenu1 = wx.Menu()
		self.menu_run = self.popmenu1.Append(wx.NewId(), u"运行.全部", u"运行与暂停", kind=wx.ITEM_CHECK)
		self.popmenu1.AppendSeparator()
		#self.menu_query = self.popmenu1.Append(wx.NewId(), u"数据查询", u"查询已存储的数据")
		self.menu_query_ui = self.popmenu1.Append(wx.NewId(), u"数据组合查询", u"组合查询已存储数据")
		self.popmenu1.AppendSeparator()
		self.menu_editable = self.popmenu1.Append(wx.NewId(), u"编辑状态", u"进出编辑状态，增加/删除测试点", kind=wx.ITEM_CHECK )
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightDown)
		self.Bind(wx.EVT_MENU, self.OnRunSignals,self.menu_run)
		self.Bind(wx.EVT_MENU, lambda evt: os.startfile('dialog_query.pyw'),self.menu_query_ui)
		self.Bind(wx.EVT_MENU, self.OnToggleEdit,self.menu_editable)


	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)
	
	def OnAbout(self, event):
		"""Show the about dialog"""
		info = wx.AboutDialogInfo()
		# Make a template for the description
		desc = [u"\nwxPython Cookbook Chapter 5\n",
		u"Platform Info: (%s,%s)",
		u"License: Public Domain"]
		desc = u"\n".join(desc)
		# Get the platform information
		py_version = [sys.platform,
			u",python",
			sys.version.split()[0]]
		platform = list(wx.PlatformInfo[1:])
		platform[0] += (" " + wx.VERSION_STRING)
		wx_info = u",".join(platform)
		# Populate with information
		info.SetName(u"AboutBox Recipe")
		info.SetVersion(u"1.0")
		info.SetCopyright(u"Copyright () Joe Programmer")
		info.SetDescription(desc % (py_version, wx_info))
		# Create and show the dialog
		wx.AboutBox(info)

	#~ def OnIdle(self, event):#12 空闲时的处理
		#~ self.Relayout()
		
	def OnToggleEdit(self, event):#12 空闲时的处理
		self.editable = not self.editable 
		self.SetEditable(self.editable)
		
		
	def SetEditable(self, toggle):
		self.btn_add.Show(toggle)
		self.btn_del.Show(toggle)
		self.step_add.Show(toggle)
	
	def OnRunSignals(self,evt):
		if self.signals_count == 0:
			return 
		self.SetEditable(False)
		if self.signals_status != "stopped":
			self.signals_status = "stopped"
			self.btn_run.SetLabel("run")
			self.btn_run.SetBackgroundColour("green")
			for signal in self.signals:
				signal.Pause()

		else:
			self.signals_status = "running"
			self.btn_run.SetLabel("pause")
			self.btn_run.SetBackgroundColour("red")
			for signal in self.signals:
				signal.Run()

			
	def OnExit(self, evt):
		self.Close()


	
	def OnOpenSession(self,event):
		self.DelSignals(self.signals_count)
		dlg = wx.FileDialog(None,"select a file ")
		if dlg.ShowModal()!=wx.ID_OK:
			return
		file_name = dlg.GetPath()
		session_file = open(file_name,'r')
		
		#process each line as Signal_Control object
		for line in session_file.readlines():
			line = line.replace(" ","").replace("\t","").replace("\n","")
			for element in line.split(';'):
				pair = element.split('=')
				if pair[0] == "color_ok":
					str_ = pair[1].strip('(').strip(')')
					str_value = str_.split(',')
					color_ok = wx.Colour(string.atoi(str_value[0]),
                                                             string.atoi(str_value[1]),
                                                             string.atoi(str_value[2]),
                                                             string.atoi(str_value[3]))
				elif pair[0] == "color_bad":
					str_ = pair[1].strip('(').strip(')')
					str_value = str_.split(',')
					color_bad = wx.Colour(string.atoi(str_value[0]),
                                                             string.atoi(str_value[1]),
                                                             string.atoi(str_value[2]),
                                                             string.atoi(str_value[3]))
				elif pair[0] == "url_name":
					url_name = pair[1].strip('"')
				elif pair[0] == "refer_file":
					refer_file = pair[1].strip('"')

				elif pair[0] == "eut_name":
					eut_name = pair[1].strip('"')
				elif pair[0] == "eut_serial":
					eut_serial = pair[1].strip('"')
				elif pair[0] == "points":
					points_number = string.atoi(pair[1].strip('"'))
				else:
					pass
					
			signal_panel = Signal_Control(parent=self.panel_signals,
								id=-1, 
								size_=(-1,-1),
								color_ok=color_ok,
								color_bad=color_bad,
								url_name=url_name,
								eut_name=eut_name,
								eut_serial=eut_serial,
								refer_file=refer_file,
								points=points_number,
								persist = (self.queue_persist_in ,self.queue_persist_out)
								)
			
			self.AddSignalOnce(signal_panel)
		session_file.close()
		self.Relayout()
		
	def OnSaveSession(self,event):
		dlg = wx.FileDialog(None,"select a file ")
		if dlg.ShowModal()!=wx.ID_OK:
			return
		file_name = dlg.GetPath()
		session_file = open(file_name,'w')
		for signal in self.signals:
			line = "color_ok=%s;\
				color_bad=%s;\
				url_name=%s;\
				eut_name=%s;\
				eut_serial=%s;\
				refer_file=%s;\
				points=%s\n"\
				%(signal.color_ok,
				signal.color_bad,
				signal.url_name,
				signal.eut_name,
				signal.eut_serial,
				signal.refer_file,
				signal.points)
			session_file.write(line.replace(" ","").replace("\t",""))
		session_file.close()
		
	def SaveSession_sqlite(self):
		
		pass

	def OnAddSignals(self,event):
		self.AddSignals(self.step_add.GetValue())
		self.Relayout()
		


	def AddSignalOnce(self,signal):
		self.signals_count += 1
		self.sizer_signals.Add(signal,2,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
		signal.SetupPoints_()
		#self.sizer_signals.Add(signal)
		#加入数组,进行管理
		self.signals.append(signal)

		#~ self.spaces.append(space)

	  
	def AddSignals(self,signals_num=2):
		while signals_num != 0:
			signal_ctrl = Signal_Control(parent=self.panel_signals,
								id=-1,
								size_=(-1,-1), 
								refer_file="refer_table.cfg",
								points = 389,
								persist=(self.queue_persist_in, 
									self.queue_persist_out) 
								)
			self.AddSignalOnce(signal_ctrl)
			signals_num -= 1
		#扩展窗口以显示全貌
		#~ self.panel_signals.SetupScrolling()

	
	def OnDelSignals(self,event):
		self.DelSignals(self.step_add.GetValue())
		self.Relayout()

	def DelSignals(self,signals_num=2):
		if signals_num >  self.signals_count:
			signal_num =  self.signals_count
		while signals_num != 0:
			signal = self.signals.pop()
			#~ space  = self.spaces.pop()
			self.sizer_signals.Remove(signal)
			#~ self.sizer_signals.Remove(space)
			
			#资源回收
			signal.Destroy()
			#~ space.Destroy()
			self.signals_count -= 1
			signals_num -= 1
		#扩展窗口以显示全貌


			


if __name__=='__main__':
	app = wx.App(clearSigInt=True)
	frm = Frame(None, -1)
	#~ frm.SetSize((1000,700))
	frm.Show()
	app.SetTopWindow(frm)
	app.MainLoop()

