#config_db.py
data_db ="sqlite3_all.db"
data_table_name = "data"
eut_db ="sqlite3_eut.db"
eut_table_name = "eut"

#constants for RELAYS
R4RELAY  = 0.2

#constants for ADC resolution , A2 channel amplifier
ADC_BITS = 12
K_A2	 = 10

#index for circuit component
_RR  = 0
_A1 = 1
_RH  = 3
_RL  = 4

#index for circuit node
_VR = 0
_VADC = 1

#index for gain
_GAIN = 0
_A1i = 1
_A2i = 2

#index for RR_par  
_R = 0
_SER = 1


#index for range_
_MIN = 0
_MAX = 1

#index for solutions
_VMIN  = 0
_VMIN_M  = 1
_VMAX_M  = 2
_VMAX  = 3
_IR = 4
_IG = 5 


#index for config
_I_  = 0
_R_  = 1

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
	def __init__(self,Rs,Vrefs):
		self.Rs = Rs
		self.Vrefs = Vrefs
		self.config = [None,None,None,None]
		self.gains=[]
		self.init_gains()
		self.init_RR_series()

	def init_gains(self):
		#self.init_gains_serial()
		self.init_gains_par()

#	def init_gains_serial(self):
#		if not self.Rs:
#			return
#		j=0
#		for i in range(0,pow(2,len(Rs[_RA1])) ):
#			r_ = float(0)
#			series = self.find_series(i)
#			for r_j in series:
#				r_ +=  Rs[_RA1][r_j]
#
#			k2 = float(r_)+1
#			self.gains.append( [k2,series,j] )
#		self.gains.sort(key=lambda x:x[_GAIN])

	def init_gains_par(self):
		if not self.Rs:
			return
		j=0
		for i in range(0,pow(2,len(R[_RA1])) ):
			r_par = 0.0
			par_series = self.find_series(i)
			for r_j in par_series:
				if r_par == 0.0:
					r_par = r_j
					continue
				r_par = (r_par * self.R[_RA1][r_j]) /(r_par + Rs[_RA1][r_j])

			k1= float(r_par)+1
			self.gains.append( [k1,par_series,j] )
		self.gains.sort(key=lambda x:x[_GAIN])

	def find_series(self,i):
		result =[]
		remain = i
		ser = (1,2,4,8,16,32,64,128)
		index = len(ser)
		for x in range(1,index+1):
			if not (remain - ser[index-x])<0 :
				remain -= ser[index-x]
				result.append(index-x)
				if remain == 0 :
					break

		return result

	def init_RR_series(self):
		if not self.Rs:
			return
		j=0
		self.RR_par=[]
		for i in range(0,pow(2,len(Rs[_RR])) ):
			r_par = pow(2,32)
			par_series = self.find_series(i)
			for r_j in par_series:
				Rx = Rs[_RR][r_j] + R4RELAY  
				r_par = (float(r_par) * Rx ) /(float(r_par) + Rx)

			self.RR_par.append( [r_par,par_series,j] )
		self.RR_par.sort(key=lambda x:x[_GAIN])

	
	def show_gains(self):
		self.show_gains_par()

	def show_gains_par(self):
		index = 0
		last_gain = self.gains[0]
		for gain in self.gains:
			index +=1
			i = gain[_A1i]
			if gain[_GAIN]/last_gain[_GAIN] > 1.2:
				print '%03d:%03.3f %03.4f\t'%(
					index,
					gain[_GAIN],
					gain[_GAIN]/last_gain[_GAIN])
				print 'RA1=', i 
			last_gain = gain

	def show_gains__(self):
		index = 0
		last_gain = self.gains[0]
		for gain in self.gains:
			index +=1
			i = gain[_A1i]
			j = gain[_A2i]
			if gain[_GAIN]/last_gain[_GAIN] > 1.2:
				print '%03d:%03.3f %03.4f\t%s\t%s'%(
					index,
					gain[_GAIN],
					gain[_GAIN]/last_gain[_GAIN],
					'RA1=%03.3f@%d'%( Rs[_RA1][i] ,i) ,
					'RA2=%03.3f@%d'%( Rs[_RA2][j] ,j) )
			last_gain = gain



	def find_solution(self,range_,unit):

		if unit=='Ohm':	
			self.unit = 'Ohm'
			return self.find_solution4R(range_)
		if unit=='Volt':	
			self.unit = 'Volt'
			return self.find_solution4U(range_)
		if unit=='Amp':	
			self.unit = 'Amp'
			return self.find_solution4I(range_)
		pass

	def find_solution4R(self,range_):
		Min = range_[_MIN]*0.99
		Min_M = range_[_MIN]
		Max_L = range_[_MAX]*0.99
		Max = range_[_MAX]*1.01
		RH = float(self.Rs[_RH][0])
		RL = float(self.Rs[_RL][0])
		Vref = self.Vrefs[_VR]*RL/(RH + RL)
		Vresolv = self.Vrefs[_VADC]/pow(2,ADC_BITS)
		solutions=[]
		for ir in range(0,len(self.RR_par)):
			RRi= self.RR_par[ir][_R]
			gain4_min = (RRi+Min)/RRi
			gain4_min_M = (RRi+Min_M)/RRi
			gain4_max_L = (RRi+Max_L)/RRi
			gain4_max = (float(RRi)+Max)/float(RRi)
			V1min = Vref*gain4_min
			V1min_M = Vref*gain4_min_M
			V1max_L = Vref*gain4_max_L
			V1max = Vref*gain4_max
			ig = len(self.gains)
			while 1:
				ig -=1
				if ig < 0:
					break
				gain  = self.gains[ig][_GAIN]
				V2min = V1min * gain
				V2min_M = V1min_M * gain
				V2max_L = V1max_L * gain
				V2max = V1max * gain
				if V2max <= self.Vrefs[_VADC]*0.97  and (V2min_M-V2min)*K_A2 >= 3*Vresolv:
					solutions.append([V2min,V2min_M,V2max_L,V2max,ir,ig])
					break
		solutions.sort(key=lambda x:x[_VMAX]-x[_VMIN])
		try:
			solution = solutions[-1]
			solution.append(solution[_VMIN_M]-solution[_VMIN])
			solution.append(solution[_VMAX]-solution[_VMAX_M])
		except:
			print "%.3f--%.3f solution not found."%(range_[_MIN],range_[_MAX])
			return
		ig = solution[_IG]
		a1_gain = self.gains[ig][_GAIN]
		a1i= self.gains[ig][_A1i]
		ra1= [] 
		for x in a1i:
			ra1.append((x,self.Rs[_RA1][x]))

		ir = solution[_IR]
		rr = self.RR_par[ir][_R]
		rr1= []
		for x in self.RR_par[ir][_SER]:
			rr1.append((x,self.Rs[_RR][x]))

		out  = "range \t\t%05.3f~%05.3ffound: delta %.5f:%.5f\n"%(range_[_MIN],range_[_MAX],solution[-2],solution[-1])
		out += "ADC input\t %05.3f-%05.3f,"%(solution[_VMIN], solution[_VMAX])
		out += " gain %0.4f\n"%(self.gains[ig][_GAIN])
		out += "RR=%.3f@%d\t"%(rr,ir)
		out += "RH=%.3f@%d\t"%(RH,0)
		out += "RL=%.3f@%d\t"%(RL,0)
		print out
		print  "RR1=",rr1
		print  "RA1=",ra1
		self.config[_RR_]  = (rr1,rr)
		self.config[_RA1_] = (ra1,a1_gain)
		self.config[_RA2_] = ([],1)
		self.config[_RANGE_] = (solution[_VMIN],solution[_VMAX])

	def find_solution4U(self,range_):
		VMax = range_[_MAX]*1.01
		RUH = float(300*2)
		RUL = float(10/2+0.01)
		RAH = float(18)
		RAL = float(2)
		K1 = RUL/(RUH+RUL)
		K2 = (RAH+RAL)/RAL
		Vresolv = self.Vrefs[_VADC]/pow(2,ADC_BITS)
		V1max = VMax * K1 * K2
		ig = len(self.gains)
		while 1:
			ig -=1
			if ig < 0:
				break
			gain  = self.gains[ig][_GAIN]
			V2max = V1max * gain
			if V2max <= self.Vrefs[_VADC]*0.97 :
				solution=[V2max,ig]
				break
		ig = solution[-1]
		a1_gain = self.gains[ig][_GAIN]
		a1i= self.gains[ig][_A1i]
		ra1= [] 
		for x in a1i:
			ra1.append((x,self.Rs[_RA1][x]))

		out  = "range \t\t%05.3f~%05.3ffound: %.5f\n"%(range_[_MIN],range_[_MAX],solution[-1])
		out += "ADC input\t %05.3f-%05.3f,"%(0,solution[-2])
		out += " gain %0.4f\n"%(self.gains[ig][_GAIN])
		print out
		print  "RA1=",ra1
		self.config[_RR_]  = None
		self.config[_RA1_] = (ra1,a1_gain)
		self.config[_RA2_] = ([],1)
		self.config[_RANGE_] = (0,solution[1])

	def find_solution4I(self,range_):
		IMax = range_[_MAX]*1.01
		VMax = 0.005*IMax
		RAH = float(18)
		RAL = float(2)
		K1 = (RAH+RAL)/RAL
		Vresolv = self.Vrefs[_VADC]/pow(2,ADC_BITS)
		V1max = VMax * K1
		ig = len(self.gains)
		while 1:
			ig -=1
			if ig < 0:
				break
			gain  = self.gains[ig][_GAIN]
			V2max = V1max * gain
			if V2max <= self.Vrefs[_VADC]*0.97 :
				solution=[V2max,ig]
				break
		ig = solution[-1]
		a1_gain = self.gains[ig][_GAIN]
		a1i= self.gains[ig][_A1i]
		ra1= [] 
		for x in a1i:
			ra1.append((x,self.Rs[_RA1][x]))

		out  = "range \t\t%05.3f~%05.3ffound: %.5f\n"%(range_[_MIN],range_[_MAX],solution[-1])
		out += "ADC input\t %05.3f-%05.3f,"%(0,solution[-2])
		out += " gain %0.4f\n"%(self.gains[ig][_GAIN])
		print out
		print  "RA1=",ra1
		self.config[_RR_]  = None
		self.config[_RA1_] = (ra1,a1_gain)
		self.config[_RA2_] = ([],1)
		self.config[_RANGE_] = (0,solution[1])

	def find_result4R(self,value_hex):
		#print self.config
		RH = float(self.Rs[_RH][0])
		RL = float(self.Rs[_RL][0])
		Vref = self.Vrefs[_VR]*RL/(RH + RL)

		Volt_A2out= self.Vrefs[_VADC]*value_hex/pow(2,ADC_BITS)
		A2_gain   = self.config[_RA2_][_R_]
		Volt_A1out  = Volt_A2out/A2_gain
		A1_gain   = self.config[_RA1_][_R_]
		Volt_Rout  = Volt_A1out/A1_gain
		RR = self.config[_RR_][_R_]
		Ri = Volt_Rout/Vref*RR - RR 
		return Ri

#	def find_result4R(self,value_hex):
#		print self.config
#		RH = float(self.Rs[_RH][0])
#		RL = float(self.Rs[_RL][0])
#		Vref = self.Vrefs[_VR]*RL/(RH + RL)
#
#		Volt_A2out= self.Vrefs[_VADC]*value_hex/pow(2,ADC_BITS)
#		A2_gain   = self.config[_RA2_][_R_]
#		Volt_A1out  = Volt_A2out/A2_gain
#		A1_gain   = self.config[_RA1_][_R_]
#		Volt_Rout  = Volt_A1out/A1_gain
#		RR = self.config[_RR_][_R_]
#		Ri = Volt_Rout/Vref*RR - RR 
#		return Ri
RA1_series = (0.200,0.511,1.2,2.4,3.3,3.3+3.9,18,47)
#RA1_series = (2,4,8,16,32,180,220,250)
RAH_series = (0,3,15,30+30,210+30)
RR_series = (10/2,22/2,22*2,300/2,300*2,3900/2,3900*2,18000)
RH_series = (18000,)
RL_series = (200,)
Rs = [None,None,None,None,None]
Rs[_RA1] = RA1_series
Rs[_AH] =  RAH_series
Rs[_RR]  = RR_series
Rs[_RH]  = RH_series
Rs[_RL]  = RL_series

Vrefs = [None,None]
Vrefs[_VR]=2.483
Vrefs[_VADC]=3.3
gPGA = Pga(Rs=Rs,Vrefs=Vrefs)


if __name__=='__main__':
	#RA1_series = (0.010,0.2,0.22+0.22,0.36+0.36,0.36+0.62,1+0.36,1+0.82,2.2+0.18)
	#RA1_series = (0.20,0.511,1.2,3.3,3.3+3.9,18,47,47*2)
	RA1_series = (0.200,0.511,1.2,2.4,3.3,3.3+3.9,18,47)
	#RA1_series = (2,4,8,16,32,180,220,250)
	RA2_series = (0,3,15,30+30,210+30)
	RR_series = (10/2,22/2,22*2,300/2,300*2,3900/2,3900*2,18000)
	RH_series = (18000,)
	RL_series = (200,)
	Rs = [None,None,None,None,None]
	Rs[_RA1] = RA1_series
	Rs[_RA2] = RA2_series
	Rs[_RR]  = RR_series
	Rs[_RH]  = RH_series
	Rs[_RL]  = RL_series
	
	Vrefs = [None,None]
	Vrefs[_VR]=2.483
	Vrefs[_VADC]=3.3
	PGA1 = Pga(Rs=Rs,Vrefs=Vrefs)
	PGA1.show_gains()
	for range_,unit in (
			((5.6,190.6),'Ohm'),
			((10,1000),'Ohm'),
			((20,2000),'Ohm'),
			((33,240),'Ohm'),
			((40,4000),'Ohm'),
			((50,5370),'Ohm'),
			((100,10070),'Ohm'),
			((150,11870),'Ohm'),
			((200,20000),'Ohm'),
			((300,30000),'Ohm'),
			((500,20000),'Ohm'),
			((1000,100000),'Ohm'),
			((2000,200000),'Ohm'),
			((0,5),'Volt'),
			((0,10),'Volt'),
			((0,15),'Volt'),
			((0,10),'Amp'),
			((4,20),'Amp'),
			((5000,500000),'Ohm'),):
		PGA1.find_solution(range_,unit)

	print PGA1.find_series(1)
	print PGA1.find_series(128)
	print PGA1.find_series(255)
		

