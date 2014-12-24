# -*- coding: utf-8 -*-
#!python
"""Create a Frame instance and display image.""" 
import sys 
import wx
import os 
import math
import wx.lib.agw.balloontip as btip

class Data_Real(wx.Object):
	def __init__(self,
				pos=0,
				value=0.0,
				):
		self.pos   = float(pos)
		self.value= float(value)
		
	def GetPos(self):
		return self.pos
			
	def GetValue(self):
		return self.value


class Data_Validated(wx.Object):
	def __init__(self,valid= False,
				pos=0,
				value=-100,
				value_refer=0.0,
				precision_refer=0.0,
				precision=0.0,
				):
		self.valid = valid
		self.pos   = pos
		self.value= value
		self.value_refer     = value_refer
		self.precision_refer= precision_refer
		self.precision         = precision
		self.length = int(1)
		
	def GetValid(self):
		if self.valid:
			return True
		else:
			return False

	def GetXvalue(self):
		return self.pos


	def GetYvalue(self):
		return self.value
			
	def GetValue_refer(self):
		return self.value_refer

	def GetPrecision_refer(self):
		return self.precision_refer
	
	def GetPrecision(self):
		return self.precision
	
	def SetLength(self,length):
		self.length = abs(int(length))
	
	def GetLength(self):
		return self.length 
	

class Data_Point(wx.Object):
	def __init__(self, data=[],  ok_color="blue", bad_color="red"):
		if data:
			self.data = data
		else:
			self.data = []
			self.data.append(Data_Validated())
		self.ok_color   = ok_color
		self.bad_color = bad_color


	
	def GetData(self):
		return self.data
		
	def AppendData(self,data_validated):
		self.data.append(data_validated)	

	def SetOkColor(self,color):
		self.ok_color   = color  
		
	def SetBadColor(self,color):
		self.bad_color   = color
	

	
		
		
############################################################################################################################################
class Signal_Control_Basic(wx.Panel):   
	def __init__(self,
		     parent=None,
		     size_=(-1,-1),
		     id=-1,
		     bg_color = "grey",
		     color_ok=wx.Color(0,250,0,200),
		     color_bad=wx.Color(250,0,0,200),
		     eut_name="qw32edrt44s",
		     eut_serial="10p8-082wj490",
		     points=25):
		super(Signal_Control_Basic, self).__init__(parent, id,size=size_)
		self.bg_color= bg_color #persist~~~~~~~~~~~~~~~~~~
		self.color_ok = color_ok  #persist~~~~~~~~~~~~~~~~~~
		self.color_bad = color_bad #persist~~~~~~~~~~~~~~~~~~ 
		self.eut_name = eut_name #persist~~~~~~~~~~~~~~~~~~
		self.eut_serial = eut_serial #persist~~~~~~~~~~~~~~~~~~
		self.points = points
		self.MaxValue = 200 

		

		self.topsizer = wx.BoxSizer(wx.VERTICAL)# 创建一个分割窗

		box_name=wx.StaticBox(self,label=u"名称")
		sizer_name = wx.StaticBoxSizer(box_name,wx.VERTICAL)
		self.text_name = wx.TextCtrl(self,-1,eut_name,style=(wx.TE_READONLY),size=(200,20))
		sizer_name.Add(self.text_name,2,wx.EXPAND|wx.LEFT|wx.RIGHT)

		box_serial=wx.StaticBox(self,label=u"序列号")
		sizer_serial = wx.StaticBoxSizer(box_serial,wx.VERTICAL)
		self.text_serial = wx.TextCtrl(self,-1,eut_serial,style=(wx.TE_READONLY),size=(200,20))
		sizer_serial.Add(self.text_serial, 0, wx.ALL, 0)

		self.sizer_info = wx.BoxSizer(wx.HORIZONTAL)# 创建一个分割窗
		self.sizer_info.Add(sizer_name)
		self.sizer_info.Add((20,00))
		self.sizer_info.Add(sizer_serial)
		self.topsizer.Add(self.sizer_info,0,wx.EXPAND|wx.LEFT|wx.RIGHT)

		self.sizer_data = wx.BoxSizer(wx.HORIZONTAL)
		self.topsizer.Add(self.sizer_data, 20,wx.EXPAND|wx.LEFT|wx.RIGHT)
		
		self.SetSizer(self.topsizer)
		self.data_store = []
		self.SetupPoints(self.points)
		self.Layout()
		

	def AppendPointValue(self,point,data_v_obj):
		self.data_store[point].data.append(data_v_obj)

	def SetMaxValue(self,maxvalue):
		self.MaxValue = maxvalue 
		
	def GetMaxValue(self):
		return self.MaxValue

	def SetupPoints(self, points):
		if len( self.data_store) != 0 :
			for window in self.data_store:  #清空data points
				self.sizer_data.Detach(window)
				window.Destroy()
		self.data_store = []		 #重新生成data points
		max_value = self.GetMaxValue()
		data_height = self.GetClientRect().height
		for index in range(0,points):
			#~ print "point's max value:%5.2f"%max_value
			data_panel = Data_Point(parent=self, id =-1,
						size=(5,data_height), 
						data=[],
						max_value=max_value,
						ok_color=self.color_ok,
						bad_color=self.color_bad)
			data_panel.SetBackgroundColour(self.bg_color)
			self.data_store.append(data_panel)
			self.sizer_data.Add(data_panel ,1,wx.EXPAND|wx.LEFT|wx.RIGHT,0)
		self.Layout()
		self.Refresh(True)

		
	def ShowData(self):
		datas_v= []
		for data_point in self.data_store:
			datas_v.append(data_point.data[-1])
		self.FormatData(sys.stdout,datas_v)

	def FormatData(self,tofile,datas_v):
		out  = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		out += "%s\t"%self.eut_name 
		out += "%s\t"%self.eut_serial
		out += u' 数据清单如下:\n'
		out += u"位置\t数值\t参考值\t参考精度\t实际精度\t结果"
		print >> tofile,out
		for cur_data_v in datas_v:
			valid = cur_data_v.GetValid()
			pos   = cur_data_v.GetPos()
			value= cur_data_v.GetValue()
			value_refer= cur_data_v.GetValue_refer()
			precision_refer= cur_data_v.GetPrecision_refer()
			if valid:
				valid_view = u"Pass"

			else:
				valid_view = u"Fail"
				self.debug_out.SetStyle( self.debug_out.GetNumberOfLines(),
								-1,
								wx.TextAttr("yellow","red"))
			line_cur  =  "%4d\t"   % pos
			line_cur +=  "%5.2f\t" % value
			line_cur +=  "%5.2f\t" % value_refer
			line_cur +=  "%5.4f\t\t" % precision_refer
			line_cur +=  "%5.4f\t\t"% precision
			line_cur +=  "%s\n"   % valid_view
			print >> tofile,line_cur 
			out += line_cur 
			self.debug_out.SetStyle( self.debug_out.GetNumberOfLines(),
							-1,
							wx.TextAttr("black","white"))
	
		return out
	
		

############################################################################################################################################


if __name__=='__main__':
	app = wx.App()
	frm = wx.Frame(None)
	panel = Data_Point(parent=frm,id=-1,
					ok_color=wx.Colour(0,250,0,alpha=250),
					bad_color=wx.Colour(250,0,0,alpha=250),
					data=[],
					max_value=200)
					
	data_v = Data_Validated(valid=False,
						pos=5,
						value=90,
						value_refer=101,
						precision_refer=0.01,
						precision =-0.05)
	panel.AppendData(data_v)
	
	frm.SetSize((800,600))
	frm.Show()
	app.SetTopWindow(frm)
	app.MainLoop()
	
