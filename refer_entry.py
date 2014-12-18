# -*- coding: utf-8 -*-
#!python
import glob
import string



class Refer_Entry(object):
#	__slots__ = {"Xvalue":float,"Xprecision":float,"Yvalue":float,"Yprecision":float,"Yoffset":float,"Ymin":float,"Ymax":float}
	def __init__(self,Xvalue=0,Xprecision=0,Yvalue=0,Yprecision=0,Yoffset=0,Ymin=0,Ymax=0,valid_status=False):
		self.valid_status = valid_status
		self.Xvalue	= self.ToFloat( Xvalue)
		self.Xprecision = self.ToFloat( Xprecision)
		self.Yvalue	= self.ToFloat (Yvalue)
		self.Yprecision = self.ToFloat(Yprecision)
		self.Yoffset	= self.ToFloat(Yoffset)
		self.Ymin = self.ToFloat(Ymin)
		self.Ymax = self.ToFloat(Ymax)

	def ToFloat(self,value):
		if not value:
			value = float(0)
		return float(value)

	def Values(self):
		return (self.Xvalue,self.Xprecision,self.Yvalue,self.Yprecision,self.Yoffset,self.Ymin,self.Ymax)

	def ShowSensor(self):
		out = ''
		out += "X:%.3f,"%(self.Xvalue)
		out += "Xp:%.3f,"%(self.Xprecision)
		out += "Y:%.3f,"%(self.Yvalue)
		out += "Yp:%.3f,"%(self.Yprecision)
		out += "Yo:%.3f,"%(self.Yoffset)
		return out

	def ShowThermo(self):
		out = ''
		out += "X:%.3f,"%(self.Xvalue)
		out += "Ymin:%.3f,"%(self.Ymin)
		out += "Y:%.3f,"%(self.Yvalue)
		out += "Ymax:%.3f,"%(self.Ymax)
		return out
	
	def GetValidStatus(self):
		return self.valid_status

	def SetValidStatus(self,status):#status= True/False
		self.valid_status = status


	def GetXvalue(self):
		return self.Xvalue

	def SetXvalue(self,value):
		self.Xvalue= float(value)

	def GetXprecision(self):
		return self.Xprecision

	def SetXprecision(self,value):
		self.Xprecision= float(value)

	def GetYvalue(self):
		return self.Yvalue

	def SetYvalue(self,value):
		self.Yvalue= float(value)

	def GetYmin(self):
		return self.Ymin

	def SetYmin(self,value):
		self.Ymin= float(value)

	def GetYmax(self):
		return self.Ymax

	def SetYmax(self,value):
		self.Ymax= float(value)

	def GetYprecision(self):
		return self.Yprecision

	def SetYprecision(self,value):
		self.Yprecision= float(value)

	def GetYoffset(self):
		return self.Yoffset

	def SetYoffset(self,value):
		self.Yoffset= float(value)

