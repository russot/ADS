# -*- coding: utf-8 -*-
from decimal import *
import util
#import configure



#constants for RELAYS
gRDSon  = 0.05000
gRcon  = 0.05000

#constants for ADC resolution , A2 channel amplifier

#index for circuit component
_RR  = 0
_RA1 = 1
_RAH = 2
_RH  = 3
_RL  = 4
_REF = 5
_RUH = 6
#for PT thermo 
_RPH = 7
_RPAH= 8
_RPAL= 9
#for  NTC  
_RNH = 10


#index for circuit node
_VREF = 0
_VADC = 1
_VDD  = 2
_PMM  = 3

#index for gain
_GAIN = 0
_Rpar = 0
_Rx = 1
_RV = 2

#index for RR_par  
_R = 0
_SER = 1


#index for range_
_MIN = 0
_MAX = 1

#index for solutions
_VMIN  = 0
_VMIN_R  = 1
_VMAX  = 2
_IR = 3
_IG = 4 


#index for config
_G_  = 0
_R_  = 1
_CODE_  = 2

_RR_  = 0
_RA1_  = 1
_RA2_  = 2
_RANGE_  = 3

def find(list_,item):
	result = None
	for x in range(0,len(list_)):
		if list_[x] ==  item:
			result = x
			break
	return result

class  Pga():
	def __init__(self,Rs):
		getcontext().prec = 20
		self.ADC_BITS = 12
		self.Rs = Rs
		self.SetVrefs()

	def SetVrefs(self):
		self.config=util.gSession["signal_config"]
		self.gains=[]
		self.init_gains()
		self.init_RR_series()
		self.resolvs = 3.0
		self.unit = 'Ohm'

	def GetVrefs(self):
		return self.Vrefs

#----------------------------------------------------------------------------------------------------
	def init_gains(self):
		#self.init_gains_serial()
		self.init_gains_par()


	def init_gains_par(self):
		if not self.Rs:
			return
		self.gains.append( [1,None,3.4E38]) #for RA1 being all open
		return
		#below is comment out by return above
		for i in range(1,pow(2,len(self.Rs[_RA1])) ):
			r_par = 3.4E38
			par_series = self.find_series(i)
			for r_j in par_series:
				Rx =  Rs[_RA1][r_j] + gRDSon
				r_par = r_par * Rx / (r_par + Rx)

			R_AH = float(self.Rs[_RAH][0])
			k1= float(r_par+R_AH)/r_par
			self.gains.append( [k1,par_series,r_par] )
		#self.gains.append( [1,None,3.4E38]) #for RA1 being all open
		self.gains.sort(key=lambda x:x[_GAIN])

#----------------------------------------------------------------------------------------------------
	def find_series(self,i):
		result =[]
		remain = i
		ser = []
		for i in range(0,16):
			ser.append(pow(2,i))
		index = len(ser)
		for x in range(1,index+1):
			if not (remain - ser[index-x])<0 :
				remain -= ser[index-x]
				result.append(index-x)
				if remain == 0 :
					break
		return result

#----------------------------------------------------------------------------------------------------
	def init_RR_series(self):
		if not self.Rs:
			return
		self.RR_par=[]
		for i in range(1,pow(2,len(self.Rs[_RR])) ):
			r_par = 3.4E38
			par_series = self.find_series(i)
			for r_j in par_series:
				Rx = Rs[_RR][r_j] + gRDSon
				r_par = r_par * Rx  / (r_par + Rx)

			self.RR_par.append( [r_par,par_series] )
		self.RR_par.sort(key=lambda x:x[_Rpar])

	
#----------------------------------------------------------------------------------------------------
	def show_gains(self):
		self.show_gains_par()

	def show_gains_par(self):
		index = 0
		last_gain = self.gains[0]
		for gain in self.gains[0:]:
			index +=1
			if gain[_GAIN]/last_gain[_GAIN] > 0.2:
				print '%03d:%.5f %.5f\t%.5f'%(
					index,
					gain[_GAIN],
					gain[_GAIN]/last_gain[_GAIN],
					gain[_RV])
				print 'RA=', gain[_Rx]
			last_gain = gain

#----------------------------------------------------------------------------------------------------
	def Get_Hex2MiliMeter(self,Xvalue_):
		pmm = util.gSession["signal_config"]["Vrefs"][_PMM]
		return float(Xvalue_)/pmm

#----------------------------------------------------------------------------------------------------
	def Get_Hex2Float(self,HexValue):
		result = 0.0000
		if self.unit == 'Ohm':
			result = self.Get_Hex2R(HexValue)
			#print "get Ohm."
		elif self.unit == 'Volt':
			result = self.Get_Hex2U(HexValue)
			#print "get Volt"
		elif self.unit == 'Amp':
			result = self.Get_Hex2I(HexValue)
			#print "get Amper."
		return result



#----------------------------------------------------------------------------------------------------
	def find_solution(self,range_,unit_):
		unit = unit_.strip(' ')
		print "unit......",unit
		if unit.startswith('Ohm') or  unit.startswith('ohm'):	
			self.unit = 'Ohm'
			self.find_solution4R(range_)
		elif unit.startswith('Vol') or  unit.startswith('vol') :	
			self.unit = 'Volt'
			self.find_solution4U(range_)
		elif unit.starswith('Amp') or  unit.startswith('amp'):	
			self.unit = 'Amp'
			self.find_solution4I(range_)
		return self.GetCode()


#----------------------------------------------------------------------------------------------------
	def find_solution4R(self,range_):
		Vresolv = self.config["Vrefs"][_VADC]/pow(2,self.ADC_BITS)
		Rmin   = float(range_[_MIN])*float(0.99)
		Rmin_r = float(range_[_MIN])
		Rmax_r = float(range_[_MAX])
		Rmax   = float(range_[_MAX])*float(1.01)
		RH     = float(self.Rs[_RH][0])
		RL     = float(self.Rs[_RL][0])
		Rref   = float(self.Rs[_REF][0])
		Rcon   = float(gRcon)
		Vref   = float(self.Vrefs[_VREF])
		Vadc   = float(self.Vrefs[_VADC])
		solutions=[]
		print "Rmin:%.3f"%Rmin
		print "Rmin_r:%.3f"%Rmin_r
		print "Rmax:%.3f"%Rmax
		print "Rref:%.3f"%Rref
		print "Rcon:%.3f"%Rcon
		print "Vref:%.3f"%Vref
		print "Vadc:%.3f"%Vadc
		print "Vresolv:%.6f"%Vresolv
		for ir in range(0,len(self.RR_par)):
			RRi= self.RR_par[ir][_R]
			Vi_min   = Vref*float(Rmin+Rcon)/float(RRi+Rref+Rmin+Rcon)
			Vi_min_r = Vref*float(Rmin_r+Rcon)/float(RRi+Rref+Rmin_r+Rcon)
			Vi_max_r = Vref*float(Rmax_r+Rcon)/float(RRi+Rref+Rmax_r+Rcon)
			Vi_max   = Vref*float(Rmax+Rcon)/float(RRi+Rref+Rmax+Rcon)
			ig = len(self.gains)
			while 1:
				ig -=1
				if ig < 0:
					break
				gain  = self.gains[ig][_GAIN]
				Vo_min = Vi_min * gain
				Vo_min_r = Vi_min_r * gain
				Vo_max_r = Vi_max_r * gain
				Vo_max = Vi_max * gain
				#if Vo_max <= Vadc*0.97  and (Vo_min_r-Vo_min) >= 2*self.Vresolv:
				if (Vo_min_r-Vo_min) >= self.resolvs*Vresolv and  (Vo_max-Vo_max_r) >= self.resolvs*Vresolv:
					solutions.append([Vo_min,Vo_min_r,Vo_max,ir,ig])
					#print Vo_max,'^^^^',(Vo_min_r-Vo_min)
					break
		if len(solutions) < 1:
			print "%.3f--%.3f solution not found."%(range_[_MIN],range_[_MAX])
			return
		#solution found 
		#solutions.sort(key=lambda x:(x[_VMAX]-x[_VMIN]))
		solutions.sort(key=lambda x:x[_VMAX])
		best_solution = solutions[0]
		print "sol len",len(solutions)
		ig = best_solution[_IG]
		a1_gain = self.gains[ig][_GAIN]
		Rai= self.gains[ig][_Rx]
		print a1_gain,'gain--r',Rai
		Ra= [] 
		Ra_code = 0
		if Rai:
			for x in Rai:
				Ra.append((x,self.Rs[_RA1][x]))
				Ra_code += pow(2,x)
		ir = best_solution[_IR]
		Rpar = self.RR_par[ir][_R]
		Rr= []
		Rr_code = 0
		for x in self.RR_par[ir][_SER]:
			Rr.append((x,self.Rs[_RR][x]))
			Rr_code += pow(2,x)

		out  = "range \t\t%05.3f~%05.3f\tfound with delta %.5f\n"%(range_[_MIN],range_[_MAX],best_solution[_VMIN_R]-best_solution[_VMIN])
		out += "ADC input\t %05.3f-%05.3f,"%(best_solution[_VMIN], best_solution[_VMAX])
		out += "gain %0.4f\n"%(self.gains[ig][_GAIN])
		out += "RR=%.5f@%d\t"%(Rpar,ir)
		print out
		print  "RR=",Rr
		print  "RA1=",Ra
		self.config[_RR_]  = (Rpar,Rr,Rr_code)
		self.config[_RA1_] = (a1_gain,Ra,Ra_code)
		self.config[_RA2_] = ([],1)
		self.config[_RANGE_] = (best_solution[_VMIN],best_solution[_VMAX])

	def Get_Hex2R(self,value_hex):
		#print self.config

		Vref = float(self.config["Vrefs"][_VREF])
		Vadc = float(self.config["Vrefs"][_VADC])
		Rref   = float(self.Rs[_REF][0])
		Rcon   = float(gRcon)
		Volt_A1out= float(Vadc)*float(value_hex)/float(pow(2,self.ADC_BITS))
		A1_gain   = float(self.config[_RA1_][_G_])
		Volt_Rout  = Volt_A1out/A1_gain
		Rpar = self.config[_RR_][_G_]
		Ri = (Volt_Rout*(Rref+Rpar+Rcon) - Vref*Rcon)/(Vref-Volt_Rout)
		return Ri

	def Get_R2Hex(self,value_R):
		#print self.config
		R_ = float(value_R)
		Vref = float(self.config["Vrefs"][_VREF])
		Vadc = float(self.config["Vrefs"][_VADC])
		Rref   = float(self.Rs[_REF][0])
		Rpar   = float(self.config[_RR_][_G_])
		Rcon   = float(gRcon)
		A1_gain= float(self.config[_RA1_][_G_])
		Volt_Rout  = Vref*(R_+Rcon)/(R_+Rcon+Rref+Rpar)
		Volt_A1out = Volt_Rout*A1_gain 
		ratio   = Volt_A1out/float(Vadc)
		hexValue   = int(ratio*float(pow(2,self.ADC_BITS)))
		return hexValue 
#----------------------------------------------------------------------------------------------------
	def find_solution4U(self,range_):
		Vadc = float(self.config["Vrefs"][_VADC])
		VMax = range_[_MAX]*1.01
		RUH = self.Rs[_RUH][0]
		Rcon   = float(gRcon)
		solutions=[]
		for ir in range(0,len(self.RR_par)):
			RRi= self.RR_par[ir][_R] + gRDSon
			Vi_max = float(VMax)*RRi/float(RRi+RUH+Rcon)
			ig = len(self.gains)
			while 1:
				ig -=1
				if ig < 0:
					break
				gain  = self.gains[ig][_GAIN]
				Vo_max = Vi_max * gain
				if Vo_max <= Vadc*0.97:
					solutions.append([0.001,0.001,Vo_max,ir,ig])
					break
		if not solutions:
			print "%.3f--%.3f solution not found."%(range_[_MIN],range_[_MAX])
			return
		solutions.sort(key=lambda x:x[_VMAX])
		best_solution = solutions[-1]

		ig = best_solution[_IG]
		a1_gain = self.gains[ig][_GAIN]
		a1i= self.gains[ig][_Rx]
		Ra= [] 
		Ra_code = 0
		if a1i:
			for x in a1i:
				Ra.append((x,self.Rs[_RA1][x]))
				Ra_code += pow(2,x)

		ir = best_solution[_IR]
		Rpar = self.RR_par[ir][_R]
		Rr= []
		Rr_code = 0
		for x in self.RR_par[ir][_SER]:
			Rr.append((x,self.Rs[_RR][x]))
			Rr_code += pow(2,x)

		out  = "range \t\t%05.3f~%05.3f\tfound with delta %.5f\n"%(range_[_MIN],range_[_MAX],best_solution[_VMIN_R]-best_solution[_VMIN])
		out += "ADC input\t %05.3f-%05.3f,"%(best_solution[_VMIN], best_solution[_VMAX])
		out += "gain %0.4f\n"%(self.gains[ig][_GAIN])
		out += "RR=%.5f@%d\t"%(Rpar,ir)
		print out
		print  "RR=",Rr
		print  "RA1=",Ra
		self.config[_RR_]  = (Rpar,Rr,Rr_code)
		self.config[_RA1_] = (a1_gain,Ra,Ra_code)
		self.config[_RA2_] = ([],1)
		self.config[_RANGE_] = (best_solution[_VMIN],best_solution[_VMAX])

	def Get_Hex2U(self,value_hex):
		#print self.config
		print "U_hex:",value_hex
		Vref = float(self.config["Vrefs"][_VREF])
		Vadc = float(self.config["Vrefs"][_VADC])
		RUH    = self.Rs[_RUH][0]
		RDSon = gRDSon  
		Rcon   = float(gRcon)
		Rpar_  = self.config[_RR_][_G_] + gRDSon
		print "Rpar&RUH",Rpar_,';',RUH
		Volt_Aout= float(Vadc)*float(value_hex)/float(pow(2,self.ADC_BITS))
		A_gain   = float(self.config[_RA1_][_G_])
		Volt_Ain  = Volt_Aout/A_gain
		print "Vadc_in:",Volt_Ain
		#Volt_Ain  = Vi * Rpar/(Rpar+RUH+Rcon)
		Vin = Volt_Ain  * (Rpar_+RUH+RDSon+Rcon) / (Rpar_+RDSon)
		print "Vin:",Vin
		return Vin

	def Get_U2Hex(self,Vin):
		#print self.config
		Vref = float(self.config["Vrefs"][_VREF])
		Vadc = float(self.config["Vrefs"][_VADC])
		RUH    = self.Rs[_RUH][0]
		Rcon   = float(gRcon)
		Rpar_  = self.config[_RR_][_G_] + gRDSon
		A_gain = float(self.config[_RA1_][_G_])
		Volt_Ain  = Vin * Rpar_/(Rpar_+RUH+Rcon)
		Volt_Aout = Volt_Ain  * A_gain
		HexValue  = Volt_Aout / Vadc*float(pow(2,self.ADC_BITS))
		#Volt_Ain  = Vi * Rpar/(Rpar+RUH+Rcon)
		return int(HexValue)

#----------------------------------------------------------------------------------------------------
	def find_solution4I(self,range_):
		Vadc = float(self.config["Vrefs"][_VADC])
		Imax = range_[_MAX]*1.01
		solutions=[]
		for ir in range(0,len(self.RR_par)):
			RRi= self.RR_par[ir][_R] + gRDSon
			Vi_max = Imax*RRi
			ig = len(self.gains)
			while 1:
				ig -=1
				if ig < 0:
					break
				gain  = self.gains[ig][_GAIN]
				Vo_max = Vi_max * gain
				if Vo_max <= Vadc*0.97:
					solutions.append([0.001,0.001,Vo_max,ir,ig])
					break
		if not solutions:
			print "%.3f--%.3f solution not found."%(range_[_MIN],range_[_MAX])
			return
		solutions.sort(key=lambda x:x[_VMAX])
		best_solution = solutions[-1]

		ig = best_solution[_IG]
		a1_gain = self.gains[ig][_GAIN]
		a1i= self.gains[ig][_Rx]
		Ra= [] 
		Ra_code = 0
		if a1i:
			for x in a1i:
				Ra.append((x,self.Rs[_RA1][x]))
				Ra_code += pow(2,x)

		ir = best_solution[_IR]
		Rpar = self.RR_par[ir][_R]
		Rr= []
		Rr_code = 0
		for x in self.RR_par[ir][_SER]:
			Rr.append((x,self.Rs[_RR][x]))
			Rr_code += pow(2,x)

		out  = "range \t\t%05.3f~%05.3f\tfound with delta %.5f\n"%(range_[_MIN],range_[_MAX],best_solution[_VMIN_R]-best_solution[_VMIN])
		out += "ADC input\t %05.3f-%05.3f,"%(best_solution[_VMIN], best_solution[_VMAX])
		out += "gain %0.4f\n"%(self.gains[ig][_GAIN])
		out += "RR=%.5f@%d\t"%(Rpar,ir)
		print out
		print  "RR=",Rr
		print  "RA1=",Ra
		self.config[_RR_]  = (Rpar,Rr,Rr_code )
		self.config[_RA1_] = (a1_gain,Ra,Ra_code)
		self.config[_RA2_] = ([],1)
		self.config[_RANGE_] = (best_solution[_VMIN],best_solution[_VMAX])

	def Get_Hex2I(self,value_hex):
		#print self.config
		Vadc = float(self.config["Vrefs"][_VADC])
		Rpar_    = self.config[_RR_][_G_] + gRDSon
		A_gain   = float(self.config[_RA1_][_G_])
		Volt_Aout= Vadc*float(value_hex)/float(pow(2,self.ADC_BITS))
		Volt_Ain  = Volt_Aout/A_gain
		#Volt_Ain  = Vi * Rpar/(Rpar+RUH+Rcon)
		Iin = Volt_Ain  / Rpar_
		return Iin

	def Get_I2Hex(self,Iin):
		#print self.config
		Vadc = float(self.config["Vrefs"][_VADC])
		Rpar_  = self.config[_RR_][_G_]+ gRDSon
		A_gain = float(self.config[_RA1_][_G_])
		Volt_Ain  = Iin * Rpar_
		Volt_Aout = Volt_Ain  * A_gain
		HexValue  = Volt_Aout / Vadc*float(pow(2,self.ADC_BITS))
		#Volt_Ain  = Vi * Rpar/(Rpar+RUH+Rcon)
		return int(HexValue)

#----------------------------------------------------------------------------------------------------
	def Get_Hex2Rpt(self,value_hex):
		Vadc = float(self.config["Vrefs"][_VADC])
		Vref = float(self.config["Vrefs"][_VREF])
		Rph   = float(self.Rs[_RPH][0])
		Rpah   = float(self.Rs[_RPAH][0])
		Rpal   = float(self.Rs[_RPAL][0])
		Volt_Aout= Vadc*float(value_hex)/float(pow(2,self.ADC_BITS))
		Again   = (Rpah+Rpal)/Rpal
		Vrpt  = Volt_Aout/Again
		Rpt =  Rph*Vrpt/(Vref*(1-Vrpt/Vref))
		return Rpt

	def Get_Rpt2Hex(self,Rpt):
		Vadc = float(self.config["Vrefs"][_VADC])
		Vref = float(self.config["Vrefs"][_VREF])
		Rph   = float(self.Rs[_RPH][0])
		Rpah   = float(self.Rs[_RPAH][0])
		Rpal   = float(self.Rs[_RPAL][0])
		Again   = (Rpah+Rpal)/Rpal
		Vrpt  = Vref*Rpt/(Rpt+Rph)
		Vao= Vrpt*Again
		HexValue  = Vao/Vadc*float(pow(2,self.ADC_BITS))
		return int(HexValue)

	def Get_Hex2Rntc(self,value_hex):
		Vadc = float(self.config["Vrefs"][_VADC])
		Vref = float(self.config["Vrefs"][_VREF])
		Rnh   = float(self.Rs[_RNH][0])
		Vntc  = Vadc*float(value_hex)/float(pow(2,self.ADC_BITS))
		Rntc  = Vntc*Rnh/(Vref-Vntc)
		return Rntc

	def Get_Rntc2Hex(self,Rntc):
		Vadc = float(self.config["Vrefs"][_VADC])
		Vref = float(self.config["Vrefs"][_VREF])
		Rnh   = float(self.Rs[_RNH][0])
		Vntc  = Vref*Rntc/(Rntc+Rnh)
		HexValue  = Vntc/Vadc*float(pow(2,self.ADC_BITS))
		return int(HexValue)

	def Get_Hex2Vout(self,value_hex):
		Vadc = float(self.config["Vrefs"][_VADC])
		Vref = float(self.config["Vrefs"][_VREF])
		RL   = gVout_RL
		RH   = gVout_RH
		Vadc_in	  = Vadc*float(value_hex)/float(pow(2,self.ADC_BITS))
		Vout	  = Vadc_in*gVout_Amp
		return Vout

	def GetCode(self):
		Rr_code = self.config[_RR_][_CODE_]
		Ra_code = self.config[_RA1_][_CODE_]
		print "Rr code: 0x%x \t Ra code: 0x%x"%(Rr_code, Ra_code)
		return (Rr_code, Ra_code)


#	def find_result4R(self,value_hex):
#		print self.config
#		RH = float(self.Rs[_RH][0])
#		RL = float(self.Rs[_RL][0])
#		Vref = self.Vrefs[_VREF]*RL/(RH + RL)
#
#		Volt_A2out= self.Vrefs[_VADC]*value_hex/pow(2,ADC_BITS)
#		A2_gain   = self.config[_RA2_][_R_]
#		Volt_A1out  = Volt_A2out/A2_gain
#		A1_gain   = self.config[_RA1_][_R_]
#		Volt_Rout  = Volt_A1out/A1_gain
#		RR = self.config[_RR_][_R_]
#		Ri = Volt_Rout/Vref*RR - RR 
#		return Ri
RA1_series = (	float(22),
		float(200),
		float(300),
		float(511),
		float(91000),
		float(5100),
		float(2000),
		float(1200)
		)
#RA1_series = (2,4,8,16,32,180,220,250)
RR_series = (	float(5), #R0
		float(10),#R1
		float(22),#R2
		float(100),#R3
		float(1200),#R4
		float(511),#R5
		float(300),#R6
		float(200),#R7
		float(2000),#R8
		float(3300),#R9
		float(3900),#R10
		float(7800),#R11
		float(99999999999),#R12
		float(94000),#R13
		float(47000),#R14
		float(18000),#R15
		)
RAH_series = (float(1200),)
RH_series = (float(18000),)
RL_series = (float(2000),)
REF_series = (float(50),)
RUH_series = (float(3900),)
#PT NTC series
RPH_series =  (float(18000),)
RPAH_series =  (float(18000),)
RPAL_series =  (float(1200),)
RNH_series  = (float(18000),)
RUH_series  = (float(3900),)

gVout_Full = 6000
gVout_RL   = float(1.5)
gVout_RH   = float(12.0)
gVout_Amp  = (gVout_RL+gVout_RH)/gVout_RL

Rs = [None,None,None,None,None,None,None,None,None,None,None,None]
Rs[_RR]  = RR_series
Rs[_RA1] = RA1_series
Rs[_RAH] = RAH_series
Rs[_RH]  = RH_series
Rs[_RL]  = RL_series
Rs[_REF]  = REF_series
Rs[_RPH]  = RPH_series
Rs[_RPAH]  = RPAH_series
Rs[_RPAL]  = RPAL_series
Rs[_RNH]  = RNH_series
Rs[_RUH]  = RUH_series

gPGA = Pga(Rs=Rs)

if __name__=='__main__':
	gPGA.show_gains()
	for range_,unit in (
			((5.6,190.6),'Ohm'),
			#((10,1000),'Ohm'),
			#((20,2000),'Ohm'),
			#((33,240),'Ohm'),
			#((40,4000),'Ohm'),
			#((50,5370),'Ohm'),
			#((100,10070),'Ohm'),
			((150,7870),'Ohm'),
			((200,20000),'Ohm'),
			((300,30000),'Ohm'),
			((500,20000),'Ohm'),
			((1000,100000),'Ohm'),
			((2000,200000),'Ohm'),
			((0,5),'Volt'),
			((0,10),'Volt'),
			((0,15),'Volt'),
			((0,0.010),'Amp'),
			((0.004,0.020),'Amp'),
			((5000,500000),'Ohm'),):
		gPGA.find_solution(range_,unit)
		hex_ = 0x0e00
		Rfind = gPGA.Get_Hex2R(0xe00)
		Hfind = gPGA.Get_R2Hex(Rfind)
		print "hex_0x%x-->R_%.5f-->hex_0x%x"%(hex_,Rfind,Hfind)
	print gPGA.find_series(1)
	print gPGA.find_series(128)
	print gPGA.find_series(255)
		
	for range_,unit in (
			#((0,5),'Volt'),
			#((0,10),'Volt'),
			#((0,15),'Volt'),
			((0,0.010),'Amp'),
		((0.004,0.020),'Amp'),
			):
		gPGA.find_solution(range_,unit)
		gPGA.GetCode()
		hex_ = 0x0e00
		volt = gPGA.Get_Hex2I(0xe00)
		Hfind = gPGA.Get_I2Hex(volt)
		print "hex_0x%x-->U_%.5f-->hex_0x%x"%(hex_,volt,Hfind)

	hex_ = 0x0d00
	Rpt_last = gPGA.Get_Hex2Rpt(hex_)
	count = 0
	for i in range(0,800):
		hex_ += 1
		count +=1
		Rpt = gPGA.Get_Hex2Rpt(hex_)
		if Rpt - Rpt_last >= 3.98:
			print u"%d bits/C"%count
			break
		print 'RPT_%.5f : 0x%x'%(Rpt,gPGA.Get_Rpt2Hex(Rpt))
		Rntc = gPGA.Get_Hex2Rntc(hex_)
		print 'RNTC_%.5f : 0x%x'%(Rntc,gPGA.Get_Rntc2Hex(Rntc))
