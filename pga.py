#config_db.py
data_db ="sqlite3_all.db"
data_table_name = "data"
eut_db ="sqlite3_eut.db"
eut_table_name = "eut"

#constans for ADC resolution , A2 channel amplifier
ADC_BITS = 12
K_A2	 = 10.1

#index for circuit component
_RR  = 0
_RA1 = 1
_RA2 = 2
_RH  = 3
_RL  = 4

#index for circuit node
_VR = 0
_VADC = 1

#index for gain
_GAIN = 0
_A1i = 1
_A2i = 2


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

	def init_gains(self):
		self.init_gains_serial()

	def init_gains_serial(self):
		if not self.Rs:
			return
		j=0
		for i in range(0,pow(2,len(Rs[_RA1])) ):
			r_ = float(0)
			series = self.find_series(i)
			for r_j in series:
				r_ +=  Rs[_RA1][r_j]

			k2 = float(r_)+1
			self.gains.append( [k2,series,j] )
		self.gains.sort(key=lambda x:x[_GAIN])

	def init_gains_par(self):
		if not self.Rs:
			return
		j=0
		for i in range(0,pow(2,len(Rs[_RA1])) ):
			r_par = pow(2,32)
			par_series = self.find_series(i)
			for r_j in par_series:
				r_par = (float(r_par) * Rs[_RA1][r_j]) /(float(r_par) + Rs[_RA1][r_j])

			k2 = float(r_par)+1
			self.gains.append( [k2,par_series,j] )
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


	
	def init_gains__(self):
		if not self.Rs:
			return
		i = 0 
		j = 0
		for i in range(0,len(Rs[_RA1])):
			k1= float(Rs[_RA1][i])+1 
			for j in range(0,len(Rs[_RA2])):
				k2 = float(Rs[_RA2][j])+1
				self.gains.append( [k1*k2,i,j] )
		self.gains.sort(key=lambda x:x[_GAIN])
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
		pass

	def find_solution4R(self,range_):
		Min = range_[_MIN]*0.99
		Min_M = range_[_MIN]
		Max_L = range_[_MAX]*0.99
		Max = range_[_MAX]*1.01
		V = []
		RH = float(self.Rs[_RH][0])
		RL = float(self.Rs[_RL][0])
		Vref = self.Vrefs[_VR]*RL/(RH + RL)
		Vresolv = self.Vrefs[_VADC]/pow(2,ADC_BITS)
		solutions=[]
		for ir in range(0,len(self.Rs[_RR])):
			gain4_min = (float(Rs[_RR][ir])+Min)/float(Rs[_RR][ir])
			gain4_min_M = (float(Rs[_RR][ir])+Min_M)/float(Rs[_RR][ir])
			gain4_max_L = (float(Rs[_RR][ir])+Max_L)/float(Rs[_RR][ir])
			gain4_max = (float(Rs[_RR][ir])+Max)/float(Rs[_RR][ir])
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
				if V2max < self.Vrefs[_VADC]  and (V2min_M-V2min)*K_A2 > 3*Vresolv:
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
		ir = solution[_IR]
		ig = solution[_IG]
		a1i= self.gains[ig][_A1i]
		#a2i = self.gains[ig][_A2i]
		rr = self.Rs[_RR][ir]
		ra1= [] 
		for x in a1i:
			ra1.append((x,self.Rs[_RA1][x]))
		#ra2 = self.Rs[_RA2][a2i]
		out  = "range \t\t%05.3f~%05.3ffound: delta %.5f:%.5f\n"%(range_[_MIN],range_[_MAX],solution[-2],solution[-1])
		out += "ADC input\t %05.3f-%05.3f,"%(solution[_VMIN], solution[_VMAX])
		out += " gain %0.4f\n"%(self.gains[ig][_GAIN])
		out += "RR=%.3f@%d\t"%(rr,ir)
		out += "RH=%.3f@%d\t"%(RH,0)
		out += "RL=%.3f@%d\t"%(RL,0)
		print out
		print  "RA1=",ra1
		self.config[_RR_]  = (ir,rr)
		self.config[_RA1_] = (a1i,ra1)
		#self.config[_RA2_] = (a2i,ra2)
		self.config[_RANGE_] = (solution[_VMIN],solution[_VMAX])


	def find_result4R(self,value_hex):
		print self.config
		RH = float(self.Rs[_RH][0])
		RL = float(self.Rs[_RL][0])
		Vref = self.Vrefs[_VR]*RL/(RH + RL)

		Volt_A2out= self.Vrefs[_VADC]*value_hex/pow(2,ADC_BITS)
		RA2   = self.config[_RA2_][_R_]
		Volt_A1out  = Volt_A2out/(RA2+1)
		RA1   = self.config[_RA1_][_R_]
		Volt_Rout  = Volt_A1out/(RA1+1)
		RR = self.config[_RR_][_R_]
		Ri = Volt_Rout/Vref*RR - RR 
		return Ri



if __name__=='__main__':
	#RA1_series = (0.010,0.2,0.22+0.22,0.36+0.36,0.36+0.62,1+0.36,1+0.82,2.2+0.18)
	RA1_series = (0.20,0.53,1.2,3.3,7.6,18,47,120)
	#RA1_series = (2,4,8,16,32,180,220,250)
	RA2_series = (0,3,15,30+30,210+30)
	RR_series = (20,56,200,560,2000,5600,20000,56000)
	RH_series = (20000,)
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
			((33,240),'Ohm'),
			((5.6,190.6),'Ohm'),
			((200,20000),'Ohm'),
			((5000,500000),'Ohm'),
			((40,4000),'Ohm'),
			((200,20000),'Ohm'),
			((20,2000),'Ohm'),
			((150,131870),'Ohm')):
		PGA1.find_solution(range_,unit)
	for range_,unit in (
			((33,240),'Ohm'),
			((5.6,190.6),'Ohm')):
		PGA1.find_solution(range_,unit)
#		print PGA1.find_result4R(2000)
	last_gain = 255
	for x in range(1,255):
		gain_ =  255.0/float(x)
		print x, gain_,(last_gain-gain_)/last_gain
		last_gain = gain_

		

