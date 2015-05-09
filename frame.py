# -*- coding: utf-8 -*-
"""Create a Frame instance and display image.""" 
import sys 
import wxversion
wxversion.select("3.0")
import wx 
from signal_control import Signal_Control
import string 
import time
import util
import pga

import server_endpoints
import wx.animate



class Frame(wx.Frame):   #3
	def __init__(self,  parent=None, id=-1,size=(1024,768),
		pos=wx.DefaultPosition,
		title='Hello,wxPython!'):
		super(Frame, self).__init__(parent=parent, id=id, title=title,size=size)
		self.signals = []
		self.spaces = []
		self.signals_count = 0

		


		
		self.topsizer =wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗
#		self.topsizer.Add(self.sizer_toolbar)
		#self.topsizer.Add(self.sizer_signals,wx.EXPAND|wx.ALL)

		self.SetSizer(self.topsizer)
		self.CreateMenu()
		#print " create menu ok"


		self.SetEditable(False)
		#print "add signal"

		#有循环依赖关系: self.AddSignals() self.InitSession()
		self.InitSession()
		#重要：下面进行其它部分配置的更新!!!
		pga.gPGA.SetVrefs()
		self.AddSignals(1)
		self.signals[0].signal_panel.ResumeSession()
		#print "add signal OK"
		self.Show(True)
		print "now show logo"	
		self.ShowLogo()


		#self.signals[0].signal_panel.ResumeSession()
		self.timer = wx.Timer(self,-1)
		self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
		self.timer.Start(500,False)

	def InitSession(self):
		self.OpenSession("default.session")


	def OnTimer(self,event):
		self.StopLogo()

	def StopLogo(self):
		self.curGif.Stop()
		self.curGif.Show(False)
		self.timer.Stop()

	def ShowLogo(self):
		self.ShowGif('logo.gif')
		pass


	def ShowGif(self,fpath):
		mm  = wx.DisplaySize()
		img = wx.Image(fpath, wx.BITMAP_TYPE_GIF)
		x0  = (mm[0] - img.GetWidth())/2
		y0  = (mm[1] - img.GetHeight())/2
		self.curGif = wx.animate.GIFAnimationCtrl(self,-1,fpath,(x0,y0),(img.GetWidth(), img.GetHeight()))
		self.Bind(wx.EVT_LEFT_DOWN,self.OnTimer,self.signals[0])
		self.curGif.GetPlayer().UseBackgroundColour(True)
		self.curGif.Play()

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
		self.PushStatusText("total %d signals "%(self.signals_count))
		self.panel_signals.Refresh(True)
		self.Refresh(True)
		
	def CreateMenu(self):

		self.menuBar = wx.MenuBar()# 创建菜单栏 
		# 创建File菜单栏
		self.menu1 = wx.Menu()
		self.menu_open = self.menu1.Append(wx.NewId(), u"&Open/打开", "open session")
		self.menu_save = self.menu1.Append(wx.NewId(), u"&Save/保存", "save session")
		self.menu1.AppendSeparator()
		self.menu_run = self.menu1.Append(wx.NewId(), u"&Run|Pause/运行|暂停", "run or pause")
		self.menu1.AppendSeparator()
		self.menu1.AppendSeparator()
		self.menu_exit = self.menu1.Append(wx.NewId(), u"&Exit/退出", "exit ")
		self.menuBar.Append(self.menu1, u"&File/文件")                
		 # 创建Edit菜单栏
		self.menu2 = wx.Menu()
		self.menu_setUPSW = self.menu2.Append(wx.NewId(), u"&User Password/用户密码", "")
		self.menu_setAPSW = self.menu2.Append(wx.NewId(), u"&Admin Password/管理密码", "")
		self.menu2.AppendSeparator()
		self.menu_select = self.menu2.Append(wx.NewId(), u"&Select Comp./器件选择", "")
		self.menu_option  = self.menu2.Append(wx.NewId(), u"&Options/选项...", "")
		self.menuBar.Append(self.menu2, u"&Set设置")
		
		DBmenu = wx.Menu()
		self.menu_QueryDB = DBmenu.Append(wx.NewId(),u"&Query查询")
		self.menuBar.Append(DBmenu, u"&DataBase数据库")

		
		helpmenu = wx.Menu()
		helpmenu.Append(wx.ID_ABOUT, u"&About/关于")
		self.menuBar.Append(helpmenu, u"&Help/帮助")
		
		self.SetMenuBar(self.menuBar)
		self.Bind(wx.EVT_MENU, self.OnSaveSession, self.menu_save)
		self.Bind(wx.EVT_MENU, self.OnOpenSession, self.menu_open)
		self.Bind(wx.EVT_MENU, self.OnRunPause, self.menu_run)
		self.Bind(wx.EVT_MENU, self.OnExit, self.menu_exit)
		self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
		self.Bind(wx.EVT_MENU, self.OnSetPassword, self.menu_setUPSW)
		self.Bind(wx.EVT_MENU, self.OnSetPassword, self.menu_setAPSW)
		self.Bind(wx.EVT_MENU, self.OnSetupOptions, self.menu_option)
		self.Bind(wx.EVT_MENU, self.OnSelectComponent, self.menu_select)
		self.Bind(wx.EVT_MENU, self.OnQueryDB, self.menu_QueryDB)

		self.statusBar = self.CreateStatusBar()#1 创建状态栏 
		


		self.editable = False


	def OnRightDown(self,event):
		pos = self.ScreenToClient(event.GetPosition())
		self.PopupMenu(self.popmenu1, pos)

	def OnQueryDB(self,event):
		QueryUI = util.Server_("..\python27\python.exe refer_table.py")
		QueryUI.start()

	def OnSetupOptions(self,event):
		for signal in self.signals:
			if not signal:
				return
			signal.SetupOptions()

	def OnSelectComponent(self,event):
		for signal in self.signals:
			if not signal:
				return
			signal.SelectComponent()

	def OnSetPassword(self,event):

		if event.GetId() == self.menu_setUPSW.GetId():
			util.gAuthen.AuthenSetup(util.USER)
		else:
			util.gAuthen.AuthenSetup(util.ADMIN)

	
	def OnAbout(self, event):
		"""Show the about dialog"""
		info = wx.AboutDialogInfo()
		# Make a template for the description
		desc = [u"\nwxPython Cookbook Chapter\n",
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
		info.SetCopyright(u"Copyright () ")
		info.SetDescription(desc % (py_version, wx_info))
		# Create and show the dialog
		wx.AboutBox(info)

	#~ def OnIdle(self, event):#12 空闲时的处理
		#~ self.Relayout()
		
	def OnToggleEdit(self, event):#12 空闲时的处理
		self.editable = not self.editable 
		self.SetEditable(self.editable)
		
		
	def SetEditable(self, toggle):
		pass
	
	def OnExit(self, evt):
		self.Close()

	def OnRunPause(self,event):
		for signal in self.signals:
			signal.ToggleRun()
		


	def OnSaveSession(self,event):
		if not util.gAuthen.Authenticate(util.ADMIN):
			return False
		try:
			print "\nsession saved to default.session"
			print util.gSession
			dlg = wx.FileDialog(None,u"选择会话文件",wildcard="*.session")
			if dlg.ShowModal() != wx.ID_OK:
				dlg.Destroy()
				return
			session_file = open(dlg.GetPath(),'wb')
			session_file.write(util.gZpickle.dumps(util.gSession))
			print "\nsession saved to %s OK"%dlg.GetPath()
			session_file.close()
			dlg.Destroy()
		except Exception, e:
			session_file.close()
			print e

	def OnOpenSession(self,event):
		#try:
		dlg = wx.FileDialog(None,u"选择会话文件",wildcard="*.session")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		session_file_name = dlg.GetPath()
		self.OpenSession(session_file_name)
		#重要：下面进行其它部分配置的更新!!!
		pga.gPGA.SetVrefs()
		self.signals[0].signal_panel.ResumeSession()
		dlg.Destroy()

	def OpenSession(self,session_file_name):
		try:
			print "\nload new session"
			session_file = open(session_file_name,'rb')
			util.gSession = util.gZpickle.loads(session_file.read())
			print util.gSession
			session_file.close()
			return True
		except Exception,e:
			print "\nload session failed:"
			print e
			return False
		self.Refresh(True)

	def OnAddSignals(self,event):
		self.AddSignals(self.step_add.GetValue())
		self.Relayout()
		


	def AddSignalOnce(self,signal):
		self.signals_count += 1
		self.topsizer.Add(signal,1,wx.EXPAND|wx.ALL)
		
		self.signals.append(signal)

		
	  
	def AddSignals(self,signals_num=1):
		while signals_num != 0:
			port = '%d'%(server_endpoints.PORT)
			ip = '%s'%(server_endpoints.IP_ADDRESS)
			URL = ip+':'+port+'/'+'usb1'
			#print URL
			
			sizeX,sizeY = wx.DisplaySize()
			signal_ctrl = Signal_Control(parent=self,
						size = (sizeX*5,sizeY*8/10),
						#size = (1200,700),
						id=-1,
						url = URL,
						eut_name="",
						eut_serial="",)
			print "display size", wx.DisplaySize(),
			#signal_ctrl.populate_data()
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


			


####################################################################################################
if __name__=='__main__':
	util.gServer4EP.start()
	time.sleep(0.5)
	app = wx.App()
	frm = Frame(None, -1)
	frm.Maximize()
	app.SetTopWindow(frm)
	#frm.ShowFullScreen(True)
	app.MainLoop()

