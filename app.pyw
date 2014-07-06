# -*- coding: utf-8 -*-
#!python
"""Hello, wxPython! program"""

# FileName simple.py

import sys 
import wx 
import os 
from wx import xrc 
import urllib

from frame import Frame


class MyApp(wx.App): 
	def OnInit(self): 

#		image = wx.Image('background_1024_768.jpg', wx.BITMAP_TYPE_JPEG)   
		self.frame = Frame(parent=None, id=-1, title='VR auto system' )
		self.frame.Show() 
		print "App Init...\n"
		return True 


if __name__ == '__main__':   #6
	app = MyApp() 
	app.MainLoop() 
