# -*- coding: utf-8 -*-
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
		float(99999999999),#R11
		float(99999999999),#R12
		#float(99999999999),#R13
		float(100000),#R13
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

Rs = [None,None,None,None,None,None,None,None,None,None,None,None,None]
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
