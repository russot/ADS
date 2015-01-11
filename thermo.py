# -*- coding: utf-8 -*-
#!python
"""Signal UI component .""" 
import math
from refer_entry import Refer_Entry
from thermo_sensor import *







#index for named cells
_VALUE	= int(0)
_RC	= int(1)

#index for refer table RC
REF_ROW = 6
REF_COL = 6


class Thermo():
	#__slots__ = {'ID':str, 'field': dict, 'Refer_Table': list}
	def __init__(self):
		self.PT = Thermo_Sensor()
		self.NTC = Thermo_Sensor()
		self.temprature = 0.0
		self.init_ok = True
		#self.SetPT("pt1000-01")

	def SetPT(self,PN):
		err_msg = u"Error: 无法测温，因为无PT1000电阻，请在NTC数据库中输入PT1000电阻!"
		self.init_ok = True
		if not self.PT.RestoreFromDBZ(PN):
			print err_msg
			self.init_ok = False
			return None
		print u"OK:设置PT 成功!"
		return True
		
	def SetNTC(self,PN):
		err_msg = u"Error: 无法在NTC数据库中找到此PN的NTC!"
		print "to set-ntc %s now...."%PN
		if not self.NTC.RestoreFromDBZ(PN):
			print err_msg
			return None
		print u"OK:设置NTC_%s 成功!"%PN
		return True
#----------------------------------------------------------------------------------------------------
#below method based on PT circuit 
	def GetRpt(self,hex_value):
		RA2H = 2000.0
		RA2L = 200.0
		RA1L = 200.0
		RRH  = 18000.0
		RRL  = 200.0
		Vref = 2.487
		VADC = 3.263
		Hex_Max = 4096.0
		A2_Vout = VADC*hex_value/Hex_Max
		A1_Vout = A2_Vout*RA2L/(RA2H+RA2L)
		A1_Vin  = Vref*RRL/(RRH+RRL)
		AMP1 = A1_Vout/A1_Vin
		Rpt  = AMP1*RA1L-RA1L
		print "Rpt current:%5.8f"%(A1_Vout/(Rpt+RA1L))
		print "A2out:%.5f,A1out:%.5f,A1in:%.5f,Rpt:%.5f"%(A2_Vout,A1_Vout,A1_Vin,Rpt)
		return Rpt

	def GetTemprature(self,hex_value):
		err_msg = u"Error: 无法测温，因为无PT1000电阻，请在NTC数据库中输入PT1000电阻!"
		if not self.init_ok:
			print err_msg
			return None
		Rpt = self.GetRpt(hex_value)
		self.temprature = self.PT.GetT(Rpt)

		print "temprature is %8.2f now"%self.temprature
		return self.temprature

#----------------------------------------------------------------------------------------------------
#below method based on NTC circuit 
	def GetRntc(self,hex_value,Amp1):
		RH = 2000.0
		Vref = 2.5
		VADC = 3.3
		Hex_Max = 4096.0
		A2_Vout = VADC*hex_value/Hex_Max
		A1_Vout = A2_Vout
		A1_Vin  = A1_Vout/Amp1
	#	A1_Vin  = Vref*Rntc/(Rntc+RH)
	#	Rntc*A1_Vin +RH*A1_Vin  =Vref*Rntc
	#	Rntc(A1_Vin-Vref) = -RH*A1_Vin
		Rntc= RH*A1_Vin/(Vref-A1_Vin)
		return Rntc

	def Validate(self,hex_NTC,hex_PT):
		Rntc = self.GetRntc(hex_value=hex_NTC,Amp1=1.2)
		temprature = self.GetTemprature(hex_PT)
		Rref = self.NTC.GetR(temprature)
		precision = self.NTC.GetPrecision()
		offset = abs(Rntc-Rref)/Rref
		if offset > precision:
			result = False
		else:
			result = True
		print precision,offset,"pre & real"
		return (result,temprature,Rntc,Rref)
	
############################################################################################################################################
Demo_PN = "010204"
Demo_PT = "pt1000-01"
gModule = False
if __name__=='__main__':
	#app = wx.App()
	gModule = True
	thermo  = Thermo()
	thermo.SetPT(Demo_PT)
	thermo.SetNTC(Demo_PN)
	print thermo.PT.GetT(thermo.PT.GetR(25.0)),"@25.0"
	print thermo.Validate(hex_NTC=0xa90,hex_PT=0x97d)
	
